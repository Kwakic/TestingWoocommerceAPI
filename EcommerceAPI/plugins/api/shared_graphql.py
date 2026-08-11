# -------------------------
# graphql_client fixture
# -------------------------
import pytest

from EcommerceAPI.src.clients.graphql_client import GraphQLClient
from EcommerceAPI.src.configs.config_graphql import get_graphql_host


@pytest.fixture(scope="session")
def graphql_client():
    """
    Provide a session-scoped GraphQLClient instance.

    The GraphQL endpoint is resolved from the shared framework
    configuration for the active API_ENV.

    This fixture only wires configuration into the GraphQL client.
    GraphQL connectivity validation will be added separately once
    the GraphQL endpoint is available.
    """

    graphql_base_url = get_graphql_host()

    return GraphQLClient(base_url=graphql_base_url)
