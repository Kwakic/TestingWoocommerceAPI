import pytest
import logging
from jsonschema import validate
from dateutil.parser import isoparse  # For robust ISO date parsing

from EcommerceAPI.src.utilities.date_timestamp_utils import get_customers_in_window

from tests.shared.schemas.customer import customer_schema

# from EcommerceAPI.src.utilities.raw_requests import RawAPIClient

logger = logging.getLogger(__name__)
#  logger.setLevel(logging.DEBUG)  # already set in pytest.ini


pytestmark = [pytest.mark.customers, pytest.mark.smoke]


@pytest.mark.tcid05
def test_customer_deletion_removes_resource(all_resources, customer_helper, customers_dao, create_valid_customer):
    """
    🎯 Test to validate end-to-end customer deletion:
    - Customer is created successfully.
    - Can be deleted via API with correct status and ID.
    - Cannot be retrieved after deletion (404 expected).
    - Is no longer present in the database.
    - Deletion is tracked to avoid double cleanup.

    Args:
        all_resources: mark_deleted (skip cleanup for this resource)
        customer_helper: Provides customer's helper
        customers_dao: Provides customer's DAOs
        create_valid_customer (Callable): Factory fixture to create test customer.

    The test follows this lifecycle
    CREATE → DELETE → VERIFY (API) → VERIFY (DB) → CLEANUP (fixture)

    The tricky part is: 👉 How do we avoid deleting the same resource twice?
    That’s where this comes in: mark_deleted("customers", customer_id)

    The framework has automatic cleanup at the end of the test, but:
    👉 In THIS test, you already deleted the customer manually. So you must tell the framework:
        “⚠️ Don’t delete this again later”
    """

    # -------------------------------------------
    # 🔧 Access helpers
    # -------------------------------------------
    # Prevent double deletion during teardown.
    # Skip cleanup for this resource
    mark_deleted = all_resources.mark_deleted

    # -------------------------------------------
    # 🛠️ Step 1: Create test customer via fixture
    # -------------------------------------------
    logger.info("🛠 Creating a test customer via factory fixture for deletion.")
    # To keep the customer in the DB (i.e., skip deletion), pass: customer = create_customer_for_test(skip_cleanup=True)
    customer = create_valid_customer()  # Default: skip_cleanup=False, validate_response=True
    # No need to assert ID/email. The fixture already does it: customer_helper.assert_valid_customer_response(customer)

    customer_id = customer["id"]
    email = customer["email"]

    # -------------------------------
    #  🗑️ Step 2:  Delete customer and validate deletion response
    # -------------------------------
    logger.info(f"🧹 Deleting customer ID={customer_id}")
    delete_response = customer_helper.call_delete_customer(
        customer_id=customer_id,
        expected_status_code=200
    )

    assert delete_response["id"] == customer_id, (
        f"❌ Mismatched delete_it.py ID: expected {customer_id}, got {delete_response.get('id')}"
    )
    logger.info(f"✅ Deletion response confirmed for ID={customer_id}")

    # 🧼 Mark resource deleted to prevent re-cleanup. Avoid double-deletion by flagging this customer as already removed
    mark_deleted("customers", customer_id)

    # -------------------------------------------
    # 🔍 Step 3: Verify customer is no longer accessible via API
    # -------------------------------------------
    logger.info(f"🔎 Verifying GET after deletion returns 404 for ID={customer_id}")
    response = customer_helper.call_get_customer_by_id(customer_id=customer_id, expected_status_code=404)
    # Validating deleted customer's error message"
    assert response['code'] == "woocommerce_rest_invalid_id", (f"Invalid Error code. Current: '{response['code']}', "
                                                               f"Expected: 'woocommerce_rest_invalid_id'")
    assert response['message'] == "Invalid resource ID.", (f"Invalid Error message. Current: '{response['message']}', "
                                                           f"Expected: 'Invalid resource ID'")
    assert response['data'] == {'status': 404}, (f"Invalid data. Current: {response['data']}, "
                                                 f"Expected: {{'status': 404}}")
    # Optional): Extract the post-deletion response validation into a reusable utility method:
    # def assert_customer_deleted_response(response):
    #     assert response['code'] == "woocommerce_rest_invalid_id"
    #     assert response['message'] == "Invalid resource ID."
    #     assert response['data'] == {'status': 404}
    # Then reuse across deletion-related tests.
    logger.info(f"✅ Assertion passed: API confirms customer ID={customer_id} is deleted")

    # -------------------------------------------
    # 🧠 Step 4: DB Validation: Ensure deletion from database
    # -------------------------------------------
    logger.info(f"🗃️ Validating DB deletion for email={email}")
    db_customer = customers_dao.get_customer_by_email(email)
    assert not db_customer, f"❌ Customer still exists in DB for email={email}"
    logger.info(f"✅ Assertion passed: DB confirms customer deletion for ID={customer_id}")


