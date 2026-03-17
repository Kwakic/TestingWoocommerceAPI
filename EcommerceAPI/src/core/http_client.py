import requests
from typing import Any, Dict, Optional


class HttpClient:
    """
    LOW-LEVEL HTTP CLIENT (Transport Layer)

    This class is responsible ONLY for sending HTTP requests and returning
    the raw response object from the `requests` library.

    It is intentionally kept minimal and stateless to ensure:
    - Reusability across different APIs/services
    - Testability
    - Clean separation of concerns

    ------------------------------------------------------------------------
    ✅ RESPONSIBILITIES
    ------------------------------------------------------------------------
    ✔ Send HTTP requests (GET, POST, PUT, DELETE, etc.)
    ✔ Attach headers, query params, JSON body, and authentication
    ✔ Return raw `requests.Response` object

    ------------------------------------------------------------------------
    ❌ NON-RESPONSIBILITIES
    ------------------------------------------------------------------------
    ✘ NO response JSON parsing  → handled later by HttpResponse
    ✘ NO validation             → handled by validators
    ✘ NO validators             → handled in tests
    ✘ NO business logic         → handled in helpers
    ✘ NO logging                → handled in higher layers (APIClient / plugins)

    ------------------------------------------------------------------------
    ⚠️ IMPORTANT: "json" PARAMETER CONFUSION
    ------------------------------------------------------------------------
    The `json` parameter in requests:
        json=payload

    DOES NOT mean:
        "parsed JSON response"

    It means:
        "send this Python dict as JSON in the request body"

    Example:
        payload = {"email": "test@test.com"}

        This:
            json=payload

        Sends:
            {"email": "test@test.com"}
        as a JSON HTTP body.

    ------------------------------------------------------------------------
    📦 RESPONSE HANDLING
    ------------------------------------------------------------------------
    This client RETURNS RAW response:

        requests.Response (comes from the requests library.)

    Which contains:
        response.status_code   → HTTP status (e.g., 200, 400)
        response.text          → raw response body (string)
        response.json()        → parsed JSON (if valid JSON - LOW-LEVEL, may raise ValueError)
        response.headers       → response headers
        response.url           → final URL

    👉 IMPORTANT:
    JSON parsing happens later in:
        HttpResponse.from_http_requests(...)

    ------------------------------------------------------------------------
    🧱 ARCHITECTURE POSITION
    ------------------------------------------------------------------------
        HttpClient (this class)
            ↓
        APIClient (adds retries, logging, wrapping)
            ↓
        HttpResponse (parses JSON)
            ↓
        Helpers / Validators / Tests

    ------------------------------------------------------------------------
    🚀 WHY requests.Session()?
    ------------------------------------------------------------------------
    We use a persistent session to:
    ✔ Reuse TCP connections (performance improvement)
    ✔ Reduce latency in test suites
    ✔ Mimic real client behavior

    This is especially useful in:
    - API test automation
    - High-volume test execution (CI/CD)

    The flow is: HttpClient → requests.Response → HttpResponse → Helpers/Tests


    ------------------------------------------------------------------------
    Default network timeout (seconds)
    ------------------------------------------------------------------------
    IMPORTANT:
    requests library does NOT enforce a timeout by default.
    Without a timeout, a network call may block indefinitely if the server stops responding or the connection hangs.
    Transport layers should ALWAYS enforce a timeout to prevent test suites from freezing.
    This default can be overridden later if needed by higher layers.
    ------------------------------------------------------------------------
    """

    def __init__(self, timeout: tuple[int, int] = (5, 30)):
        """
        Initialize HTTP client.

        Args:
            timeout:
                Default network timeout used for all HTTP requests.

                Format:
                    (connect_timeout, read_timeout)

                connect_timeout → max time to establish TCP connection
                read_timeout    → max time waiting for server response

        Why this exists:
            The requests library has NO default timeout, meaning a request
            could block forever if the server stops responding.

            Setting a default timeout ensures the transport layer is safe
            and prevents test suites from hanging indefinitely.
        """
        # Persistent session improves performance via connection reuse
        self.session = requests.Session()

        # Default request timeout
        self.timeout = timeout

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,  # ✅ REQUEST BODY (not response parsing)
        auth: Optional[Any] = None,
    ) -> requests.Response:
        """
        Send an HTTP request.

        Args:
            method (str): HTTP method (GET, POST, etc.)
            url (str): Full URL
            headers (dict, optional): HTTP headers
            params (dict, optional): Query parameters (?key=value)
            json (dict, optional): Python dict to send as JSON body
                                   (serialized automatically by requests)
            auth (Any, optional): Authentication object (e.g., OAuth1)

        Returns:
            requests.Response: RAW response object (not parsed)

        The return value of this class is specifically designed to be passed into your next layer:
        HttpResponse.from_http_requests(response)

        Example:
            response = client.request(
                method="POST",
                url="https://api.com/users",
                json={"email": "test@test.com"}
            )

            # Raw access:
            response.status_code
            response.text
            response.json()

        """
        # You are NOT calling requests.Response directly.You are calling self.session.request(..) and this function
        # RETURNS a raw requests.Response class object which is used by def_request_with_backoff(self..)
        # and this method calls response = self.http_client.request(..)
        # 👉 requests library → builds HTTP request → sends it → creates Response object → returns it

        # http_request_response = self.session.request(
        #     method=method,
        #     url=url,
        #     headers=headers,
        #     params=params,
        #     json=json,  # ✅ SEND JSON (not parse)
        #     auth=auth,
        # )
        #
        # return http_request_response

        return self.session.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=json,  # ✅ SEND JSON (not parse)
            auth=auth,
            timeout=self.timeout
        )


