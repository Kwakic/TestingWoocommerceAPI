import pytest
import logging
from dateutil.parser import isoparse  # For robust ISO date parsing

from EcommerceAPI.src.customers.validators.customer_validators import (
    assert_valid_customer_response,
    assert_single_customer_by_email,
    assert_customer_identity
)
from EcommerceAPI.src.utils.date_timestamp_utils import get_customers_in_window

logger = logging.getLogger(__name__)
#  logger.setLevel(logging.DEBUG)  # already set in pytest.ini

# Apply shared markers for the test module
pytestmark = [pytest.mark.customers, pytest.mark.integration, pytest.mark.regression]


@pytest.mark.tcid07
@pytest.mark.parametrize("minute_offset", [1, 5])
def test_list_customers_created_within_time_range_with_db_check(customer_helper, customers_dao, minute_offset: int,
                                                                create_valid_customer):
    """
    Verify that a customers appears in results when filtering by a time
    window that includes the creation timestamp.

    Endpoint tested:
        GET /customers?created_after=&created_before=

    Fixture responsibilities (`create_valid_customer`):
        - POST /customers
        - response validation (Pydantic)
        - automatic cleanup registration

    Test flow:
        1. Create a customers
        2. Build a time window around the server creation timestamp
        3. Retrieve customers using time filters
        4. Ensure the created customers appears in the results
        5. Validate returned customers
        6. Verify API data matches database
    """

    # Step 1 — Create customers (fixture performs POST validation)
    logger.info("🛠 Creating a test customers via factory fixture.")
    # To keep the customers in the DB (i.e., skip deletion),set: customers = create_customer_for_test(skip_cleanup=True)
    customer = create_valid_customer()  # Default: skip_cleanup=False, validate_response=True

    customer_id = customer["id"]
    customer_email = customer["email"]

    # Step 2 — Build time filter using server timestamp
    created_at_str = customer.get("date_created_gmt")
    assert created_at_str, "❌ 'date_created_gmt' missing in response"
    created_at = isoparse(created_at_str)  # converted version is: datetime.datetime(2025, 7, 2, 19, 48, 33)

    # Step 3 — Retrieve customers within the time window
    filtered_customers = get_customers_in_window(
        helper=customer_helper,
        created_at=created_at,
        before_min=minute_offset,
        after_min=1,
        negative=False
    )

    # Ensure the API returned results
    assert filtered_customers, "❌ No customers returned from GET /customers with date filters"
    logger.info(f"✅ Assertion passed: Customers returned from filtered GET: count={len(filtered_customers)}")

    # Step 4 — Extract the expected customers from dataset
    customer_model = assert_single_customer_by_email(
        filtered_customers,
        customer_email
    )

    # Step 5 — Validate customers identity
    assert_customer_identity(
        customer_model,
        customer_id,
        customer_email
    )

    logger.info(
        "✅ Customer found in filtered results: ID=%s Email=%s",
        customer_id,
        customer_email
    )

    # Step 6 — Validate structure of returned customers
    for cust in filtered_customers:
        assert_valid_customer_response(cust)
    logger.info("📦 All customers in filtered list passed schema validation")

    # Step 7 — Verify API data matches database
    customer_helper.assert_customer_exists_and_matches_db(customer_email, customers_dao)

    logger.info("🎯 Full validation complete for customers ID: %r", customer_id)


@pytest.mark.tcid08
@pytest.mark.negative
def test_customer_should_not_returned_when_filtered_outside_creation_time(customer_helper, customers_dao,
                                                                          create_valid_customer):
    """
    Verify that a customers is NOT returned when filtering outside
    the creation timestamp window.

    Endpoint tested:
        GET /customers?created_after=&created_before=

    Test flow:
        1. Create a customers
        2. Build a time window outside the creation timestamp
        3. Query customers using the filter
        4. Ensure the created customers is NOT returned
    """

    # Step 1 — Create customers
    logger.info("🛠 Creating a test customers via factory fixture.")
    # To keep the customers in the DB (i.e., skip deletion),set: customers = create_customer_for_test(skip_cleanup=True)
    customer = create_valid_customer()  # Default: skip_cleanup=False, validate_response=True

    customer_id = customer["id"]

    created_at_str = customer.get("date_created_gmt")
    assert created_at_str, "❌ 'date_created_gmt' missing in response"
    created_at = isoparse(created_at_str)  # converted version is: datetime.datetime(2025, 7, 2, 19, 48, 33)

    # Step 2 — Retrieve customers outside creation window
    # Note: Use the utility with logging now included inside it. ⏳ Parse server timestamps the exact creation time from
    # the customers response (in GMT) using ISO parser to avoid datetime bugs.
    filtered_customers = get_customers_in_window(
        helper=customer_helper,
        created_at=created_at,
        before_min=1,
        after_min=1,
        negative=True
    )

    returned_ids = [c["id"] for c in filtered_customers]

    # Step 3 — Ensure customers is excluded from results
    assert customer_id not in returned_ids, (
        f"❌ Customer ID {customer_id} was incorrectly included in results filtered outside its creation time"
    )

    logger.info(f"✅ Customer ID {customer_id} correctly excluded from filtered API list")
