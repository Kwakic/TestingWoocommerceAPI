from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests


@dataclass
class GraphQLResponse:
    """
    GRAPHQL RESPONSE WRAPPER
    (Raw HTTP Response → GraphQL Framework Response)

    Converts a raw `requests.Response` into a structured,
    GraphQL-specific response object.

    ------------------------------------------------------------------------
    RESPONSIBILITIES
    ------------------------------------------------------------------------

    ✔ Store HTTP status code
    ✔ Store response headers
    ✔ Parse the GraphQL response body safely
    ✔ Expose GraphQL `data`
    ✔ Expose GraphQL `errors`
    ✔ Preserve raw response text
    ✔ Expose request metadata (URL, elapsed time)

    ------------------------------------------------------------------------
    NON-RESPONSIBILITIES
    ------------------------------------------------------------------------

    ✘ NO schema validation
    ✘ NO business validation
    ✘ NO assertions
    ✘ NO logging
    ✘ NO retries
    ✘ NO request execution

    This is a PURE DATA CONTAINER.

    ------------------------------------------------------------------------
    GRAPHQL SUCCESS CONTRACT
    ------------------------------------------------------------------------

    Unlike REST, HTTP 200 does not necessarily mean that the
    GraphQL operation succeeded.

        HTTP 200 + no errors[]  → GraphQL success
        HTTP 200 + errors[]     → GraphQL failure
        HTTP != 200             → GraphQL failure

    Therefore `.ok` represents both the HTTP and GraphQL result.
    """

    status_code: int
    headers: Dict[str, str]
    data: Optional[Any]
    errors: List[Any]
    text: str
    url: str
    elapsed: float
    content: Optional[bytes] = None

    @property
    def ok(self) -> bool:
        """
        Return whether the GraphQL operation succeeded.

        GraphQL may return HTTP 200 even when the operation contains
        GraphQL-level errors, so status_code alone is insufficient.
        """
        return self.status_code == 200 and not self.errors

    @classmethod
    def from_http_requests(
        cls,
        response: requests.Response,
        elapsed: float,
    ) -> "GraphQLResponse":
        """
        Convert a raw `requests.Response` into a structured
        `GraphQLResponse`.

        JSON parsing is performed safely. If the response body is
        not valid JSON, an empty GraphQL body is used rather than
        raising a parsing exception.

        Args:
            response:
                Raw response returned by HttpClient.

            elapsed:
                Request duration in seconds.

        Returns:
            GraphQLResponse:
                Structured GraphQL response object.
        """

        try:
            json_data = response.json()
        except ValueError:
            json_data = {}

        # A valid GraphQL response body is expected to be a JSON object.
        # Keep the wrapper defensive if the server returns something else.
        if not isinstance(json_data, dict):
            json_data = {}

        return cls(
            status_code=response.status_code,
            headers=dict(response.headers),
            data=json_data.get("data"),
            errors=json_data.get("errors") or [],
            text=response.text,
            url=response.url,
            elapsed=elapsed,
            content=response.content,
        )
