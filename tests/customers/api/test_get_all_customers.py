import pytest
import logging
from unittest.mock import patch
from datetime import timedelta

from EcommerceAPI.src.utils.generic_utilities import generate_random_string
from EcommerceAPI.src.customers.validators.customer_validators import (
    assert_valid_customer_response,
)
from EcommerceAPI.src.utils.date_timestamp_utils import (
    get_now_utc_floor,
    to_iso_utc,
    safe_parse_utc_datetime,
)

logger = logging.getLogger(__name__)
#  logger.setLevel(logging.DEBUG)  # already set in pytest.ini

pytestmark = [pytest.mark.integration]


@pytest.mark.tcid("TCID-012")
@pytest.mark.contract
@pytest.mark.smoke
def test_get_all_customers_list_not_empty_and_valid_schema(
    customer_helper,
    customers_dao,
    create_valid_customer,
):
    """
    Smoke test for GET /customers endpoint.

    Validates that:
        - API returns a non-empty list of customers
        - Each returned customers has a valid structure (Pydantic validation)

    Test flow:
        1. Create customer for test
        2. Call GET /customers
        3. Ensure response contains customers
        4. Validate structure of each customers
    """

    # --------------------------------------------------
    # Ensure deterministic data
    # --------------------------------------------------
    logger.info("🛠 Creating at least one customer to ensure non-empty dataset.")
    create_valid_customer()

    # --------------------------------------------------
    # Act
    # --------------------------------------------------
    logger.info("🟢 Calling GET all customers without filters.")
    customers = customer_helper.list_customers_paginated()

    # Ensure API returned customers
    assert customers, "❌ No customers returned from GET /customers"
    assert isinstance(
        customers, list
    ), f"Expected list of customers, got: {type(customers)}"

    logger.info(f"✅ Retrieved {len(customers)} customers.")

    # Validate structure of each returned customers
    for cust in customers:
        try:
            assert_valid_customer_response(cust)
        except Exception as e:
            pytest.fail(
                f"❌ Customer schema validation failed for ID={cust.get('id')}: {e}"
            )

    logger.info("✅ All returned customers conform to schema.")


@pytest.mark.tcid("TCID-013")
@pytest.mark.regression
@pytest.mark.contract
def test_get_all_customers_pagination_boundary(
    customer_helper, customers_dao, create_valid_customer
):
    """
    Verify pagination behavior for GET /customers using an isolated test dataset (no dependency on global DB state)..

    Validates that:
        - Pagination retrieves multiple pages correctly
        - No duplicate customers appear across pages
        - All returned customers have valid structure

    Test flow:
        1. Creates controlled dataset
        2. Retrieve customers with small page size
        3. Collect results across multiple pages
        4. Ensure no duplicate IDs
        5. Validate structure of each customers
        6. Stops correctly (no infinite loop)
    """
    # You can write a parameterized test to test multiple per_page boundary values (1, 2, 10, etc.)
    per_page = 5
    max_pages = 5  # Safeguard: increase if dataset is large
    qty = 12  # Enough to span multiple pages

    # ------------------------------------------
    # 🔥 Controlled dataset (KEY FIX)
    # ------------------------------------------
    test_run_id = generate_random_string()

    logger.info(
        f"🛠 Creating {qty} customers for pagination test (run_id={test_run_id})"
    )

    for i in range(qty):
        create_valid_customer(email=f"test_{test_run_id}_{i}@supersqa.com")

    logger.info(
        f"🟢 Testing pagination boundary with per_page={per_page}, max_pages={max_pages}"
    )

    # --------------------------------------------------
    # Act
    # --------------------------------------------------
    all_customers = customer_helper.list_customers_for_test(
        test_run_id=test_run_id,
        per_page=per_page,
        max_pages=max_pages,
    )

    # --------------------------------------------------
    # Assert — basic checks
    # --------------------------------------------------
    assert all_customers, "❌ No customers returned from paginated GET /customers"
    assert isinstance(all_customers, list), f"Expected list, got: {type(all_customers)}"

    logger.info(f"✅ Retrieved {len(all_customers)} customers.")

    # --------------------------------------------------
    # Assert — deterministic size
    # --------------------------------------------------
    assert (
        len(all_customers) == qty
    ), f"❌ Expected {qty} customers, got {len(all_customers)}"

    # --------------------------------------------------
    # 🔥 Assert — pagination actually happened
    # --------------------------------------------------
    assert (
        len(all_customers) > per_page
    ), "❌ Pagination did not occur — all data returned in single page"

    # --------------------------------------------------
    # Assert — no duplicates
    # --------------------------------------------------
    ids = [c["id"] for c in all_customers]
    assert len(ids) == len(
        set(ids)
    ), "❌ Duplicate customers found across paginated results"

    logger.info(f"✅ Retrieved {len(all_customers)} unique customers across pages.")

    # --------------------------------------------------
    # Assert — schema validation
    # --------------------------------------------------
    for cust in all_customers:
        try:
            assert_valid_customer_response(cust)
        except Exception as e:
            logger.error(
                f"❌ Schema validation failed for customers ID={cust.get('id')}: {e}"
            )
            logger.debug(f"Offending customers JSON: {cust}")
            pytest.fail(f"❌ Customer schema invalid for ID={cust.get('id')}")

    logger.info("✅ All paginated customers conform to schema.")


