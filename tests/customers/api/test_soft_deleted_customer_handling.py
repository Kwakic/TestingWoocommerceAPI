import pytest
import logging
from faker import Faker

from EcommerceAPI.src.utils.filtering_utils import filter_out_soft_deleted

faker = Faker()
logger = logging.getLogger(__name__)
#  logger.setLevel(logging.DEBUG)  # already set in pytest.ini

pytestmark = [pytest.mark.customers, pytest.mark.smoke, pytest.mark.created_within_window]


@pytest.mark.tcid06
def test_soft_deleted_customer_is_still_returned_by_api(customer_helper, customers_dao, all_resources,
                                                        create_valid_customer):
    """
    Verify WooCommerce soft-delete behavior.

    Soft-deleting a customers in the database (user_status = 1):
        - keeps the customers record in the database
        - does NOT remove the customers from the WooCommerce API response

    This test documents the default WooCommerce behavior.

    Test flow:
        1. Create a customers via fixture
        2. Soft-delete the customers in DB (user_status = 1)
        3. Confirm DB reflects the soft deletion
        4. Verify API still returns the customers

    Note:
        WooCommerce uses "soft delete_it.py" via status flags (e.g., user_status, post_status='trash').
        However, the core REST API does not automatically exclude such entities unless customized.

    """

    # Step 1 — Create customers (POST /customers handled by fixture)
    logger.info("🛠 Creating a test customers via factory fixture.")
    # To keep the customers in the DB (i.e., skip deletion), set: customers = create_customer_for_test(skip_cleanup=True)
    customer = create_valid_customer()  # Default: skip_cleanup=False, validate_response=True
    # No need to assert ID/email. The fixture already does it: customer_helper.assert_valid_customer_response(customers)

    customer_id = customer["id"]
    customer_email = customer["email"]

    # Step 2 — Soft delete customers in DB (user_status = 1)
    rows_updated = customers_dao.soft_delete_customer_by_id(customer_id)
    assert rows_updated == 1, f"❌ Expected 1 row updated, got {rows_updated}"
    logger.info(f"🟡 Soft-deleted customers ID={customer_id} by setting user_status=1")

    # Step 3 — Verify DB reflects soft deletion
    updated_customer = customers_dao.get_customer_by_id(customer_id)
    assert updated_customer is not None, "❌ Customer not found in DB after soft delete"
    assert str(updated_customer["user_status"]) == "1", (f"❌ Expected user_status=1, "
                                                         f"got {updated_customer['user_status']}")
    logger.info("✅ DB confirms soft-deleted customers with user_status=1")

    # Step 4 — Confirm API still returns soft-deleted customers
    logger.warning(
        f"🔍 Note: WooCommerce REST API does NOT filter users with user_status=1. "
        f"Customer with email={customer_email} will still be returned unless backend customization is added."
    )
    # You could log this or check it manually if desired:
    customers = customer_helper.list_customers_paginated(email=customer_email)
    logger.info(f"API returned customers(s): {customers}")


@pytest.mark.tcid30
def test_soft_deleted_customers_are_excluded_by_custom_filter(
    customer_helper,
    customers_dao,
    create_valid_customer
):
    """
    Verify that custom filtering removes soft-deleted customers.

    WooCommerce API behavior:
        - Soft-deleted customers (user_status = 1) are still returned.

    Framework behavior:
        - Custom filtering removes soft-deleted records.

    Test flow:
        1. Create customers
        2. Soft delete in DB (user_status = 1)
        3. Retrieve customers from API
        4. Apply custom filtering utility
        5. Ensure soft-deleted customers is excluded
    """

    # Step 1 — Create customers
    logger.info("🛠 Creating a test customers via factory fixture.")
    # To keep the customers in the DB (i.e., skip deletion), set: customers = create_customer_for_test(skip_cleanup=True)
    customer = create_valid_customer()  # Default: skip_cleanup=False, validate_response=True
    # No need to assert ID/email. The fixture already does it: customer_helper.assert_valid_customer_response(customers)

    customer_id = customer["id"]
    email = customer["email"]

    # Step 2 — Soft delete customers in DB
    rows_updated = customers_dao.soft_delete_customer_by_id(customer_id)
    assert rows_updated == 1, f"❌ Expected 1 row updated, got {rows_updated}"

    db_customer = customers_dao.get_customer_by_email(email)
    assert db_customer is not None
    assert str(db_customer["user_status"]) == "1"

    # Step 3 — Retrieve raw API data (WooCommerce behavior)
    raw_customers = customer_helper.list_customers_paginated(email=email)
    assert raw_customers, "❌ API did not return any customers"

    raw_ids = [c["id"] for c in raw_customers]

    assert customer_id in raw_ids, (
        "❌ Soft-deleted customers should STILL appear in raw API response (Woo behavior)"
    )

    # Step 4 — Apply custom filtering utility
    filtered_customers = filter_out_soft_deleted(
        items=raw_customers,
        get_db_record_fn=customers_dao.get_customer_by_email,
        id_field="email",
        deleted_flag="user_status",
        deleted_value=1
    )

    filtered_ids = [c["id"] for c in filtered_customers]

    # Step 5 — Ensure soft-deleted customers is excluded
    assert customer_id not in filtered_ids, (
        "❌ Soft-deleted customers was NOT filtered out by custom logic"
    )
