
import pytest
import logging
from jsonschema import validate
from unittest.mock import patch
from datetime import timedelta

from tests.shared.schemas.customer import customer_schema
from EcommerceAPI.src.utilities.date_timestamp_utils import get_now_utc_floor, to_iso_utc, safe_parse_utc_datetime

logger = logging.getLogger(__name__)
#  logger.setLevel(logging.DEBUG)  # already set in pytest.ini

# Apply shared markers for the test module
pytestmark = [pytest.mark.customers, pytest.mark.smoke]


@pytest.mark.tcid09
def test_get_all_customers_list_not_empty_and_valid_schema(customer_helper, customers_dao):
    """
    Basic schema_validation test: Get all customers (paginated) and validate response schema for each.

    Checks:
    - The API returns a non-empty list of customers.
    - Each customer object conforms to the expected JSON schema.
    - Pagination works up to first page (default per_page=100).
    """

    logger.info("🟢 Calling GET all customers without filters.")
    customers = customer_helper.call_list_all_customers_paginated()

    # Assert we got a non-empty list
    assert customers, "❌ No customers returned from GET /customers"
    assert isinstance(customers, list), f"Expected list of customers, got: {type(customers)}"

    logger.info(f"✅ Retrieved {len(customers)} customers.")

    # Validate schema of each customer returned
    for cust in customers:
        try:
            validate(instance=cust, schema=customer_schema)
        except Exception as e:
            pytest.fail(f"❌ Customer schema validation failed for ID={cust.get('id')}: {e}")

    logger.info("✅ All returned customers conform to schema.")


@pytest.mark.regression
@pytest.mark.tcid10
def test_get_all_customers_pagination_boundary(customer_helper, customers_dao):
    # You could write a parameterized test to test multiple per_page boundary values (1, 2, 10, etc.), like:
    # @pytest.mark.parametrize("per_page", [1, 2, 5])
    # def test_pagination_with_various_per_page(per_page, customer_resources_fixture):
    #     ...
    # Helps find issues at page size extremes (off-by-one, 0-index bugs, etc.).
    """
    Tests that pagination works correctly by fetching customers with a small per_page value.

    - Calls multiple pages until no more customers or max_pages is hit.
    - Asserts no duplicates across pages.
    - Validates schema for each customer.
    - Logs a warning if max_pages is hit without exhausting data.
    """

    per_page = 5
    max_pages = 20  # Safeguard: increase if dataset is large

    logger.info(f"🟢 Testing pagination boundary with per_page={per_page}, max_pages={max_pages}")

    params = {'per_page': per_page}
    all_customers = customer_helper.call_list_all_customers_paginated(params=params, max_pages=max_pages)

    assert all_customers, "❌ No customers returned from paginated GET /customers"
    assert isinstance(all_customers, list), f"Expected list of customers, got: {type(all_customers)}"

    # 	Added truncation warning if page cap is reached
    if len(all_customers) >= per_page * max_pages:
        logger.warning(f"⚠️ Retrieved exactly {len(all_customers)} customers, "
                       f"which matches per_page * max_pages. Results may be truncated.")

    # Check for duplicates by customer ID
    ids = [c['id'] for c in all_customers]
    assert len(ids) == len(set(ids)), "❌ Duplicate customers found across paginated results"

    logger.info(f"✅ Retrieved {len(all_customers)} unique customers across pages.")

    # Validate schema on all customers
    for cust in all_customers:
        try:
            validate(instance=cust, schema=customer_schema)
        except Exception as e:
            logger.error(f"❌ Schema validation failed for customer ID={cust.get('id')}: {e}")
            logger.debug(f"Offending customer JSON: {cust}")
            pytest.fail(f"❌ Customer schema invalid for ID={cust.get('id')}")

    logger.info("✅ All paginated customers conform to schema.")


