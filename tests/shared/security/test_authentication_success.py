import pytest

pytestmark = [
    pytest.mark.security,
    pytest.mark.smoke,
    pytest.mark.shared
]

ENTITIES = [
    "customers",
    "products",
    "orders",
    "coupons",
]


@pytest.mark.parametrize("entity", ENTITIES)
def test_authenticated_requests_are_allowed(api_client, entity):
    """
    Authentication success guard.

    Ensures valid OAuth credentials allow access
    to WooCommerce API endpoints.

    This complements the negative authentication matrix
    which verifies invalid credentials are rejected.
    """

    response = api_client.get(entity)

    assert response.status_code == 200
    assert isinstance(response.json, list)