import pytest
import logging
from dateutil.parser import isoparse  # For robust ISO date parsing

from EcommerceAPI.src.utils.date_timestamp_utils import get_customers_in_window
from EcommerceAPI.src.customers.validators.customer_validators import (
    assert_customer_not_found_error,
    assert_valid_customer_response,
)

logger = logging.getLogger(__name__)
#  logger.setLevel(logging.DEBUG)  # already set in pytest.ini


pytestmark = [pytest.mark.integration]


@pytest.mark.tcid05
@pytest.mark.e2e  # lightweight E2E
@pytest.mark.regression
def test_customer_deletion_removes_resource(
    all_resources, customer_helper, customers_dao, create_valid_customer
):
    """
    Verify that deleting a customers removes the resource completely.

    Endpoint tested:
        DELETE /customers/{id}

    Test flow:
        1. Create a customers
        2. Delete the customers
        3. Verify API no longer returns the customers (404)
        4. Verify the customers record is removed from the database

    Args:
        all_resources: mark_deleted (skip cleanup for this resource)
        customer_helper: Provides customers's helper
        customers_dao: Provides customers's DAOs
        create_valid_customer (Callable): Factory fixture to create test customers.

    The framework has automatic cleanup at the end of the test, but:
    In THIS test, you already deleted the customers manually. So you must tell the framework:
        “Don’t delete this again later” by setting: mark_deleted("customers", customer_id)
    """

    # Prevent double deletion during test teardown
    mark_deleted = all_resources.mark_deleted

    # Step 1 — Create customers
    logger.info("🛠 Creating a test customers via factory fixture for deletion.")
    # To keep the customers in the DB (i.e., skip deletion), pass: customers = create_customer_for_test(skip_cleanup=True)
    customer = (
        create_valid_customer()
    )  # Default: skip_cleanup=False, validate_response=True

    customer_id = customer["id"]
    email = customer["email"]

    # Step 2 — Delete customers
    logger.info(f"🧹 Deleting customers ID={customer_id}")

    # By setting flag "return_http_response=True" it returns HttpResponse necessary to validate status_code, headers...
    delete_response = customer_helper.delete_customer(
        customer_id, return_http_response=True
    )

    # Validate HTTP response
    assert delete_response.status_code == 200

    # # Extract response body
    delete_data = delete_response.json

    assert (
        delete_data["id"] == customer_id
    ), f" ❌ Mismatched delete_it.py ID: expected {customer_id}, got {delete_data.get('id')}"
    logger.info(f"✅ Deletion response confirmed for ID={customer_id}")

    # Mark resource as deleted to prevent teardown from deleting it again
    mark_deleted("customers", customer_id)

    # Step 3 — Verify API returns 404 after deletion
    logger.info(f"🔎 Verifying GET after deletion returns 404 for ID={customer_id}")
    response = customer_helper.get_customer_by_id(customer_id=customer_id)
    # Validating deleted customers's error message"

    assert_customer_not_found_error(
        response
    )  # It validates: data: status 404, code, error message

    # Then reuse across deletion-related tests.
    logger.info(
        f"✅ Assertion passed: API confirms customers ID={customer_id} is deleted"
    )

    # Step 4 — Verify customers is removed from database
    logger.info(f"🗃️ Validating DB deletion for email={email}")
    db_customer = customers_dao.get_customer_by_email(email)
    assert not db_customer, f"❌ Customer still exists in DB for email={email}"
    logger.info(
        f"✅ Assertion passed: DB confirms customers deletion for ID={customer_id}"
    )


@pytest.mark.tcid18
@pytest.mark.negative
@pytest.mark.contract
@pytest.mark.regression
@pytest.mark.parametrize("minute_offset", [1, 2])
def test_deleted_customer_not_in_created_after_filter(
    customer_helper,
    customers_dao,
    all_resources,
    create_valid_customer,
    minute_offset: int,
):
    """
    Verify that a deleted customers does not appear in filtered
    GET /customers results.

    Endpoint tested:
        GET /customers?created_after=&created_before=

    Test flow:
        1. Create a customers
        2. Delete the customers
        3. Query customers using a time window that includes the creation time
        4. Ensure the deleted customers is NOT returned

    Parameterized with different minute offsets to test consistency across varied filtering windows.

            TIME WINDOW
        ┌─────────────────┐
        │                 │
       09:59   10:00   10:02
                ↑
           customers created
    """

    # Step 1 — Create customers
    logger.info("🛠 Creating a test customers via factory fixture.")
    customer = create_valid_customer(skip_cleanup=True)
    # skip_cleanup=True because the test deletes the resource manually
    customer_id = customer["id"]

    # Step 2 — Parse server creation timestamp
    created_at_str = customer.get("date_created_gmt")
    assert created_at_str, "❌ 'date_created_gmt' missing in response"
    created_at = isoparse(created_at_str)

    # Step 3 — Delete customers
    logger.info(f"🧹 Deleting customers ID={customer_id}")
    # By setting flag "return_http_response=True" it returns HttpResponse necessary to validate status_code, headers...
    delete_response = customer_helper.delete_customer(
        customer_id, return_http_response=True
    )

    # Transport validation (FAIL FAST) Status validated BEFORE JSON
    assert delete_response.status_code == 200

    # Extract JSON to validate body
    delete_data = delete_response.json

    assert (
        delete_data["id"] == customer_id
    ), f" ❌ Mismatched delete_it.py ID: expected {customer_id}, got {delete_data.get('id')}"

    # Step 4 — Query customers within creation window
    # Use the utility with logging now included inside it.⏳ Parse server timestamps the exact creation time from
    # the customers response (in GMT) using ISO parser to avoid datetime bugs.
    filtered_customers = get_customers_in_window(
        helper=customer_helper,
        created_at=created_at,
        before_min=minute_offset,
        after_min=1,
        negative=False,  # This means the deleted customers *should* have shown up if not deleted.
    )

    # Extract returned customers IDs
    returned_ids = [c["id"] for c in filtered_customers]

    # Step 5 — Ensure deleted customers is excluded
    assert (
        customer_id not in returned_ids
    ), f"❌ Deleted customers ID {customer_id} was incorrectly included in filtered results"

    logger.info(
        "✅ Deleted customers ID %s correctly excluded from filtered API list",
        customer_id,
    )

    # Step 6 — Validate structure of remaining customers
    for cust in filtered_customers:
        assert_valid_customer_response(cust)

    logger.info("📦 All customers in filtered list passed structure validation")