@pytest.mark.negative_test
@pytest.mark.regression
@pytest.mark.tcid11
def test_get_all_customers_empty_list_with_mock(customer_helper, customers_dao):
    """
    Test GET /customers returns an empty list when no customers exist.
    Uses mocking to simulate an empty DB/API response.

    Explanation:
    - The test uses patch.object to replace the call_list_all_customers_paginated method only for this test run.
    - The method is mocked to always return an empty list.
    - Then the test asserts the returned list is empty, simulating no customers in DB.
    - You get a fully isolated test that doesn't depend on DB state.

    Mocking the empty DB scenario is a great idea for a test — it isolates the API behavior without requiring real
    DB changes and keeps tests reliable and fast.
    """

    with patch.object(customer_helper, 'call_list_all_customers_paginated', return_value=[]):
        logger.info("🟢 Mocking call_list_all_customers_paginated to return empty list")
        customers = customer_helper.call_list_all_customers_paginated()

        # The mocked method should return an empty list
        assert customers == [], "❌ Expected empty list from mocked call_list_all_customers_paginated"
        logger.info("✅ Successfully mocked empty customer list")


@pytest.mark.negative_test
@pytest.mark.tcid19
def test_list_customers_created_in_the_future_returns_empty(customer_helper, customers_dao):
    """
    🔒 Negative Test: Ensure no customers are returned with a future 'date_created_gmt' timestamp.

    🎯 Purpose:
        - Ensures backend systems don't create customers dated *after* current UTC time.
        - Detects system clock drift, bad test data, or time zone calculation bugs.

    🕒 Timestamp Strategy:
        - Capture the UTC 'now' once at test start.
        - Strip microseconds for cleaner API compatibility.
        - Apply a ±1 second tolerance buffer to account for real-world race conditions.
        Why include a 1-second tolerance buffer?
        - Some systems (or APIs) round timestamps up to the next second.
        - Async test execution might cause a very recent creation to appear slightly in the future.
        - Adding this buffer prevents false negatives without compromising test intent.

    🛡️ Enabled: Tolerance Buffer (±1 second)
        - This buffer helps avoid false negatives caused by:
            • Millisecond delays in processing
            • API/backend time rounding
            • System clock skew

    🧪 Test Expectation:
        - The filtered list of customers created after now (with buffer) should be empty.
    """

    # 🕒 Step 1: Capture the current UTC time once (and strip microseconds)

    # Get the current UTC datetime with microseconds stripped (clean second precision)
    now_utc = get_now_utc_floor()
    # Convert the datetime to an ISO 8601 string with 'Z' suffix (e.g., '2025-08-03T12:00:00Z') for API filtering
    created_after = to_iso_utc(now_utc)
    logger.info(f"🔍 Fetching customers created after current time: {created_after}")

    # 🚀 Step 2: Fetch customers. Call the /customers API with created_after filter set to "now".
    filtered_customers = customer_helper.call_list_all_customers_paginated(
        created_after=created_after
    )

    logger.info(f"📝 Initial API returned {len(filtered_customers)} customers")

    # ⏱ Step 3: Apply ±1 second tolerance to reduce test flakiness due to rounding or latency
    # Filter out customers that were created within 1 second *after* `now_utc`.
    # - it goes through a list (filtered_customers)
    # - it filters based on a condition
    # - it collects the matching items (cust) into a new list (future_customers)
    tolerance = timedelta(seconds=1)
    future_customers = [
        cust for cust in filtered_customers
        if safe_parse_utc_datetime(cust.get("date_created_gmt", "")) > (now_utc + tolerance)
    ]

    # ❌ Step 4: Assert that no customer will exist *truly* in the future (beyond the buffer)
    assert not future_customers, (
        f"❌ Found {len(future_customers)} customer(s) created after now (+1s buffer) — "
        f"Possible clock drift or invalid timestamp. Base time: {created_after}"
    )

    logger.info(f"✅ No customers found beyond {created_after} (+1s buffer) — test passed")

    # 📋 Step 5: Optional debugging trace for any unexpected future entries (within or beyond buffer)
    for cust in filtered_customers:
        raw_ts = cust.get("date_created_gmt", "")
        try:
            parsed_ts = safe_parse_utc_datetime(raw_ts)
            logger.debug(
                f"🕵️ Customer ID={cust['id']} | date_created_gmt={raw_ts} | parsed={parsed_ts.isoformat()}"
            )
        except Exception as e:
            logger.warning(
                f"⚠️ Failed to parse timestamp for customer ID={cust.get('id')} | raw_ts={raw_ts} | Error: {e}"
            )
