"""
Central utility for sending authenticated HTTP requests to the API under test (Orchestration).

------------------------------------------------------------------------
🎯 PURPOSE
------------------------------------------------------------------------
Acts as the transport + orchestration layer for API communication.

It is responsible for:
    - Executing HTTP requests via HttpClient
    - Applying retry logic with exponential backoff
    - Logging structured request/response data
    - Converting raw responses into HttpResponse objects

------------------------------------------------------------------------
✅ FEATURES
------------------------------------------------------------------------
- Authenticates using OAuth1 (WooCommerce keys)
- Uses requests.Session() for connection reuse (performance)
- Automatic retries with exponential backoff & jitter
- Structured logging (method, endpoint, status, duration, payload)
- Payload masking for sensitive fields
- Safe and consistent response handling via HttpResponse

------------------------------------------------------------------------
📦 RESPONSE MODEL (IMPORTANT)
------------------------------------------------------------------------
All high-level methods return:

    HttpResponse

This provides:
    - status_code
    - json (safe parsed body)
    - text (raw body)
    - headers
    - elapsed time

👉 NEVER returns raw `requests.Response` in normal flows

------------------------------------------------------------------------
🔬 LOW-LEVEL ACCESS
------------------------------------------------------------------------
For advanced debugging or edge cases:

    request_raw()

returns:
    tuple(requests.Response, elapsed)

------------------------------------------------------------------------
🧪 USAGE
------------------------------------------------------------------------
- Used by API classes (CustomersApi, etc.)
- Used by helpers for positive test flows
- Used directly in negative tests (without helper abstractions)

Example:
    response = APIClient.post("customers", payload)
    assert response.status_code == 201
    assert response.json["id"] is not None

------------------------------------------------------------------------
⚠️ DESIGN PRINCIPLES
------------------------------------------------------------------------
- Transport layer only (no business validation)
- No validators
- No schema validation
- Stateless and reusable
- Single response format (HttpResponse)

------------------------------------------------------------------------
"""

import os  # Read environment variables (e.g. ENV).
import time  # Measure request durations, use sleep for backoff.
import json
import logging
import typing
from random import uniform  # Adds random jitter to exponential backoff.
import requests
from urllib.parse import urlparse

from EcommerceAPI.src.core.http_client import HttpClient
from EcommerceAPI.src.core.http_response import HttpResponse
from EcommerceAPI.src.auth.auth_resolver import resolve_auth

# Use central logging/redaction configuration and helpers to avoid duplication
from EcommerceAPI.src.utils.custom_logger import (
    DEFAULT_SENSITIVE_KEYS,
    is_include_payloads,
    redact_obj,
)
from EcommerceAPI.src.core.request_context import RequestContext

# Setup logger. Creates a logger specific to the current file/module.
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# ------------------------------------------------------------------
# - LOG_PAYLOADS: when true, include request payloads in logs (default: false)
#   This prefers the central runtime toggle from custom_logger but falls back to the legacy env var for compatibility.
# - SENSITIVE_KEYS: canonical sensitive keys set (lowercased) used for fast, shallow masking.
# ------------------------------------------------------------------
LOG_PAYLOADS = is_include_payloads() or os.getenv("LOG_PAYLOADS", "").lower() in (
    "1",
    "true",
    "yes",
    "on",
)
SENSITIVE_KEYS = {k.lower() for k in DEFAULT_SENSITIVE_KEYS}


