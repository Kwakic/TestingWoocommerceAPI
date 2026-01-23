import pytest
import logging
from faker import Faker

faker = Faker()
logger = logging.getLogger(__name__)
#  logger.setLevel(logging.DEBUG)  # already set in pytest.ini

pytestmark = [pytest.mark.customers, pytest.mark.smoke, pytest.mark.created_within_window]


@pytest.mark.tcid06
def test_soft_deleted_customer_remains_in_db_but_api_still_returns_them(all_resources,
                                                                        create_valid_customer):
    """
    📌 Test Objective:
        Verify that soft-deleting a customer by setting user_status = 1:
            - ✅ Keeps the customer in the database.
            - 🔎 Does NOT affect WooCommerce REST API visibility — API still returns them.

    💡 Background:
        WooCommerce uses "soft delete_it.py" via status flags (e.g., user_status, post_status='trash').
        However, the core REST API does not automatically exclude such entities unless customized.

    ❗ This is not a bug — it is expected behavior unless your WooCommerce stack explicitly filters soft-deleted users.

    🧪 Test Flow:
        1. Create a new customer via factory fixture.
        2. Use DAO to set user_status = 1 (soft delete_it.py).
        3. Validate that the customer remains in the DB with correct flag.
        4. [Optional]: Document that the API still returns the customer, but do not assert on it.

    """

    customer_helper = all_resources.customer.helper
    dao = all_resources.customer.dao

    # Step 1: Create a new customer via API
    customer = create_valid_customer()
    customer_id = customer["id"]
    customer_email = customer["email"]

    assert customer_id, "❌ Customer ID not returned"
    assert customer_email, "❌ Customer Email not returned"
    logger.info(f"✅ Customer created: ID={customer_id}, Email={customer_email}")

    customer_helper.validate_customer_response_schema(customer=customer)

    # Step 2: Soft-delete_it.py in DB via DAO
    rows_updated = dao.soft_delete_customer_by_id(customer_id)
    assert rows_updated == 1, f"❌ Expected 1 row updated, got {rows_updated}"
    logger.info(f"🟡 Soft-deleted customer ID={customer_id} by setting user_status=1")

    # Step 3: Confirm DB reflects soft deletion
    updated_customer = dao.get_customer_by_id(customer_id)
    assert updated_customer is not None, "❌ Customer not found in DB after soft-delete_it.py"
    assert str(updated_customer["user_status"]) == "1", f"❌ Expected user_status=1, got {updated_customer['user_status']}"
    logger.info("✅ DB confirms soft-deleted customer with user_status=1")

    # Step 4: Document API behavior (do not assert)
    logger.warning(
        f"🔍 Note: WooCommerce REST API does NOT filter users with user_status=1. "
        f"Customer with email={customer_email} will still be returned unless backend customization is added."
    )
    # You could log this or check it manually if desired:
    customers = customer_helper.call_list_all_customers_paginated(email=customer_email)
    logger.info(f"API returned customer(s): {customers}")

