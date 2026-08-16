"""
HTTP Basic authentication strategy.

Used by the GraphQL client to authenticate against WPGraphQL
with a WordPress Application Password.
"""

from typing import Dict, Any
from .base_auth import AuthStrategy


class BasicAuth(AuthStrategy):
    """
    HTTP Basic authentication for GraphQL requests.

    GraphQL uses WordPress Application Password credentials:
    - username: WordPress user
    - password: WordPress Application Password

    This strategy is used by the GraphQL client and is intentionally
    separate from the OAuth1 authentication used by the WooCommerce
    REST API.
    """

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password

    def apply(self, request_kwargs: Dict[str, Any]) -> Dict[str, Any]:

        request_kwargs["auth"] = (self.username, self.password)

        return request_kwargs