@pytest.mark.tcid("TCID-014")
@pytest.mark.regression
def test_get_all_customers_empty_list_with_mock(customer_helper, customers_dao):
    """
    Verify that GET /customers handles an empty dataset.

    This test uses mocking to simulate an empty API response.

    Test flow:
        1. Mock list_customers_paginated to return []
        2. Call the helper method
        3. Ensure the returned list is empty

    Explanation:
    - The test uses patch.object to replace the call_list_all_customers_paginated method only for this test run.
    - The method is mocked to always return an empty list.
    - Then the test asserts the returned list is empty, simulating no customers in DB.
    - You get a fully isolated test that doesn't depend on DB state.
    """

    with patch.object(customer_helper, "list_customers_paginated", return_value=[]):
        logger.info("🟢 Mocking list_customers_paginated to return empty list")
        customers = customer_helper.list_customers_paginated()

        # Ensure mocked response returns empty dataset
        assert (
            customers == []
        ), "❌ Expected empty list from mocked call_list_all_customers_paginated"
        logger.info("✅ Successfully mocked empty customers list")


@pytest.mark.tcid("TCID-015")
@pytest.mark.negative
@pytest.mark.regression
def test_list_customers_created_in_the_future_returns_empty(
    customer_helper, customers_dao
):
    """
    Verify that no customers are returned with a future creation timestamp.

    Endpoint tested:
        GET /customers?created_after=

    Test flow:
        1. Capture current UTC time
        2. Query customers created after that time
        3. Ensure no customers exist beyond the tolerance window

    Note:
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
    """

    # Step 1 — Capture current UTC time

    # Get the current UTC datetime with microseconds stripped (clean second precision)
    now_utc = get_now_utc_floor()
    # Convert the datetime to an ISO 8601 string with 'Z' suffix (e.g., '2025-08-03T12:00:00Z') for API filtering
    created_after = to_iso_utc(now_utc)
    logger.info(f"🔍 Fetching customers created after current time: {created_after}")

    # Step 2 — Query customers created after current time
    filtered_customers = customer_helper.list_customers_paginated(
        created_after=created_after
    )

    logger.info(f"📝 Initial API returned {len(filtered_customers)} customers")

    # Step 3 — Apply tolerance window to avoid timing flakiness
    # Filter out customers that were created within 1 second *after* `now_utc`.
    # - it goes through a list (filtered_customers)
    # - it filters based on a condition
    # - it collects the matching items (cust) into a new list (future_customers)
    tolerance = timedelta(seconds=1)
    future_customers = [
        cust
        for cust in filtered_customers
        if safe_parse_utc_datetime(cust.get("date_created_gmt", ""))
        > (now_utc + tolerance)
    ]

    # Step 4 — Ensure no customers exist beyond tolerance window
    assert not future_customers, (
        f"❌ Found {len(future_customers)} customers(s) created after now (+1s buffer) — "
        f"Possible clock drift or invalid timestamp. Base time: {created_after}"
    )

    logger.info(
        f"✅ No customers found beyond {created_after} (+1s buffer) — test passed"
    )

    # Optional debug logging for unexpected timestamps
    for cust in filtered_customers:
        raw_ts = cust.get("date_created_gmt", "")
        try:
            parsed_ts = safe_parse_utc_datetime(raw_ts)
            logger.debug(
                f"🕵️ Customer ID={cust['id']} | date_created_gmt={raw_ts} | parsed={parsed_ts.isoformat()}"
            )
        except Exception as e:
            logger.warning(
                f"⚠️ Failed to parse timestamp for customers ID={cust.get('id')} | raw_ts={raw_ts} | Error: {e}"
            )
