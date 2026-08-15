# -------------------------
# graphql_client fixture
# -------------------------
import pytest

from EcommerceAPI.src.clients.graphql_client import GraphQLClient
from EcommerceAPI.src.configs.config_graphql import get_graphql_host
from EcommerceAPI.src.auth.basic_auth import BasicAuth
from EcommerceAPI.src.utils.credentials_utility import get_wp_admin_credentials


# ----------------------------------------------------------------
# GraphQL resource registration helper
# ----------------------------------------------------------------


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


@pytest.fixture(scope="module")
def graphql_resources(shared_api_resources):
    """
    Provide resource-registration helpers for GraphQL tests.

    GraphQL uses the same shared resource tracking and teardown mechanism as
    the REST API tests. This fixture does NOT implement its own cleanup.

    Behavior
    --------
    - Registers GraphQL-created resources with `shared_api_resources`.
    - Reuses the existing entity cleanup mechanism at module teardown.
    - Supports `skip_cleanup=True` for cases where a test intentionally wants
      to keep the created resource in the database.

    Example
    -------
        product = create_product(...)
        graphql_resources(
            product["databaseId"]
        )

    To keep the product in the database:

        graphql_resources(
            product["databaseId"],
            skip_cleanup=True,
        )

    This mirrors the existing REST fixture pattern:

        create_valid_product(skip_cleanup=True)

    Notes
    -----
    The cleanup itself remains owned by `shared_api_resources`. GraphQL only
    tells the shared framework which resources were created.
    """

    register = shared_api_resources["register_resource"]

    def _register_product(
        product_id: int | str,
        skip_cleanup: bool = False,
    ) -> None:
        """
        Register a GraphQL-created product for existing framework cleanup.

        Args:
            product_id: WooCommerce/WordPress product database ID.
            skip_cleanup: If True, do not register the product for deletion.
        """
        if skip_cleanup:
            return

        register("products", str(product_id))

    return _register_product
