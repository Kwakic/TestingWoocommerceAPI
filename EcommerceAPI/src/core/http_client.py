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
    ✘ NO validation            → handled by validators
    ✘ NO assertions            → handled in tests
    ✘ NO business logic        → handled in helpers
    ✘ NO logging               → handled in higher layers (RequestUtility / plugins)

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

        requests.Response

    Which contains:
        response.status_code   → HTTP status (e.g., 200, 400)
        response.text          → raw response body (string)
        response.json()        → parsed JSON (if valid JSON)
        response.headers       → response headers
        response.url           → final URL

    👉 IMPORTANT:
    JSON parsing happens later in:
        HttpResponse.from_requests(...)

    ------------------------------------------------------------------------
    🧱 ARCHITECTURE POSITION
    ------------------------------------------------------------------------
        HttpClient (this class)
            ↓
        RequestUtility (adds retries, logging, wrapping)
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

    ------------------------------------------------------------------------
    """

    def __init__(self):
        # Persistent session improves performance via connection reuse
        self.session = requests.Session()

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

        return self.session.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=json,  # ✅ SEND JSON (not parse)
            auth=auth,
        )
