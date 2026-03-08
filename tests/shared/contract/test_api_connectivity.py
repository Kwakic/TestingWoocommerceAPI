"""
Preflight Schema Smoke Tests (uses APIClient )

Overview
--------
These lightweight schema tests verify that WooCommerce API endpoints return responses
matching expected JSON schemas. They act as early warnings for schema drift or
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
"""

import pytest
import logging
from jsonschema import ValidationError

from EcommerceAPI.src.clients.api_client import APIClient

from EcommerceAPI.src.utilities.truncate_logging_utils import truncate_preview

log = logging.getLogger(__name__)

pytestmark = [pytest.mark.schema, pytest.mark.contract]


# =====================================================================
#  CORE VALIDATION LOGIC
# =====================================================================

def _fetch_list_and_validate_item(api: APIClient, endpoint: str, item_schema: dict, fail_on_empty: bool):
    """
    Performs the schema smoke test for a single endpoint.

    Steps:
    ------
    1. GET /<endpoint> expecting a list.
    2. If list is empty:
         - Skip (default)
         - Fail (if fail_on_empty=True)
    3. Validate the first item's structure (must contain `id`).
    4. GET /<endpoint>/<id> and validate response against the entity schema.

    Any failure includes truncation for clean logs.
    """
    # ---- Step 1: Fetch list ----
    try:
        http_response = api.get(endpoint)

        # ✅ Validate status at test level
        assert http_response.status_code == 200, (
            f"{endpoint}: Expected 200, got {http_response.status_code}"
        )
        # 💡 OPTIONAL (VERY NICE IMPROVEMENT)
        # Instead of inline validation, you could later create
        # def assert_response_list(http_response):
        #     assert http_response.status_code == 200
        #     assert isinstance(http_response.json, list)

        # ✅ Extract JSON
        items = http_response.json

        # Optional safety
        if not isinstance(items, list):
            pytest.fail(f"{endpoint}: Expected list response, got {type(items)}")

        list_len = len(items)
    except Exception as e:
        log.exception("%s: failed to fetch list.", endpoint)
        pytest.fail(
            f"{endpoint}: failed to fetch list (fail_on_empty={fail_on_empty}): "
            f"{truncate_preview(e)}"
        )

    # ---- Step 2: Empty list handling ----
    if list_len == 0:
        msg = f"{endpoint}: returned 0 items (fail_on_empty={fail_on_empty})"
        if fail_on_empty:
            pytest.fail(msg)
        pytest.skip(msg)

    # ---- Step 3: Validate first item ----
    first_item = items[0]
    first_id = first_item.get("id")

    if not first_id:
        pytest.fail(
            f"{endpoint}: first item missing 'id' field (sample_size={list_len})"
        )

    # ---- Step 4: GET /<endpoint>/<id> with schema validation ----
    try:
        http_response = api.get(f"{endpoint}/{first_id}")

        assert http_response.status_code == 200, (
            f"{endpoint}/{first_id}: Expected 200, got {http_response.status_code}"
        )

        response_json = http_response.json

        # ✅ Schema validation MOVED HERE
        from jsonschema import validate
        validate(instance=response_json, schema=item_schema)

    except ValidationError as ve:
        log.exception("%s: schema validation error for id=%s", endpoint, first_id)
        pytest.fail(
            f"{endpoint}: schema validation failed for id={first_id} "
            f"(sample_size={list_len}, fail_on_empty={fail_on_empty}): "
            f"{truncate_preview(ve.message)}"
        )

    except Exception as e:
        log.exception("%s: unexpected exception during schema validation.", endpoint)
        pytest.fail(
            f"{endpoint}: validation request failed (sample_size={list_len}, "
            f"fail_on_empty={fail_on_empty}): {truncate_preview(e)}"
        )


# =====================================================================
#  PARAMETRIZED TEST
# =====================================================================

@pytest.mark.preflight
@pytest.mark.parametrize(
    "endpoint",
    ["customers", "products", "orders", "coupons"]
)
def test_api_endpoint_available(api_client, endpoint):
    """
    Preflight API availability check.

    Fail fast if API is broken

    Ensures core API endpoints respond correctly before
    running the full test suite.
    """

    response = api_client.get(endpoint)

    assert response.status_code == 200
    assert isinstance(response.json, list)

