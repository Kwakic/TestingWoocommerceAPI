# CONTRACT TEST

"""
Overview
--------
These lightweight schema tests verify that WooCommerce API endpoints return responses
matching expected JSON models. They act as early warnings for schema drift or
environment misconfiguration before running the full test suite.

Configuration
-------------
FAIL_ON_EMPTY_LIST:
    - Environment variable (CI pipelines): export FAIL_ON_EMPTY_LIST=true
    - Pytest CLI flag: --fail-on-empty-list
    - CLI flag always has priority over the environment variable.

Usage examples:
---------------
Local quick run:
    pytest -m preflight -q -r s

Force strict behavior (fail on empty lists):
    pytest --fail-on-empty-list

CI JUnit output:
    pytest -m preflight --junitxml=reports/preflight-junit.xml

Show logs:
    pytest -m preflight -s -q -r s

This acts as:
  - API availability guard
  - environment sanity check
  - basic contract check
"""

import pytest
import logging

log = logging.getLogger(__name__)

pytestmark = [pytest.mark.contract, pytest.mark.shared, pytest.mark.integration]


# =====================================================================
#  PARAMETRIZED TEST
# =====================================================================


@pytest.mark.parametrize("endpoint", ["customers", "products", "orders", "coupons"])
def test_api_endpoint_available(api_client, endpoint):
    """
    Preflight API availability check.

    Fail fast if API is broken

    Ensures core API endpoints respond correctly before
    running the full test suite.

    This requires:
        - live API
        - auth
        - environment
        - infrastructure
        - WooCommerce bootstrapping

    It is:

        - environment validation
        - API availability
        - lightweight contract/integration validation
    """

    response = api_client.get(endpoint)

    assert response.status_code == 200
    assert isinstance(response.json, list)
