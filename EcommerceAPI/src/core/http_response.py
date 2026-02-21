from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class HttpResponse:
    """
    Lightweight wrapper around an HTTP response.

    Purpose:
    --------
    Provides a unified, structured representation of an HTTP response,
    exposing both raw and parsed data in a consistent way.

    This allows:
    - Easy debugging (headers, URL, elapsed time)
    - Access to parsed JSON when available
    - Avoiding loss of raw response data (unlike returning dict only)

    Attributes:
    -----------
    status_code : int
        HTTP status code (e.g., 200, 404, 500)

    headers : Dict[str, Any]
        Response headers returned by the server

    json : Optional[Any]
        Parsed JSON body (dict/list) if response is JSON, else None

    text : str
        Raw response body as string (always available)

    url : str
        Final request URL (after redirects if any)

    elapsed : float
        Request duration in seconds

    Notes:
    ------
    - This object does NOT perform validation or assertions.
    - It is purely a transport-layer representation.
    - Higher layers (API / validators) decide how to use it.
    """

    status_code: int
    headers: Dict[str, Any]
    json: Optional[Any]
    text: str
    url: str
    elapsed: float

    @classmethod
    def from_requests(cls, response, elapsed: float) -> "HttpResponse":
        """
        Build HttpResponse from a requests.Response object.

        Args:
        -----
        response : requests.Response
            Raw response returned by requests/http_client

        elapsed : float
            Time taken to execute the request (seconds)

        Returns:
        --------
        HttpResponse
            Structured response object with parsed JSON (if available)
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
