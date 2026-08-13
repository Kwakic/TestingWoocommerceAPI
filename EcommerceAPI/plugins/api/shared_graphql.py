# -------------------------
# graphql_client fixture
# -------------------------
import pytest

from EcommerceAPI.src.clients.graphql_client import GraphQLClient
from EcommerceAPI.src.configs.config_graphql import get_graphql_host
from EcommerceAPI.src.auth.basic_auth import BasicAuth
from EcommerceAPI.src.utils.credentials_utility import get_wp_admin_credentials


@pytest.fixture(scope="session")
def graphql_client():
    """
    Provide a session-scoped, authenticated GraphQLClient instance.

    The GraphQL endpoint is resolved from the shared framework
    configuration for the active API_ENV.

    Authentication uses a WordPress Application Password over HTTP
    Basic Auth (WP_ADMIN_USER / WP_ADMIN_APP_PASSWORD), which is what
    WPGraphQL/WooGraphQL actually checks for mutation capabilities.
    This is separate from the REST framework's AUTH_TYPE/OAuth1
    pipeline by design.
    """

    graphql_base_url = get_graphql_host()
    wp_admin_creds = get_wp_admin_credentials()

    auth_strategy = BasicAuth(
        username=wp_admin_creds["wp_admin_user"],
        password=wp_admin_creds["wp_admin_app_password"],
    )

    return GraphQLClient(base_url=graphql_base_url, auth_strategy=auth_strategy)
