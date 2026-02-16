import os  # Read environment variables (e.g. ENV).
import time  # Measure request durations, use sleep for backoff.
import json
import logging
import typing
from random import uniform  # Adds random jitter to exponential backoff.
import requests
from requests_oauthlib import OAuth1
from jsonschema import validate, ValidationError

from EcommerceAPI.src.utilities.credentialsUtility import get_wc_api_keys
# Import exception classes from centralized exceptions module and re-export them
from EcommerceAPI.src.utilities.exceptions import SchemaValidationError, UnexpectedStatusCodeError

# Use central logging/redaction configuration and helpers to avoid duplication
from EcommerceAPI.src.utilities.custom_logger import (
    DEFAULT_SENSITIVE_KEYS,
    is_include_payloads,
    redact_obj,
)

# Setup logger. Creates a logger specific to the current file/module.
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# ------------------------------------------------------------------
# - LOG_PAYLOADS: when true, include request payloads in logs (default: false)
#   This prefers the central runtime toggle from custom_logger but falls back to the legacy env var for compatibility.
# - SENSITIVE_KEYS: canonical sensitive keys set (lowercased) used for fast, shallow masking.
# ------------------------------------------------------------------
LOG_PAYLOADS = is_include_payloads() or os.getenv("LOG_PAYLOADS", "").lower() in ("1", "true", "yes", "on")
SENSITIVE_KEYS = {k.lower() for k in DEFAULT_SENSITIVE_KEYS}


def _mask_sensitive(payload: typing.Any) -> typing.Any:
    """
    Safely mask top-level sensitive keys in a payload.

    Purpose and rationale (short):
    - This is a lightweight, fast, *shallow* mask used by RequestUtility before
      placing payloads into log extras. It runs quickly and avoids deep recursion.
    - We still rely on the central redaction (`redact_obj`) at formatting time for
      full recursive redaction; this function is defense-in-depth to reduce early leakage.
    - The function is defensive: it never raises and always returns a usable value
      for logging.

    Behavior:
    - If payload is None -> return None.
    - If payload is a dict -> produce a shallow copy where top-level keys that match
      SENSITIVE_KEYS are replaced with '***'. Other keys are left as-is.
    - If payload is not a dict -> return it unchanged (to avoid expensive processing).
    - On unexpected errors -> attempt a safe fallback using the central `redact_obj`
      (which performs recursive redaction). If that also fails, return a sentinel string.

    Notes:
    - This intentionally masks only top-level keys for performance. Use `redact_obj`
      for deeper, recursive redaction when required.
    """
    if payload is None:
        return None

    # Fast-path: shallow mask for dicts (cheap & predictable)
    try:
        if isinstance(payload, dict):
            masked = {}
            for key, val in payload.items():
                # Narrowly guard stringification of keys (avoid broad except)
                key_name = None
                try:
                    key_name = str(key).lower()
                except (TypeError, ValueError):
                    # Key cannot be stringified in a normal way; leave it as-is and continue.
                    logger.debug("Non-stringable dict key %r when masking payload; leaving key unchanged", key)

                if key_name and key_name in SENSITIVE_KEYS:
                    masked[key] = "***"
                else:
                    masked[key] = val
            return masked

        # Non-dict payloads are returned unchanged to avoid unnecessary cost.
        return payload

    except (TypeError, ValueError, AttributeError) as exc:
        # Defensive fallback: try central redact (slower but recursive) on narrow exceptions only.
        logger.debug(
            "Payload shallow masking encountered %s; falling back to recursive redaction.",
            exc.__class__.__name__
        )
        try:
            redacted = redact_obj(payload)
            return redacted
        except (TypeError, ValueError, AttributeError) as exc2:
            logger.warning(
                "Final fallback failed during payload masking: %s", exc2.__class__.__name__
            )
            return "<unserializable-payload>"


