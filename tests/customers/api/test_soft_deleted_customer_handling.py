import pytest
import logging
from faker import Faker

from EcommerceAPI.src.utilities.filtering_utils import filter_out_soft_deleted

faker = Faker()
logger = logging.getLogger(__name__)
#  logger.setLevel(logging.DEBUG)  # already set in pytest.ini

pytestmark = [pytest.mark.customers, pytest.mark.smoke, pytest.mark.created_within_window]


@pytest.mark.tcid06
def test_soft_deleted_customer_is_still_returned_by_api(customer_helper, customers_dao, all_resources,
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
        3. Validate that the customer remains in the DB with a correct flag.
        4. [Optional]: Document that the API still returns the customer, but do not assert on it.

    """

    # Step 1: Create customer using factory fixture
    logger.info("🛠 Creating a test customer via factory fixture.")
    # To keep the customer in the DB (i.e., skip deletion), set: customer = create_customer_for_test(skip_cleanup=True)
    customer = create_valid_customer()  # Default: skip_cleanup=False, validate_response=True
    # No need to assert ID/email. The fixture already does it: customer_helper.assert_valid_customer_response(customer)

    customer_id = customer["id"]
    customer_email = customer["email"]

    # Step 2: Soft-delete_it.py in DB via DAO
    rows_updated = customers_dao.soft_delete_customer_by_id(customer_id)
    assert rows_updated == 1, f"❌ Expected 1 row updated, got {rows_updated}"
    logger.info(f"🟡 Soft-deleted customer ID={customer_id} by setting user_status=1")

    # Step 3: Confirm DB reflects soft deletion
    updated_customer = customers_dao.get_customer_by_id(customer_id)
    assert updated_customer is not None, "❌ Customer not found in DB after soft-delete_it.py"
    assert str(updated_customer["user_status"]) == "1", (f"❌ Expected user_status=1, "
                                                         f"got {updated_customer['user_status']}")
    logger.info("✅ DB confirms soft-deleted customer with user_status=1")

    # Step 4: Document API behavior (do not assert)
    logger.warning(
        f"🔍 Note: WooCommerce REST API does NOT filter users with user_status=1. "
        f"Customer with email={customer_email} will still be returned unless backend customization is added."
    )
    # You could log this or check it manually if desired:
    customers = customer_helper.call_list_all_customers_paginated(email=customer_email)
    logger.info(f"API returned customer(s): {customers}")


@pytest.mark.tcid30
def test_soft_deleted_customers_are_excluded_by_custom_filter(
    customer_helper,
    customers_dao,
    create_valid_customer
):
    """
    🎯 Verify that soft-deleted customers are excluded by custom filtering logic. Soft-deleted entities should be
    excluded.
    The filtering says:
        "If the DB says this customer is soft-deleted → remove it from the API response."

    WooCommerce's behavior:
    - Soft-deleted customers (user_status=1) are STILL returned by API.

    Our framework behavior:
    - We explicitly filter them out.

    Steps:
    1. Create customer
    2. Soft-delete via DB (user_status = 1)
    3. Fetch customers via API
    4. Apply custom filtering
    5. Assert customer is excluded
    """

    # -------------------------------------------
    # 🛠️ Step 1: Create customer
    # -------------------------------------------
    logger.info("🛠 Creating a test customer via factory fixture.")
    # To keep the customer in the DB (i.e., skip deletion), set: customer = create_customer_for_test(skip_cleanup=True)
    customer = create_valid_customer()  # Default: skip_cleanup=False, validate_response=True
    # No need to assert ID/email. The fixture already does it: customer_helper.assert_valid_customer_response(customer)

    customer_id = customer["id"]
    email = customer["email"]

    # -------------------------------------------
    # 🟡 Step 2: Soft delete in DB
    # -------------------------------------------
    rows_updated = customers_dao.soft_delete_customer_by_id(customer_id)
    assert rows_updated == 1, f"❌ Expected 1 row updated, got {rows_updated}"

    db_customer = customers_dao.get_customer_by_email(email)
    assert db_customer is not None
    assert str(db_customer["user_status"]) == "1"

    # -------------------------------------------
    # 🔍 Step 3: Fetch RAW API data (Woo behavior)
    # -------------------------------------------
    raw_customers = customer_helper.call_list_all_customers_paginated(email=email)
    assert raw_customers, "❌ API did not return any customers"

    raw_ids = [c["id"] for c in raw_customers]
    # Equivalent for loop version:
    # raw_ids = []
    # for c in raw_customers:
    #     raw_ids.append(c["id"])

    assert customer_id in raw_ids, (
        "❌ Soft-deleted customer should STILL appear in raw API response (Woo behavior)"
    )

    # -------------------------------------------
    # 🧠 Step 4: Apply custom filtering (UTILITY)
    # -------------------------------------------
    filtered_customers = filter_out_soft_deleted(
        items=raw_customers,
        get_db_record_fn=customers_dao.get_customer_by_email,
        id_field="email",
        deleted_flag="user_status",
        deleted_value=1
    )

    filtered_ids = [c["id"] for c in filtered_customers]

    # -------------------------------------------
    # ✅ Step 5: Assert exclusion
    # -------------------------------------------
    assert customer_id not in filtered_ids, (
        "❌ Soft-deleted customer was NOT filtered out by custom logic"
    )
