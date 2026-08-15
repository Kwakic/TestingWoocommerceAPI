import logging
import re
import time

from EcommerceAPI.src.core.http_client import HttpClient
from EcommerceAPI.src.core.graphql_response import GraphQLResponse
from EcommerceAPI.src.auth.base_auth import AuthStrategy

log = logging.getLogger(__name__)


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

    @staticmethod
    def _get_operation_info(query: str) -> tuple[str, str]:
        """Return the GraphQL operation type and name for logging."""
        # Remove leading whitespace and GraphQL comments before inspecting
        # the operation definition.
        cleaned_query = re.sub(r"^\s*(?:#.*(?:\r?\n|$))*", "", query)

        match = re.match(
            r"^(query|mutation|subscription)\b(?:\s+([A-Za-z_][A-Za-z0-9_]*))?",
            cleaned_query,
        )

        if not match:
            return "unknown", "unknown"

        operation_type = match.group(1)
        operation_name = match.group(2)

        if operation_name:
            return operation_type, operation_name

        # Anonymous operations have no GraphQL operation name. For logging,
        # use the first root field (e.g. createProduct) so the log remains
        # meaningful without requiring a GraphQL parser.
        root_field_match = re.search(
            r"\{\s*([A-Za-z_][A-Za-z0-9_]*)",
            cleaned_query,
        )

        operation_name = root_field_match.group(1) if root_field_match else "unknown"

        return operation_type, operation_name

    @staticmethod
    def _get_http_error_message(status_code: int) -> str:
        """Return an actionable description for an HTTP-level GraphQL failure."""
        messages = {
            400: "Bad request — the GraphQL endpoint rejected the HTTP request.",
            401: "Authentication failed — check the GraphQL credentials.",
            403: "Access forbidden — the authenticated user is not allowed to access the GraphQL endpoint.",
            404: "GraphQL endpoint not found — check the GraphQL URL and selected environment.",
            405: "HTTP method not allowed — the GraphQL endpoint does not accept this request method.",
            408: "Request timed out — the GraphQL endpoint did not respond in time.",
            429: "Too many requests — the GraphQL endpoint rate-limited the request.",
            500: "GraphQL server error — the server failed while processing the request.",
            502: "Bad gateway — the GraphQL endpoint could not be reached through the gateway.",
            503: "GraphQL service unavailable — the endpoint is unavailable.",
            504: "Gateway timeout — the GraphQL endpoint did not respond in time.",
        }

        return messages.get(
            status_code,
            f"HTTP request failed with status {status_code}.",
        )

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

        graphql_response = GraphQLResponse.from_http_requests(
            response=response,
            elapsed=elapsed,
        )

        operation_type, operation_name = self._get_operation_info(query)

        if graphql_response.status_code >= 400:
            error_message = self._get_http_error_message(graphql_response.status_code)

            log.error(
                "❌ GraphQL request failed → HTTP %s (completed in %.2fs)",
                graphql_response.status_code,
                elapsed,
            )
            log.error("   %s", error_message)
            log.error("   Endpoint: %s", graphql_response.url)

        elif graphql_response.errors:
            log.error(
                "❌ GraphQL %s %s → HTTP %s (completed in %.2fs)",
                operation_type,
                operation_name,
                graphql_response.status_code,
                elapsed,
            )

            for error in graphql_response.errors:
                log.error(
                    "   GraphQL error: %s",
                    error.get("message", error) if isinstance(error, dict) else error,
                )
        else:
            log.info(
                "🔷 GraphQL %s %s → HTTP %s (completed in %.2fs)",
                operation_type,
                operation_name,
                graphql_response.status_code,
                elapsed,
            )

        return graphql_response
