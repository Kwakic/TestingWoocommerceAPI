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
    Verify the collection response's basic HTTP and JSON format contract.

    Checks for HTTP 200, an application/json content type, and a decoded
    JSON array. Entity-specific fields are outside this transport-level check.
    """

    response = api_client.get(endpoint)

    assert response.status_code == 200

    content_type = response.headers.get("Content-Type", "")
    assert "application/json" in content_type

    assert isinstance(response.json, list)
