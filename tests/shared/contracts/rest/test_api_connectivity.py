"""Live REST collection endpoint availability checks.

Run this with the shared REST contract suite; it requires a configured,
reachable WooCommerce API. It verifies that each supported collection endpoint
returns HTTP 200 and a JSON array. It does not validate entity fields.

Examples:
    pytest tests/shared/contracts/rest/test_api_connectivity.py -q
    pytest tests/shared/contracts/rest -v
"""

import pytest
import logging

from EcommerceAPI.src.metadata.entity_metadata import discover_framework_entities

log = logging.getLogger(__name__)

pytestmark = [pytest.mark.contract, pytest.mark.shared, pytest.mark.integration]

# ---------------------------------------------------------------------
# Business entities officially supported by the framework.
#
# Shared framework suites execute once for every supported entity.
# The registry is maintained centrally in entity_metadata.py.
# ---------------------------------------------------------------------

ENTITIES = discover_framework_entities()

# =====================================================================
#  PARAMETRIZED TEST
# =====================================================================


@pytest.mark.parametrize("endpoint", ENTITIES)
def test_api_endpoint_available(api_client, endpoint):
    """
    Check that a supported REST collection endpoint is available.

    This live API contract check requires valid API configuration and
    authentication. A successful response must contain a JSON array.
    """

    response = api_client.get(endpoint)

    assert response.status_code == 200
    assert isinstance(response.json, list)