@pytest.mark.negative_test
@pytest.mark.tcid18
@pytest.mark.parametrize("minute_offset", [1, 2])
def test_deleted_customer_not_in_created_after_filter(customer_helper, customers_dao, all_resources,
                                                      create_valid_customer, minute_offset: int):
    """
    ❌ End-to-end negative test that verifies deleted customers do not appear in filtered GET /customers results.

    This test ensures that once a customer is deleted, they are no longer returned by the /customers API,
    even if queried using a valid timestamp window that includes their original creation time.

    **Steps:**
    1. ✅ Create a customer via POST (using test fixture).
    2. ✅ Extract and parse server-provided `date_created_gmt` timestamp.
    3. ✅ Delete the customer explicitly via DELETE.
    4. ✅ Construct `created_after` and `created_before` filter window around the original creation time.
    5. ✅ Call GET /customers with time filters.
    6. ✅ Assert that the deleted customer is NOT included in the API response.
    7. ✅ Validate schema for all remaining returned customers.

    **Why use server-side timestamp for filtering?**
    - Ensures the deleted customer technically *should* fall within the filter range.
    - Confirms that deletion logic is respected by the filtering mechanism.

    **Why this test matters: **
    - Guarantees soft-deleted or fully removed records are not exposed in public/customer-facing APIs.
    - Prevents stale, deleted, or logically orphaned data from leaking into clients, dashboards, or integrations.
    - Strengthens data integrity and trust in time-based filters.

    Parameterized with different minute offsets to test consistency across varied filtering windows.
    """

    # -------------------------------------------
    # ✅ Create customer via fixture factory
    # -------------------------------------------
    logger.info("🛠 Creating a test customer via factory fixture.")
    customer = create_valid_customer(skip_cleanup=True)
    # When to Use skip_cleanup=True.You only need it when: You're not calling mark_deleted(...), and You're
    # manually deleting the customer inside your test, and you want to completely bypass automatic cleanup, usually for
    # full lifecycle testing or deletion-negative cases (e.g., test customer already missing or deletion fails).
    customer_id = customer["id"]

    # -------------------------------------------
    # 📅 Parse server-provided creation timestamp
    # -------------------------------------------
    created_at_str = customer.get("date_created_gmt")
    assert created_at_str, "❌ 'date_created_gmt' missing in response"
    created_at = isoparse(created_at_str)

    # -------------------------------------------
    # 🗑️ Delete customer before filtering
    # -------------------------------------------
    logger.info(f"🧹 Deleting customer ID={customer_id}")
    customer_helper.call_delete_customer(customer_id)

    # -------------------------------------------
    # 📞 Call GET /customers with date filters
    # -------------------------------------------

    # Use the utility with logging now included inside it.⏳ Parse server timestamps the exact creation time from
    # the customer response (in GMT) using ISO parser to avoid datetime bugs.
    filtered_customers = get_customers_in_window(
        helper=customer_helper,
        created_at=created_at,
        before_min=minute_offset,
        after_min=1,
        negative=False  # This means the deleted customer *should* have shown up if not deleted.
    )

    # 🔍 Extract IDs from response
    returned_ids = [c["id"] for c in filtered_customers]

    # -------------------------------------------
    # ❌ Assert deleted customer does NOT appear
    # -------------------------------------------
    assert customer_id not in returned_ids, (
        f"❌ Deleted customer ID {customer_id} was incorrectly included in filtered results"
    )
    logger.info(f"✅ Deleted customer ID {customer_id} correctly excluded from filtered API list")

    # 📋 Schema validation for remaining customers
    for cust in filtered_customers:
        validate(instance=cust, schema=customer_schema)
    logger.info("📦 All customers in filtered list passed schema validation")

    # 🔐 Why This Matters
    # Ensures GET /customers doesn’t return deleted entries
    # Prevents stale or logical removed data from leaking into client apps



