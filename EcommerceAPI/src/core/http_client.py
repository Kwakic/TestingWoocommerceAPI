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
