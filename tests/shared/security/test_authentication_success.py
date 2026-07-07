# SECURITY TEST
"""
================================================================================
Authentication Success Test

Purpose
-------
Verify that valid OAuth credentials are accepted by every supported
framework entity.

Unlike the authentication rejection matrix, this test validates the
successful authentication path.

Entity discovery is delegated to the framework.

The entities plugin remains the Single Source of Truth, therefore
adding a new entity automatically extends this test without modifying
its implementation.
================================================================================
"""

import pytest
from EcommerceAPI.plugins.entities import discover_entity_names


pytestmark = [pytest.mark.security, pytest.mark.smoke, pytest.mark.shared]


# ------------------------------------------------------------------
# Framework entity discovery.
#
# Every supported framework entity must accept authenticated requests.
#
# Adding a new entity automatically expands this validation without
# modifying the test.
# ------------------------------------------------------------------


@pytest.mark.parametrize(
    "entity",
    discover_entity_names(),
)
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
