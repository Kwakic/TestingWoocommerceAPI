import requests
from typing import Any, Dict, Optional


class HttpClient:
    """
    LOW-LEVEL HTTP client.

    Responsibilities:
    -----------------
    ✔ Send HTTP requests
    ✔ Return raw Response

    Non-responsibilities:
    ---------------------
    ✘ No JSON parsing
    ✘ No validation
    ✘ No assertions
    """

    def __init__(self):
        # self.session = requests.Session()  # Reuse TCP connections for speed. Using requests.Session() improves
        # # performance by reusing TCP connections. This is helpful if you're hitting the API repeatedly during tests.
        # # It allows us to access to speed up our code when sending requests to the same server. This is perfect for
        # # scraping data or accessing APIs
        self.session = requests.Session()

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        auth: Optional[Any] = None,
    ) -> requests.Response:

        return self.session.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=json,
            auth=auth,
        )