def _mask_sensitive(payload: typing.Any) -> typing.Any:
    """
    Safely mask top-level sensitive keys in a payload.

    Purpose and rationale (short):
    - This is a lightweight, fast, *shallow* mask used by APIClient before
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
                    logger.debug(
                        "Non-stringable dict key %r when masking payload; leaving key unchanged",
                        key,
                    )

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
            exc.__class__.__name__,
        )
        try:
            redacted = redact_obj(payload)
            return redacted
        except (TypeError, ValueError, AttributeError) as exc2:
            logger.warning(
                "Final fallback failed during payload masking: %s",
                exc2.__class__.__name__,
            )
            return "<unserializable-payload>"


# -----------------------------------------
# 🔹 Robust, Extensible API Request Utility
# -----------------------------------------
class APIClient:
    """
    Enterprise API client responsible for:

    - building full API URLs
    - orchestrating HTTP requests
    - handling retries/backoff
    - delegating authentication to AuthStrategy

    Note:
    For business-level interactions, use API layer (e.g., CustomersApi).
    ------------------------------------------------------------------------
    """

    def __init__(
        self, base_url: str, retries: int = 3, backoff: float = 2.0, auth_strategy=None
    ):
        """
        Initialize API client.

        Args:
            base_url: Base API endpoint
            retries: Number of retry attempts
            backoff: Exponential backoff factor
            auth_strategy: None

        """
        self.base_url = base_url
        self.env = os.getenv("ENV", "test").lower()

        # Allow dependency injection for testing
        self.http_client = HttpClient()

        # Retry/backoff configuration
        self.max_attempts = retries
        self.backoff_factor = backoff

        # ---------------------------------------------------------
        # Authentication strategy resolution
        # Priority:
        # 1) Explicit injection (used by security tests)
        # 2) Framework configuration (AUTH_TYPE)
        # ---------------------------------------------------------
        if auth_strategy:
            self.auth_strategy = auth_strategy
        else:
            self.auth_strategy = resolve_auth()

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
    def _request_with_backoff(self, ctx: RequestContext):
        """
        Execute an HTTP request with automatic retry and exponential backoff.

        This method provides resilience for transient failures that commonly occur
        in distributed systems and during CI test execution.

        Retry conditions:
            - HTTP status codes: 429, 500, 502, 503, 504
            - Network/connection exceptions raised by requests

        Behavior:
            - Retries up to `self.max_attempts`
            - Uses exponential backoff with jitter to reduce "thundering herd"
            - Logs retry attempts with structured logging
            - Returns the raw `requests.Response` object

        Returns:
            requests.Response: Raw response returned by the HTTP client.

        Raises:
            requests.RequestException: If all retry attempts fail due to network errors.
            RuntimeError: If retries are exhausted unexpectedly.
        """
        url = ctx.url
        headers = ctx.headers
        params = ctx.params
        json_payload = ctx.json
        method = ctx.method

        last_exception: requests.RequestException | None = None

        for attempt in range(1, self.max_attempts + 1):
            try:
                request_kwargs = {
                    "method": method,
                    "url": url,
                    "headers": headers,
                    "params": params,
                    "json": json_payload,
                }

                request_kwargs = self.auth_strategy.apply(request_kwargs)

                response = self.http_client.request(**request_kwargs)
                if response is None:
                    raise RuntimeError("HttpClient.request() returned no response")

                if (
                    response.status_code in {429, 500, 502, 503, 504}
                    and attempt < self.max_attempts
                ):
                    sleep_time = self.backoff_factor**attempt + uniform(0, 1)
                    logger.warning(
                        f"Retry {attempt} on {url} after {sleep_time:.2f}s "
                        f"(status {response.status_code})",
                        extra={
                            "event": "request.retry",
                            "method": method.upper(),
                            "endpoint": url,
                        },
                    )
                    time.sleep(sleep_time)
                    continue

                return response

            except requests.RequestException as exc:
                last_exception = exc

                if attempt < self.max_attempts:
                    sleep_time = self.backoff_factor**attempt + uniform(0, 1)
                    logger.warning(
                        f"Retry {attempt} due to exception: {exc}. Sleeping {sleep_time:.3f}s",
                        extra={
                            "event": "request.exception",
                            "method": method.upper(),
                            "endpoint": url,
                        },
                    )
                    time.sleep(sleep_time)
                    continue

                raise

        if last_exception is not None:
            raise last_exception
        raise RuntimeError("Connection Error! Exhausted retries for request")

    # -------------------------------------------------------------------------
    # 🧪 Low-level utility for raw REST API calls (mainly for negative tests or debugging).
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
                ⚠️ ADVANCED USE ONLY!

                Perform an HTTP request and return the raw requests.Response and elapsed time.

                In other words: "Give me raw response, but still use framework infrastructure"

                ------------------------------------------------------------------------
                🎯 PURPOSE
                ------------------------------------------------------------------------
                Provides direct, low-level access to the underlying HTTP response.

                This method bypasses:
                    - HttpResponse wrapping
                    - Logging abstraction
                    - Any higher-level processing

                ------------------------------------------------------------------------
                🧪 WHEN TO USE
                ------------------------------------------------------------------------
                Use ONLY when you need full control over the raw response:

                    - Inspect request/response at transport level
                    - Access attributes not exposed by HttpResponse
                    - Debug edge cases or unexpected API behavior
                    - Advanced negative testing scenarios
                    - Investigating headers / encoding
                    - Inspecting .request object

                    Or Something is unclear or broken like ("When HttpResponse is not enough to understand what’s
                    happening"):
                    - API returns weird error
                    - JSON parsing fails
                    - headers look wrong
                    - encoding issues
                    - redirects / auth issues
        -
                ------------------------------------------------------------------------
                ⚠️ IMPORTANT
                ------------------------------------------------------------------------
                - Returns raw `requests.Response` (NOT HttpResponse)
                - JSON parsing is NOT safe (response.json() may raise)
                - No abstraction — use carefully

                ------------------------------------------------------------------------
                RETURNS
                ------------------------------------------------------------------------
                tuple:
                    (requests.Response, elapsed_time_seconds)

                ------------------------------------------------------------------------
                EXAMPLE
                ------------------------------------------------------------------------
                resp, elapsed = APIClient.request_raw(
                    method="post",
                    endpoint="customers",
                    payload={"email": ""}
                )

                assert resp.status_code == 400

                # Manual parsing (may raise if not JSON)
                body = resp.json()

                ------------------------------------------------------------------------
                The difference between request_raw() and HttpClient.request()
                Both ultimately hit requests and return requests.Response
                ------------------------------------------------------------------------
                |              | `request_raw()`               | `HttpClient.request()`  |
                | ------------ | ----------------------------  | ----------------------  |
                | Layer        | RequestUtility (mid-level)    | HttpClient (low-level)  |
                | URL handling | ✅ builds endpoint → full URL | ❌ expects full URL     |
                | Auth         | ✅ already configured         | ✅ handled internally   |
                | Retries      | ✅ YES (via backoff)          | ❌ NO                   |
                | Logging      | ❌ minimal / none             | ❌ none                 |
                | Intended use | testing/debugging             | transport only          |

                ------------------------------------------------------------------------
                ⚠️ ADVANCED USE ONLY
                ------------------------------------------------------------------------
                This method is NOT used in normal tests.

                Prefer using standard methods (get/post/etc.) which return HttpResponse.

                Use request_raw() only when truly necessary.
        """

        url = self._build_url(endpoint)
        request_headers = headers or {"Content-Type": "application/json"}

        start = time.perf_counter()

        ctx = RequestContext(
            method=method, url=url, headers=request_headers, params=params, json=payload
        )

        resp = self._request_with_backoff(ctx)

        elapsed = time.perf_counter() - start
        return resp, elapsed

    # -----------------------------------------
    # 📋 Internal: Handle & log the response, validate, optionally return raw
    # -----------------------------------------
    @staticmethod
    def _format_error_body(response_json):
        """
        Safely format response body for logging.

        - Pretty prints JSON (dict/list)
        - Falls back to string for non-JSON responses
        - Never raises (safe for logging)

        Used for:
            - Debug logs (4xx / 5xx responses)
            - Human-readable error output
        """
        try:
            if isinstance(response_json, (dict, list)):
                return json.dumps(response_json, indent=2, ensure_ascii=False)
            return str(response_json)
        except (TypeError, ValueError) as e:
            logger.debug(f"Failed to serialize response body: {e}")
            return "<unserializable-response-body>"

    def _handle_response(
        self,
        response: requests.Response,
        duration: float = None,
        method: str = None,
        log_payload: dict = None,
    ) -> HttpResponse:
        """
        Handle HTTP response lifecycle: normalize → log → return.

        ------------------------------------------------------------------------
        🎯 PURPOSE
        ------------------------------------------------------------------------
        This method acts as the bridge between raw HTTP (requests.Response)
        and the framework-level response (HttpResponse).

        It:
            1. Converts raw response → HttpResponse (single source of truth)
            2. Logs request/response metadata
            3. Logs error body for debugging (4xx/5xx)
            4. Returns a consistent HttpResponse object

        ------------------------------------------------------------------------
        ⚠️ IMPORTANT DESIGN DECISION
        ------------------------------------------------------------------------
        - JSON parsing happens ONLY inside HttpResponse
        - This method NEVER calls response.json() directly
        - Ensures consistent, safe parsing across the framework

        Args:
            response (requests.Response): The HTTP response from requests.
            duration (float, optional): Time taken for the request (for logging).
            method (str, optional): HTTP method (for log formatting).
            log_payload (dict, optional): The request body for logging.

        ------------------------------------------------------------------------
        RETURNS
        ------------------------------------------------------------------------
        HttpResponse (always)

        """
        # --------------------------------------------------------------------
        # 1. Convert RAW → HttpResponse (SINGLE SOURCE OF TRUTH)
        # --------------------------------------------------------------------
        http_response = HttpResponse.from_http_requests(response, duration)

        # Store actual and expected status codes for later reference (for potential test assertion context)
        status_code = http_response.status_code

        # --------------------------------------------------------------------
        # 2. Prepare response body for logging
        # --------------------------------------------------------------------
        # Use parsed JSON if available, otherwise fallback to raw text
        response_body = (
            http_response.json if http_response.json is not None else http_response.text
        )

        # --------------------------------------------------------------------
        # 3. Extract endpoint (cleaner logs + avoid long shared URLs)
        # --------------------------------------------------------------------
        parsed = urlparse(response.request.url)
        endpoint_name = parsed.path

        if parsed.query:
            endpoint_name += f"?{parsed.query}"
        # --------------------------------------------------------------------
        # 4. Prepare masked payload (if enabled)
        # --------------------------------------------------------------------
        masked_payload = None
        if LOG_PAYLOADS and log_payload is not None:
            masked_payload = _mask_sensitive(log_payload)

        # --------------------------------------------------------------------
        # 5. Structured logging metadata
        # --------------------------------------------------------------------
        extra_meta = {
            "method": method.upper() if method else None,
            "endpoint": endpoint_name,
            "status": status_code,
            "duration": duration,
            "payload": masked_payload,
            "event": "request.response",
        }

        # --------------------------------------------------------------------
        # 6. Success log (always)
        # --------------------------------------------------------------------
        # Unified human-readable log lines (these remain for console/human files)
        logger.info(
            f"✅ {method.upper()} {endpoint_name} → Status code: {status_code} "
            f"(completed in {duration:.3f}s)",
            extra=extra_meta,
        )

        # --------------------------------------------------------------------
        # 7. Error logging (4xx / 5xx)
        # --------------------------------------------------------------------
        # Always log error body for 4xx/5xx responses (transport-level observability)
        if status_code >= 400:
            body_str = self._format_error_body(response_body)

            logger.debug(body_str, extra={**extra_meta, "event": "request.error_body"})

        # --------------------------------------------------------------------
        # 8. Return normalized response
        # --------------------------------------------------------------------
        # NOTE:
        # We ALWAYS return HttpResponse (even for "raw" mode)
        # This ensures a consistent interface across the framework
        return http_response

    # -----------------------------------------
    # ⚙️ Internal: Shared request logic for all verbs
    # -----------------------------------------
    def _request(
        self,
        method: str,
        endpoint: str,
        params: dict = None,
        payload: dict = None,
        headers: dict = None,
    ) -> HttpResponse:
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
              params (dict, optional): Query parameters for GET/DELETE.
              payload (dict, optional): JSON body for POST/PUT.
              headers (dict, optional): HTTP headers.

          Returns:
              HttpResponse
        """
        url = self._build_url(endpoint)
        request_headers = headers or {"Content-Type": "application/json"}

        start = time.perf_counter()

        ctx = RequestContext(
            method=method, url=url, headers=request_headers, params=params, json=payload
        )

        response = self._request_with_backoff(ctx)

        duration = time.perf_counter() - start

        return self._handle_response(
            response=response,
            duration=duration,
            method=method,
            log_payload=payload,
        )

    # -----------------------------------------
    # 🔓 Public API Methods: get, post, put, delete
    # -----------------------------------------
    # ✅ params → for GET, DELETE query strings
    # ✅ json → for POST, PUT body data

    """
    Perform a POST, GET, PUT or DELETE request and return a normalized HttpResponse.

    ------------------------------------------------------------------------
    🎯 PURPOSE
    ------------------------------------------------------------------------
    These are low-level HTTP methods used to interact with API endpoints.

    It is part of the transport/orchestration layer and is used by:
        - API classes (e.g., CustomersApi)
        - Negative tests (via fixtures)
        - Debugging scenarios

    ------------------------------------------------------------------------
    📦 RETURNS
    ------------------------------------------------------------------------
    HttpResponse:
        - status_code
        - json (parsed safely)
        - text
        - headers
        - elapsed time

    ------------------------------------------------------------------------
    ⚠️ IMPORTANT
    ------------------------------------------------------------------------
    - This method does NOT perform:
        - business validation
        - schema validation
        - validators

    - For positive test flows, prefer using API layer methods:
        CustomersApi.get_customer(...)

    ------------------------------------------------------------------------
    🧪 USAGE
    ------------------------------------------------------------------------
    Typical usage in negative tests:

        response = raw_customer_api.get("customers")
        assert response.status_code == 400

    ------------------------------------------------------------------------
    """

    def get(
        self,
        endpoint: str,
        params: dict = None,
        headers: dict = None,
    ) -> HttpResponse:
        """
        Performs a GET request.
        Args:
            endpoint (str): API path.
            params (dict, optional): Query parameters.
            headers (dict, optional): HTTP headers.
        Returns:
            HttpResponse
        """
        return self._request(
            "get",
            endpoint,
            params=params,
            headers=headers,
        )

    def post(
        self,
        endpoint: str,
        payload: dict = None,
        headers: dict = None,
    ) -> HttpResponse:
        """
        Performs a POST request.
        Args:
            endpoint (str): API path.
            payload (dict, optional): JSON body.
            headers (dict, optional): HTTP headers.
        Returns:
            HttpResponse
        """
        return self._request(
            "post",
            endpoint,
            payload=payload,
            headers=headers,
        )

    def put(
        self,
        endpoint: str,
        payload: dict = None,
        headers: dict = None,
    ) -> HttpResponse:
        """
        Performs a PUT request.
        Args:
            endpoint (str): API path.
            payload (dict, optional): JSON body.
            headers (dict, optional): HTTP headers.
        Returns:
            HttpResponse
        """
        return self._request(
            "put",
            endpoint,
            payload=payload,
            headers=headers,
        )

    def delete(
        self,
        endpoint: str,
        params: dict = None,
        headers: dict = None,
    ) -> HttpResponse:
        """
        Performs a DELETE request.
        Args:
            endpoint (str): API path.
            params (dict, optional): Query parameters.
            headers (dict, optional): HTTP headers.
        Returns:
            HttpResponse

        """
        return self._request(
            "delete",
            endpoint,
            params=params,
            headers=headers,
        )
