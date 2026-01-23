"""
Preflight Schema Smoke Tests (uses RequestUtility)

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

from EcommerceAPI.src.utilities.requestsUtility import RequestUtility

from tests.customers.schemas.customer import customer_schema
from tests.customers.schemas.order import order_schema
from tests.customers.schemas.product import product_schema
from tests.customers.schemas.coupon import coupon_schema
from EcommerceAPI.src.utilities.truncate_logging_utils import truncate_preview

log = logging.getLogger(__name__)

pytestmark = [pytest.mark.schema, pytest.mark.preflight]


# =====================================================================
#  CORE VALIDATION LOGIC
# =====================================================================

def _fetch_list_and_validate_item(api: RequestUtility, endpoint: str, item_schema: dict, fail_on_empty: bool):
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
        items = api.get(endpoint, expected_status_code=200, schema={"type": "array"})
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
        api.get(f"{endpoint}/{first_id}", expected_status_code=200, schema=item_schema)

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

@pytest.mark.parametrize(
    ("endpoint", "item_schema"),
    [
        ("customers", customer_schema),
        ("products", product_schema),
        ("orders", order_schema),
        ("coupons", coupon_schema),
    ],
    ids=["customers", "products", "orders", "coupons"],
)
def test_schema_validation(request_utility, endpoint, item_schema, fail_on_empty_list):
    """
    Parametrized schema smoke test for the four core WooCommerce API endpoints.
    """
    log.info("Running schema smoke test for: %s", endpoint)

    try:
        _fetch_list_and_validate_item(request_utility, endpoint, item_schema, fail_on_empty_list)
    except Exception as e:
        log.exception("%s: top-level schema smoke check failed.", endpoint)
        pytest.fail(
            f"{endpoint}: schema smoke check failed (fail_on_empty={fail_on_empty_list}): "
            f"{truncate_preview(e)}"
        )
