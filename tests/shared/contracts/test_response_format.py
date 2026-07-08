# CONTRACT TEST

import pytest

from EcommerceAPI.src.metadata.entity_metadata import discover_framework_entities

pytestmark = [pytest.mark.shared, pytest.mark.contract, pytest.mark.integration]

# ---------------------------------------------------------------------
# Business entities officially supported by the framework.
#
# Shared framework suites execute once for every supported entity.
# The registry is maintained centrally in entity_metadata.py.
# ---------------------------------------------------------------------


ENTITIES = discover_framework_entities()


@pytest.mark.parametrize("endpoint", ENTITIES)
def test_api_returns_json(api_client, endpoint):
    """
    API response format guard.
    It ensures that every public endpoint follows the transport contract.

    Ensures endpoints return JSON responses and
    correct content-type headers.

    Detects:
        - PHP errors returning HTML
        - proxy misconfiguration
        - incorrect content types
        - broken JSON serialization

    This test validates:
        - response content-type
        - JSON serialization
        - response structure expectations
        - schema-ish transport guarantees

    That is:
        - contract validation
        - transport contract validation
        - API format guarantee
    """

    response = api_client.get(endpoint)

    assert response.status_code == 200

    content_type = response.headers.get("Content-Type", "")
    assert "application/json" in content_type

    assert isinstance(response.json, list)
