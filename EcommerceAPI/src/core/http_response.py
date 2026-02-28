from dataclasses import dataclass
from typing import Any, Dict, Optional
import requests


@dataclass
class HttpResponse:
    """
    HTTP RESPONSE WRAPPER (Transport → Framework Bridge)

    This class represents a structured, unified view of an HTTP response.

    It is created inside RequestUtility after receiving a raw response from HttpClient.

    ------------------------------------------------------------------------
    🎯 PURPOSE
    ------------------------------------------------------------------------
    Convert raw `requests.Response` into a consistent, framework-friendly object.

    It solves a major problem in test frameworks:

        ❌ Returning dict → loses headers, status, timing, debugging info
        ❌ Returning raw Response → too low-level and inconsistent usage

    ✅ This wrapper gives you BOTH:
        - Parsed JSON (for assertions)
        - Raw data (for debugging / observability)

    ------------------------------------------------------------------------
    ✅ RESPONSIBILITIES
    ------------------------------------------------------------------------
    ✔ Store HTTP status code
    ✔ Store headers
    ✔ Parse JSON safely (if possible)
    ✔ Preserve raw response text
    ✔ Expose request metadata (URL, elapsed time)

    ------------------------------------------------------------------------
    ❌ NON-RESPONSIBILITIES
    ------------------------------------------------------------------------
    ✘ NO validation (schema/business)
    ✘ NO assertions
    ✘ NO logging
    ✘ NO retries
    ✘ NO request execution

    👉 It is a PURE DATA CONTAINER

    ------------------------------------------------------------------------
    📦 ATTRIBUTES
    ------------------------------------------------------------------------
    status_code : int
        HTTP status code (e.g., 200, 400, 404, 500)

    headers : Dict[str, Any]
        Response headers returned by the server

    json : Optional[Any]
        Parsed response body (already deserialized from JSON).:
            - dict → most API responses
            - list → collection endpoints
            - None → if response is not valid JSON

        ⚠️ IMPORTANT:
        - This is NOT the same as `requests.Response.json()`
        - This is a PRE-PARSED attribute, not a method
        - Safe to use (will never raise ValueError)

    Example:
        raw_response.json()   → method (can fail)
        http_response.json   → attribute (safe)

    text : str
        Raw response body (always available)

        Useful for:
        - debugging malformed responses
        - logging
        - non-JSON APIs

    url : str
        Final request URL (after redirects if any)

    elapsed : float
        Request duration in seconds

    raw response = (Structured HTTP response (parsed + normalized))
    ------------------------------------------------------------------------
    🔄 LIFECYCLE (VERY IMPORTANT)
    ------------------------------------------------------------------------

        HttpClient (raw HTTP)
                ↓
        requests.Response
                ↓
        HttpResponse.from_requests(...)  ← HERE
                ↓
        HttpResponse (this object)
                ↓
        Helpers / Validators / Tests

    ------------------------------------------------------------------------
    🧪 USAGE PATTERNS
    ------------------------------------------------------------------------

    ✅ POSITIVE TEST (via helper):
        response_dict = customer_helper.create_customer(...)
        # helper extracts: http_response.json

    ✅ NEGATIVE TEST (raw API):
        http_response = raw_customer_api.post(...)
        assert http_response.status_code == 400
        response = http_response.json

    ✅ DEBUGGING:
        http_response.headers
        http_response.text
        http_response.elapsed

    ------------------------------------------------------------------------
    ⚠️ DESIGN DECISION (IMPORTANT)
    ------------------------------------------------------------------------
    ALL API calls return HttpResponse at transport level.

    BUT:
        - Helpers return dict (business-friendly)
        - Raw API returns HttpResponse (full control)

    This enables:
        ✔ Clean tests
        ✔ Powerful debugging
        ✔ Flexible validation

    ------------------------------------------------------------------------
    🚀 WHY THIS MATTERS (ENTERPRISE)
    ------------------------------------------------------------------------
    This pattern is used in mature frameworks because it:

    ✔ Prevents data loss
    ✔ Separates transport from validation
    ✔ Supports both positive and negative testing cleanly
    ✔ Makes logging & debugging significantly easier
    ✔ Prepares for future extensions (async, tracing, metrics)

    CLI:
    If you debug and want to see formatted response to JSON then use the "Professional API Log" Style (Cleanest)
    If you want to see the headers and the body formatted exactly like a real JSON API response (using " and true),
    run this snippet in your Pdb:
    (Pdb) import json; print(f"Status: {response.status_code}\nHeaders: {json.dumps(response.headers, indent=2)}\nBody: {json.dumps(response.json, indent=2)}")
    or to see also the text, content and elapsed:
    (Pdb) import json; print(f"\n--- API RESPONSE ---\nURL: {response.url}\nStatus: {response.status_code}\nElapsed: {response.elapsed}s\n\nHEADERS:\n{json.dumps(response.headers, indent=2)}\n\nJSON BODY:\n{json.dumps(response.json, indent=2)}\n\nRAW TEXT:\n{response.text}\n\nRAW CONTENT (BYTES):\n{response.content}\n--------------------")

    To see the response in JSON: Convert the Python dictionary into a JSON-formatted string:
    (Pdb)  import json; print(json.dumps(customer, indent=4))

    ------------------------------------------------------------------------
    """
    status_code: int
    headers: Dict[str, str]
    json: Optional[Any]
    text: str
    url: str
    elapsed: float
    content: Optional[bytes] = None

    @classmethod
    def from_requests(cls, response: requests.Response, elapsed: float) -> "HttpResponse":
        """
        Factory method to convert a raw `requests.Response`
        into a structured HttpResponse object.

        --------------------------------------------------------------------
        🔍 WHAT HAPPENS HERE
        --------------------------------------------------------------------
        - Extracts status_code, headers, text, url
        - Attempts to parse JSON safely
        - Never raises if JSON parsing fails

        --------------------------------------------------------------------
        ⚠️ JSON PARSING BEHAVIOR
        --------------------------------------------------------------------
        We attempt:

            response.json()

        If response is NOT valid JSON:
            → ValueError is raised
            → We catch it and set json = None

        This ensures:
        ✔ No crashes on non-JSON responses
        ✔ Consistent interface for all responses

        --------------------------------------------------------------------
        Args:
        --------------------------------------------------------------------
        response : requests.Response
            Raw HTTP response returned by HttpClient

        elapsed : float
            Time taken to execute the request (seconds)

        --------------------------------------------------------------------
        Returns:
        --------------------------------------------------------------------
        HttpResponse
            Structured response object

        --------------------------------------------------------------------
        Example:
        --------------------------------------------------------------------
        raw_response = http_client.request(...)
        http_response = HttpResponse.from_requests(raw_response, elapsed=0.45)

        http_response.status_code  → 200
        http_response.json         → {"id": 1, ...}
        http_response.text         → '{"id": 1, ...}'

        """
        try:
            json_data = response.json()
        except ValueError:
            json_data = None

        return cls(
            status_code=response.status_code,
            headers=dict(response.headers),
            json=json_data,
            text=response.text,
            url=response.url,
            elapsed=elapsed,
            content=response.content
        )


# It returns raw requests.Response
# This response is a full requests.Response object from the requests library, which includes:
#     .status_code → e.g., 200, 400
#     .headers → response headers
#     .json() → parsed JSON body (if possible)
#     .text → raw response body as a string
#     .url → full URL that was hit
#     .elapsed → elapsed time


# # To see the entire raw response log the following:

# logger.debug(f"""🌐 Raw Response:
# Status: {response.status_code}
# URL: {response.url}
# Headers: {response.headers}
# Body:{response.text}
# """)
