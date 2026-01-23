import pytest
import logging

from jsonschema import validate

from tests.customers.schemas.customer import error_schema
logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.customers, pytest.mark.regression]


INVALID_UPDATE_PAYLOADS = [
    pytest.param(
        {"email": "not-an-email"},
        400,
        id="invalid-email-no-at"
    ),
    pytest.param(
        {"email": "dty@not-an-email"},
        400,
        id="invalid-email-no-at"
    ),
    pytest.param(
        {"email": "@missing-local.com"},
        400,
        id="invalid-email-missing-local-part"
    ),
    pytest.param(
        {"email": "DUPLICATE_EMAIL"},
        400,
        id="duplicate-email"
    ),
]


@pytest.mark.tcid12
def test_update_customer_first_name(all_resources, create_valid_customer, request_utility):
    """
    ✅ Test Case: Update a customer's first name and email, validate update via API and DB.
    🧪 Schema validation included.
    🎯 Ensures update works and data is consistent.
    """

    # Use the dynamic entity registry (all_resources.entities) to access helpers/DAOs
    helper = all_resources.entities["customers"].helper
    dao = all_resources.entities["customers"].dao

    # -------------------------------
    #  ✅ Create customer via fixture factory
    # -------------------------------
    logger.info("🛠 Creating a test customer for updating name and email.")
    # To keep the customer in the DB (i.e., skip deletion), pass: customer = create_customer_for_test(skip_cleanup=True)
    customer = create_valid_customer()
    customer_id = customer["id"]
    original_email = customer["email"]

    # Early assert for id and email ensures immediate failure if response is malformed.
    assert customer_id is not None, "❌ Customer ID not returned"
    assert original_email is not None, "❌ Customer Email not returned"
    logger.info(f"✅ Assertion passed: Customer created: ID={customer_id}, Email={original_email}")

    # Define update payload
    updated_first_name = "QAUpdated"
    updated_email = "mart_hanz@golp.com"

    logger.info(f"🔁 Updating customer ID={customer_id} with first_name='{updated_first_name}' "
                f"and email='{updated_email}'")

    # Use the helper's injected request_utility (singular) to perform raw update call
    update_response = request_utility.put(
        f"customers/{customer_id}",
        payload={"first_name": updated_first_name, "email": updated_email},
        expected_status_code=200
    )

    assert update_response["first_name"] == updated_first_name, (
        f"❌ First name update failed. Expected: '{updated_first_name}', Got: '{update_response.get('first_name')}'"
    )
    assert update_response["email"] == updated_email, (
        f"❌ Email update failed. Expected: '{updated_email}', Got: '{update_response.get('email')}'"
    )
    logger.info(f"✅ Assertion passed: First name has been updated to: {updated_first_name}, "
                f"and email to: {updated_email}")

    # ------------------------------------------------------------------
    # 📋 Schema Validation (validate the updated resource returned by update)
    # ------------------------------------------------------------------
    helper.validate_customer_response_schema(customer=update_response)

    # ---------------------------------------------------------------------------------------------------------
    # 🔍 Confirm customer exists in DB and API GET response matches DB.
    # 🧩 Schema Validation (it checks that the GET response is valid).
    # ---------------------------------------------------------------------------------------------------------
    helper.validate_customer_exists_and_matches(email=updated_email, dao=dao)
    logger.info(f"🎯 Full validation complete for customer ID={customer_id}")


@pytest.mark.negative_test
@pytest.mark.tcid21
@pytest.mark.parametrize("update_payload, expected_status", INVALID_UPDATE_PAYLOADS)
def test_update_customer_invalid_inputs(all_resources, create_valid_customer, update_payload,
                                        expected_status, request_utility):
    """
    ❌ Negative Test: Attempt to update an existing customer with invalid input.

    This test validates:
    - Handling of malformed or unacceptable update payloads.
    - API returns the correct error structure (via `error_schema`).
    - Database consistency (i.e., no changes are made after failure).

    It will create 4 customers:
        1. (not-an-email)
        2. (@missing-local.com)
        3. (main subject for DUPLICATE_EMAIL)
        4. (provides the email to simulate duplication)

    Args:
        all_resources: Object providing access to helpers and DAOs.
        create_valid_customer: Fixture to create a test customer.
        update_payload (dict): The invalid payload used in update request.
        expected_status (int): Expected HTTP response code.
        request_utility : ..................
    """

    helper = all_resources.entities["customers"].helper
    dao = all_resources.entities["customers"].dao

    # -------------------------------------------
    # 🧪 Set up two customers: one to update, one as duplicate
    # -------------------------------------------
    logger.info("🛠 Creating a test customer via factory fixture.")
    original_customer = create_valid_customer()
    customer_id = original_customer["id"]
    original_email = original_customer["email"]
    assert customer_id, "❌ Failed to create test customer - no ID"
    assert original_email, "❌ Test customer has no email"

    # 🔁 Inject real duplicate email if test case requires it
    if update_payload.get("email") == "DUPLICATE_EMAIL":
        duplicate_customer = create_valid_customer()
        update_payload["email"] = duplicate_customer["email"]
        logger.info(f"🔁 Using duplicate email: {update_payload['email']}")

    logger.info(f"🚫 Attempting to update customer ID={customer_id} with payload: {update_payload}")

    # ---------------------------------------------------
    # 📞 Attempt to update customer (expecting failure)
    # ---------------------------------------------------
    # Use the shared request_utility fixture for the raw call; pass expected_status so the client returns/parses the
    # error payload.

    response = request_utility.put(
        f"customers/{customer_id}",
        payload=update_payload,
        expected_status_code=expected_status
    )

    # Now assert the error structure
    assert isinstance(response, dict), f"❌ Expected error response as dict, got: {type(response)}"
    assert response["code"], f"❌ Missing 'code' in response: {response}"
    assert response["message"], f"❌ Missing 'message' in response: {response}"
    validate(instance=response, schema=error_schema)

    # -------------------------------------------
    # 🔒 Confirm that customer data in DB remains unchanged
    # -------------------------------------------
    # It is highly recommended when the API call could potentially mutate data if not properly guarded — like in
    # update, delete_it.py, or PATCH partial operations.
    # You're attempting to mutate existing data (via PUT). There's risk of a partial update or bug in backend
    # validation logic. Verifying that nothing changed is part of what makes it a strong regression test.
    # ✅ Best practice: Keep the DB check here. It's essential.
    db_customer = dao.get_customer_by_email(email=original_email)
    assert db_customer is not None, "❌ Original customer no longer in DB after failed update"
    assert db_customer["ID"] == customer_id, "❌ Customer ID mismatch"
    assert db_customer["user_email"] == original_email, "❌ Email was changed after failed update"
    logger.info("✅ Original customer record remains unchanged after failed update.")
