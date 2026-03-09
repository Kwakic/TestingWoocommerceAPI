import pytest

pytestmark = [pytest.mark.preflight]

ENTITIES = [
    "customers",
    "products",
    "orders",
    "coupons",
]


@pytest.mark.parametrize("endpoint", ENTITIES)
def test_api_returns_json(api_client, endpoint):
    """
    API response format guard.

    Ensures endpoints return JSON responses and
    correct content-type headers.

    Detects:
        - PHP errors returning HTML
        - proxy misconfiguration
        - incorrect content types
        - broken JSON serialization
    """

    response = api_client.get(endpoint)

    assert response.status_code == 200

    content_type = response.headers.get("Content-Type", "")
    assert "application/json" in content_type

    assert isinstance(response.json, list)