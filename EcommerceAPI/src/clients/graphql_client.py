import time

from EcommerceAPI.src.core.http_client import HttpClient
from EcommerceAPI.src.core.graphql_response import GraphQLResponse
from EcommerceAPI.src.auth.base_auth import AuthStrategy


class GraphQLClient:
    """
    GraphQL client (orchestration layer).

    Responsibilities:
    - Send GraphQL queries/mutations
    - Delegate HTTP transport to HttpClient
    - Convert raw HTTP responses into GraphQLResponse
    - Apply an (optional) AuthStrategy to outgoing requests

    Notes:
    - No schema validation
    - No assertions
    - No business logic
    - No GraphQL-specific response validation

    Authentication:
    - GraphQL auth is intentionally NOT resolved via auth_resolver /
      auth_factory / AUTH_TYPE — that pipeline is WooCommerce REST's
      OAuth1 mechanism, which does not authenticate WPGraphQL requests
      (proven: OAuth1 + Basic Auth with the login password both fail
      the createProduct capability check; a WordPress Application
      Password over Basic Auth is what WPGraphQL actually recognizes).
      Callers pass in whichever AuthStrategy fits instead.
    """

    def __init__(self, base_url: str, auth_strategy: AuthStrategy | None = None):
        self.base_url = base_url
        self.http = HttpClient()
        self.auth_strategy = auth_strategy

    def execute(
        self,
        query: str,
        variables: dict | None = None,
    ) -> GraphQLResponse:
        """
        Execute a GraphQL query or mutation.

        Args:
            query:
                GraphQL query or mutation string.

            variables:
                Optional GraphQL variables.

        Returns:
            GraphQLResponse:
                Structured GraphQL response.
        """

        payload = {
            "query": query,
            "variables": variables or {},
        }

        request_kwargs = {
            "method": "POST",
            "url": self.base_url,
            "json": payload,
        }

        if self.auth_strategy:
            request_kwargs = self.auth_strategy.apply(request_kwargs)

        start = time.perf_counter()

        response = self.http.request(**request_kwargs)

        elapsed = time.perf_counter() - start

        return GraphQLResponse.from_http_requests(
            response=response,
            elapsed=elapsed,
        )