# -----------------------------------------
# 🔹 Robust, Extensible API Request Utility
# -----------------------------------------
class RequestUtility:
    """
    Central utility for sending authenticated HTTP requests to the API under test.
    Features:
      - Authenticates using OAuth1 (WooCommerce keys).
      - Uses requests.Session() for connection reuse.
      - Automatic retries with exponential backoff & jitter for robustness.
      - Detailed, structured logging for diagnostics & debugging.
      - Validates response status code and (optionally) JSON schema.
      - Supports returning either parsed JSON/text or the raw Response object.
      - Logging calls emit structured metadata via the `extra` parameter (method, endpoint, status, duration, payload).
        This enables the JSONFormatter in custom_logger to produce structured events for ingestion.
      - Payload logging is opt-in via LOG_PAYLOADS environment variable to avoid leaking sensitive data and to reduce
        log volume in CI.
      - Sensitive fields in payloads are masked before being included in logs.

    Usage:
      - Used by API helpers for positive test flows.
      - Used directly (with return_raw=True) for negative/diagnostic testing.
    """

    def __init__(self, base_url: str, retries: int = 3, backoff: float = 2.0):
        """
        Initializes the RequestUtility.

        Args:
            base_url (str): Fully-qualified global URL for the API
                (e.g. http://localhost:8888/wp-json/wc/v3).
            retries (int): Number of retry attempts for transient errors.
            backoff (float): Exponential backoff factor between retries.
        """
        # Load WooCommerce OAuth credentials
        wc_creds = get_wc_api_keys()
        self.auth = OAuth1(wc_creds['wc_key'], wc_creds['wc_secret'])

        # Base url
        self.base_url = base_url

        # Environment name (test/dev/staging/prod)
        self.env = os.getenv("ENV", "test").lower()
        self.session = requests.Session()  # Reuse TCP connections for speed. Using requests.Session() improves
        # performance by reusing TCP connections. This is helpful if you're hitting the API repeatedly during tests.
        # It allows us to access to speed up our code when sending requests to the same server. This is perfect for
        # scraping data or accessing APIs

        # Retry/backoff configuration
        self.max_attempts = retries
        self.backoff_factor = backoff

        # State tracking for debugging & logging
        self.status_code = None
        self.expected_status_code = None
        self.url = None
        self.payload = None
        self.headers = None
        self.rs_json = None

    # -----------------------------------------
    # URL construction
    # -----------------------------------------
    def _build_url(self, endpoint: str) -> str:
        """
        Safely build a full request URL from base_url + endpoint.

        Ensures:
        - Exactly one '/' between base_url and endpoint
        - Endpoint is not empty
        """
        if not endpoint:
            raise ValueError("API endpoint is required (e.g. 'customers')")
        return f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"

    # -----------------------------------------
    # 🌐 Internal: Send a request with retries/backoff
    # -----------------------------------------
    def _request_with_backoff(self, method: str, **kwargs) -> requests.Response:
        """
            It sends an HTTP request with automatic retries/backoff for retryable errors.
            Retries on status codes 429/500/502/503/504 and network exceptions.
            It:
            - Tries by default up to 3 times on known retryable status codes (429, 500, etc.)
            - Adds a small random delay using uniform(0, 1) to reduce "thundering herd" issues
            - Logs warnings on each retry
            - Returns the raw response object from requests
            - This helps with flaky APIs, especially during CI or high-load testing.

        Returns:
                requests.Response: Raw response object.
        Raises:
                requests.RequestException: If all attempts fail.

            """
        for attempt in range(1, self.max_attempts + 1):
            try:
                response = self.session.request(method=method, auth=self.auth, **kwargs)  # It returns raw
                # requests.Response
                # This response is a full requests.Response object from the requests library, which includes:
                #     .status_code → e.g., 200, 400
                #     .text → raw response body as a string
                #     .json() → parsed JSON body (if possible)
                #     .headers → response headers
                #     .content → raw bytes
                #     .request → the request object that was sent
                #     .url → full URL that was hit

                # # To see the entire raw response log the following:

                # logger.debug(f"""🌐 Raw Response:
                # Status: {response.status_code}
                # URL: {response.url}
                # Headers: {response.headers}
                # Body:{response.text}
                # """)

                # Retry on transient server/client errors
                if response.status_code in {429, 500, 502, 503, 504} and attempt < self.max_attempts:
                    sleep_time = self.backoff_factor ** attempt + uniform(0, 1)
                    logger.warning(
                        f"🔁 Retry {attempt} on {kwargs.get('url')} after {sleep_time:.2f}s "
                        f"(status {response.status_code})",
                        extra={"event": "request.retry", "method": method.upper(), "endpoint": kwargs.get("url")}
                    )
                    time.sleep(sleep_time)
                    continue
                return response

            except requests.RequestException as e:
                if attempt == self.max_attempts:
                    raise
                sleep_time = self.backoff_factor ** attempt + uniform(0, 1)
                logger.warning(f"❗ Retry {attempt} due to exception: {e}. Sleeping {sleep_time:.3f}s",
                               extra={"event": "request.exception", "method": method.upper(),
                                      "endpoint": kwargs.get("url")})
                time.sleep(sleep_time)
            raise RuntimeError("Connection Error! Exhausted retries for request")

    # -------------------------------------------------------------------------
    # 🧪 Low-level utility for raw REST API calls (mainly for negative tests).
    # -------------------------------------------------------------------------

    def request_raw(
            self,
            method: str,
            endpoint: str,
            *,
            params: dict = None,
            payload: dict = None,
            headers: dict = None,
    ) -> tuple[requests.Response, float]:
        """
        Perform an HTTP request and return the raw requests.Response and elapsed time.

        This bypasses _handle_response's status/assert logic and is intended for:
            - Negative tests that expect non-2xx responses and want to inspect raw response.
            - Debugging/inspection where you need headers/status without RequestUtility raising.

        Purpose:
        --------
        - Used for negative testing scenarios where you want to bypass high-level helper logic, such as auto-generating
        valid payloads or positive-path response assertions.
        - Allows you to send malformed, incomplete, or intentionally invalid data to the API.
        - Supports returning the raw Response object for advanced debugging (headers, status, etc).

        Usage:
        ------
        - In your pytest fixtures, return request_raw() for negative testing.
        - Pass `return_raw=True` to any method if you want the full requests.Response object.


        Example usage in a test (negative test expecting 400):
        -------------------------------------------------------
        If you want the parsed response but the RequestUtility would raise because expected != actual, you can:
           - Call request_raw and then parse JSON: resp, elapsed = raw_customer_api.request_raw("post", "customers",
           payload=payload) assert resp.status_code == 400 body = resp.json()
           - Or call the normal .post(...) but set expected_status_code to the actual expected (e.g., 400) — that will
           return parsed JSON (this is the preferred approach for negative tests that assert a specific status).
           - Use return_raw=True with .post(...) only when the response would be a matching expected_status_code;
           otherwise _handle_response will raise before returning raw.


        Example in test:
        ----------------
            def test_missing_required_field(raw_customer_api):
                bad_payload = {"email": ""}  # Invalid, missing password
                # For normal use (parsed response):
                response = raw_customer_api.post("customers", bad_payload, expected_status_code=400)
                assert response["code"] == "rest_missing_callback_param"
                # For advanced debugging (headers, status, etc):
                raw_resp = raw_customer_api.post("customers", bad_payload, expected_status_code=400, return_raw=True)
                assert raw_resp.status_code == 400
                print(raw_resp.headers)

        """
        # self.url = f"{self.base_url}{endpoint}"
        self.url = self._build_url(endpoint)
        headers = headers or {"Content-Type": "application/json"}
        start = time.perf_counter()
        resp = self._request_with_backoff(method=method, url=self.url, headers=headers, params=params, json=payload)
        elapsed = time.perf_counter() - start
        return resp, elapsed

    # Convenience wrappers that call request_raw and return the raw response (keeps the public API simple)
    def raw_get(self, endpoint: str, params: dict = None) -> tuple[requests.Response, float]:
        return self.request_raw("get", endpoint, params=params)

    def raw_post(self, endpoint: str, payload: dict = None) -> tuple[requests.Response, float]:
        return self.request_raw("post", endpoint, payload=payload)

    def raw_put(self, endpoint: str, payload: dict = None) -> tuple[requests.Response, float]:
        return self.request_raw("put", endpoint, payload=payload)

    def raw_delete(self, endpoint: str, params: dict = None) -> tuple[requests.Response, float]:
        return self.request_raw("delete", endpoint, params=params)

    # -----------------------------------------
    # 📋 Internal: Handle & log the response, validate, optionally return raw
    # -----------------------------------------
    def _handle_response(
            self,
            response: requests.Response,
            expected_status_code: int,
            schema: dict = None,
            duration: float = None,
            method: str = None,
            log_payload: dict = None,
            log_params: dict = None,
            return_raw: bool = False
    ) -> typing.Union[dict, str, requests.Response]:  # is a type hint in Python that means: The return value (or
        # variable, parameter, etc.) can be any one of these types: a dict, a str or a requests.Response object.
        # The function may return a dictionary, or a string, or a requests.Response object (from the requests library).
        # Why is this used?
        # In the context of your RequestUtility methods:
        #     - If return_raw is True, the method returns a requests.Response.
        #     - Otherwise, it returns either a parsed JSON dict (if the response is JSON), or a plain string (if not).
        # Summary Table:
        # TYPE	              WHEN RETURNED
        # dict	              JSON response, parsed
        # str	              Non-JSON response (plain text)
        # requests.Response	  If return_raw=True

        """
        Parses, validates, logs, and (optionally) returns the response.

        It:
            - Checks status code and (optionally) schema.
            - Logs request/response context, including on failure.
            - On error, raises informative custom exception.
            - If return_raw, returns the raw response object for advanced tests.
            - Unified logging style.

        Key logging improvements:
        - Structured metadata is passed via `extra` so JSONFormatter can pick it up.
        - Payload included only when LOG_PAYLOADS is enabled; sensitive fields are masked via _mask_sensitive.

        Args:
            response (requests.Response): The HTTP response from requests.
            expected_status_code (int): The status code the caller expects.
            schema (dict, optional): JSON schema to validate the response.
            duration (float, optional): Time taken for the request (for logging).
            method (str, optional): HTTP method (for log formatting).
            log_payload (dict, optional): The request body for logging.
            log_params (dict, optional): The query params for logging.
            return_raw (bool): If True, return the raw Response object.

        Returns:
            dict, str, or requests.Response: Parsed JSON/text, or raw Response if requested.

        Raises:
            UnexpectedStatusCodeError, SchemaValidationError
        """

        # Store actual and expected status codes for later reference (for potential test assertion context)
        self.status_code = response.status_code
        self.expected_status_code = expected_status_code

        # Extract endpoint name for readability (avoid long global URLs)
        endpoint_name = response.request.url.replace(self.base_url, "")

        # Attempt to parse the response as JSON. If that fails, fallback to plain text.
        try:
            self.rs_json = response.json()
        except ValueError:
            self.rs_json = response.text  # Not JSON — could be plain HTML error page, etc.

        # Prepare masked payload if allowed
        masked_payload = None
        if LOG_PAYLOADS and log_payload is not None:
            masked_payload = _mask_sensitive(log_payload)

        # Structured extra metadata for loggers (helps JSON formatter)
        extra_meta = {
            "method": method.upper() if method else None,
            "endpoint": endpoint_name,
            "status": self.status_code,
            "duration": duration,
            "payload": masked_payload,
            "event": "request.response",
        }

        # # Unified logging style -->OLD AND REPLACED
        # logger.debug(f"📡 {method.upper()} {endpoint_name} → {self.status_code}")
        # logger.debug(f"✅ {method.upper()} {endpoint_name} → Status {self.status_code} ({duration:.3f}s)")
        # logger.info(f"📡 {method.upper()} {endpoint_name} → completed in {duration:.3f}s")

        # Unified human-readable log lines (these remain for console/human files)
        logger.debug(f"📡 {method.upper()} {endpoint_name} → {self.status_code}", extra=extra_meta)
        logger.debug(f"✅ {method.upper()} {endpoint_name} → Status {self.status_code} ({duration:.3f}s)",
                     extra=extra_meta)
        logger.info(f"📡 {method.upper()} {endpoint_name} → completed in {duration:.3f}s", extra=extra_meta)

        # 🚨 Raise error if the status code did not match expectations.
        # Log payload and query params only on mismatch)
        if self.status_code != expected_status_code:
            # 🔍 Log query parameters (GET, DELETE), if provided
            if log_params:
                try:
                    formatted_params = json.dumps(log_params, indent=2, ensure_ascii=False)
                except Exception as e:
                    formatted_params = str(log_params)
                    logger.debug(f"⚠️ Failed to serialize query params: {e}",
                                 extra={**extra_meta, "event": "request.params_serialization_error"})
                logger.debug(f"🔎 [Query Params] {method.upper()} {endpoint_name}:\n{formatted_params}",
                             extra={**extra_meta, "event": "request.params"})
            # 📦 Log payload/body (POST, PUT), if provided
            if log_payload:
                try:
                    formatted_payload = json.dumps(_mask_sensitive(log_payload), indent=2, ensure_ascii=False)
                except Exception as e:
                    formatted_payload = str(_mask_sensitive(log_payload))
                    logger.debug(f"⚠️ Failed to serialize payload: {e}",
                                 extra={**extra_meta, "event": "request.payload_serialization_error"})
                logger.debug(f"📦 [Payload] {method.upper()} {endpoint_name}:\n{formatted_payload}",
                             extra={**extra_meta, "event": "request.payload"})

        # 🧪 If a schema is provided, validate the response structure.
        if schema:
            try:
                validate(instance=self.rs_json, schema=schema)
            except ValidationError as e:
                raise SchemaValidationError(
                    f"Schema validation failed: {e.message}",
                    response=response,
                    response_json=self.rs_json
                )

        # 🐞 If response is a 4xx or 5xx, log the actual response body for inspection.
        # Log response body if error
        if self.status_code >= 400:
            try:
                if isinstance(self.rs_json, (dict, list)):
                    body_str = json.dumps(self.rs_json, indent=2, ensure_ascii=False)
                else:
                    # Prefer str(), but guard against known narrow errors
                    try:
                        body_str = str(self.rs_json)
                    except (TypeError, ValueError, AttributeError) as e:
                        logger.debug("str() failed for response body: %s", e, exc_info=True)
                        # Fallback to repr() which is more robust for many objects
                        try:
                            body_str = repr(self.rs_json)
                        except (TypeError, ValueError, AttributeError) as e2:
                            logger.debug("repr() also failed for response body: %s", e2, exc_info=True)
                            body_str = "<unserializable-response-body>"
            except (TypeError, ValueError, AttributeError) as ser_exc:
                logger.debug("Failed serializing response body to JSON: %s", ser_exc, exc_info=True)
                try:
                    body_str = repr(self.rs_json)
                except (TypeError, ValueError, AttributeError):
                    body_str = "<unserializable-response-body>"

            logger.debug(body_str, extra={**extra_meta, "event": "request.error_body"})

        # 🚨 Raise error if the status code did not match expectations
        if self.status_code != expected_status_code:
            raise UnexpectedStatusCodeError(
                message=f"Expected {expected_status_code}, got {self.status_code}",
                response=response,
                response_json=self.rs_json
            )
        # Optionally return the raw response object for advanced inspection
        if return_raw:
            return response

        # ✅ Success: return parsed JSON or raw text if non-JSON
        return self.rs_json

    # -----------------------------------------
    # ⚙️ Internal: Shared request logic for all verbs
    # -----------------------------------------
    def _request(
            self,
            method: str,
            endpoint: str,
            expected_status_code: int = 200,
            params: dict = None,
            payload: dict = None,
            headers: dict = None,
            schema: dict = None,
            return_raw: bool = False
    ) -> typing.Union[dict, str, requests.Response]:
        """
            It constructs and executes an HTTP request (any verb).

            Core HTTP request handler.
            It builds full URL, performs the request with retry/backoff, handles response parsing, validation, logging,
            and error raising.

            Internal handler for all HTTP methods. Orchestrates the request lifecycle.
            - It constructs the full URL.
            - It records the start time.
            - It calls _request_with_backoff(), which:
                - Makes the actual request (with retry/backoff logic for 500s, 429, etc.).
                - Returns the raw response object from requests.
            - Then it calls _handle_response(), passing:
                - The raw response
                - The expected_status_code
            - And finally the _handle_response():
                - Saves the actual status code and response JSON.
                - Compares actual vs. expected status code.
                - If they don't match, it raises an UnexpectedStatusCodeError, stopping execution unless caught.
                - If they do match, it returns the parsed JSON body (or text).

          Note:
             - Positive tests → using CustomersHelper + create_customer_for_test() fixture.
             - Negative tests → going low-level directly to requests_utility.post(...). E.g., for negative tests:
             test_update_customer.py (@pytest.mark.tcid21) or test_create_customer.py (@pytest.mark.tcid15)
             Negative tests are fundamentally different — they:
                 - Expect failure
                 - Require raw responses
                 - Should not auto-generate valid input
             Helpers are used for a positive path, raw API for negative path.
             Raw_customer_api used only where failure is expected

            Args:
                method (str): HTTP verb ('get', 'post', etc.)
                endpoint (str): API endpoint path (relative to base_url).
                expected_status_code (int): Status code to expect/assert.
                params (dict, optional): Query parameters for GET/DELETE.
                payload (dict, optional): JSON body for POST/PUT.
                headers (dict, optional): HTTP headers.
                schema (dict, optional): JSON schema to validate response.
                return_raw (bool): If True, return raw requests.Response.

            Returns:
                dict, str, or requests.Response.

            Raises:
                UnexpectedStatusCodeError, SchemaValidationError, requests.RequestException

            """
        # self.url = f"{self.base_url}{endpoint}"
        self.url = self._build_url(endpoint)
        self.payload = payload
        self.headers = headers or {"Content-Type": "application/json"}

        start = time.perf_counter()
        response = self._request_with_backoff(
            method=method,
            url=self.url,
            headers=self.headers,
            params=params,
            json=payload
        )
        duration = time.perf_counter() - start

        return self._handle_response(
            response=response,
            expected_status_code=expected_status_code,
            schema=schema,
            duration=duration,
            method=method,
            log_payload=payload,
            log_params=params,
            return_raw=return_raw
        )

    # -----------------------------------------
    # 🔓 Public API Methods: get, post, put, delete
    # -----------------------------------------
    # ✅ params → for GET, DELETE query strings
    # ✅ json → for POST, PUT body data

    def get(
            self,
            endpoint: str,
            params: dict = None,
            headers: dict = None,
            expected_status_code: int = 200,
            schema: dict = None,
            return_raw: bool = False
    ) -> typing.Union[dict, str, requests.Response]:
        """
        Performs a GET request.
        Args:
            endpoint (str): API path.
            params (dict, optional): Query parameters.
            headers (dict, optional): HTTP headers.
            expected_status_code (int): Status code to expect.
            schema (dict, optional): JSON schema to validate.
            return_raw (bool): If True, return requests.Response.
        Returns:
            dict, str, or requests.Response
        """
        return self._request(
            "get",
            endpoint,
            expected_status_code,
            params=params,
            headers=headers,
            schema=schema,
            return_raw=return_raw
        )

    def post(
            self,
            endpoint: str,
            payload: dict = None,
            headers: dict = None,
            expected_status_code: int = 201,
            schema: dict = None,
            return_raw: bool = False
    ) -> typing.Union[dict, str, requests.Response]:
        """
        Performs a POST request.
        Args:
            endpoint (str): API path.
            payload (dict, optional): JSON body.
            headers (dict, optional): HTTP headers.
            expected_status_code (int): Status code to expect.
            schema (dict, optional): JSON schema to validate.
            return_raw (bool): If True, return requests.Response.
        Returns:
            dict, str, or requests.Response
        """
        return self._request(
            "post",
            endpoint,
            expected_status_code,
            payload=payload,
            headers=headers,
            schema=schema,
            return_raw=return_raw
        )

    def put(
            self,
            endpoint: str,
            payload: dict = None,
            headers: dict = None,
            expected_status_code: int = 200,
            schema: dict = None,
            return_raw: bool = False
    ) -> typing.Union[dict, str, requests.Response]:
        """
        Performs a PUT request.
        Args:
            endpoint (str): API path.
            payload (dict, optional): JSON body.
            headers (dict, optional): HTTP headers.
            expected_status_code (int): Status code to expect.
            schema (dict, optional): JSON schema to validate.
            return_raw (bool): If True, return requests.Response.
        Returns:
            dict, str, or requests.Response
        """
        return self._request(
            "put",
            endpoint,
            expected_status_code,
            payload=payload,
            headers=headers,
            schema=schema,
            return_raw=return_raw
        )

    def delete(
            self,
            endpoint: str,
            params: dict = None,
            headers: dict = None,
            expected_status_code: int = 200,
            schema: dict = None,
            return_raw: bool = False
    ) -> typing.Union[dict, str, requests.Response]:
        """
        Performs a DELETE request.
        Args:
            endpoint (str): API path.
            params (dict, optional): Query parameters.
            headers (dict, optional): HTTP headers.
            expected_status_code (int): Status code to expect.
            schema (dict, optional): JSON schema to validate.
            return_raw (bool): If True, return requests.Response.
        Returns:
            dict, str, or requests.Response

        """
        return self._request(
            "delete",
            endpoint,
            expected_status_code,
            params=params,
            headers=headers,
            schema=schema,
            return_raw=return_raw
        )
