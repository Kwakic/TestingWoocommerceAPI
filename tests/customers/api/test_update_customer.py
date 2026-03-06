import pytest
import logging

from jsonschema import validate

from EcommerceAPI.src.customers.validators.customer_validators import (assert_customer_identity,
                                                                       assert_valid_customer_response)
from tests.shared.schemas.customer import error_schema

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.customers, pytest.mark.regression]

INVALID_UPDATE_PAYLOADS = [
    {
        "name": "invalid-email-no-at",
        "payload": {"email": "not-an-email"},
        "expected_status": 400
    },
    {
        "name": "invalid-email-missing-domain",
        "payload": {"email": "dty@not-an-email"},
        "expected_status": 400
    },
    {
        "name": "invalid-email-missing-local",
        "payload": {"email": "@missing-local.com"},
        "expected_status": 400
    },
    {
        "name": "duplicate-email",
        "payload": {"email": "DUPLICATE_EMAIL"},
        "expected_status": 400
    },
]

# Outdated version not recommended:
# INVALID_UPDATE_PAYLOADS = [
#     pytest.param(
#         {"email": "not-an-email"},
#         400,
#         id="invalid-email-no-at"
#     ),
#     pytest.param(
#         {"email": "dty@not-an-email"},
#         400,
#         id="invalid-email-missing-end-part"
#     ),
#     pytest.param(
#         {"email": "@missing-local.com"},
#         400,
#         id="invalid-email-missing-local-part"
#     ),
#     pytest.param(
#         {"email": "DUPLICATE_EMAIL"},
#         400,
#         id="duplicate-email"
#     ),
# ]
# the in test:
# @pytest.mark.parametrize("update_payload, expected_status", INVALID_UPDATE_PAYLOADS)


@pytest.mark.tcid12
def test_update_customer_first_name(customer_helper, customers_dao, create_valid_customer):
    """
    Verify that a customer can be updated successfully.

    Validates that:
        - PUT /customers/{id} returns a successful response
        - Updated fields are reflected in the API response
        - Returned customer structure is valid (Pydantic validation)

    Test flow:
        1. Create customer via fixture
        2. Update first_name and email
        3. Validate response structure
        4. Verify updated values
    """

    # Step 1 — Create customer (POST handled by fixture)
    logger.info("🛠 Creating a test customer for updating name and email.")
    # To keep the customer in the DB (i.e., skip deletion), set: customer = create_customer_for_test(skip_cleanup=True)
    customer = create_valid_customer()  # Default: skip_cleanup=False, validate_response=True

    customer_id = customer["id"]
    # original_email = customer["email"]

    # Define update payload
    updated_first_name = "QAUpdated"
    updated_email = "mart_hanz@golp.com"

    logger.info(f"🔁 Updating customer ID={customer_id} with first_name='{updated_first_name}' "
                f"and email='{updated_email}'")

    # Use the helper's injected api_client (singular) to perform raw update call
    response = customer_helper.update_customer(
        customer_id,
        payload={"first_name": updated_first_name, "email": updated_email},
        return_http_response=True
    )

    assert response.status_code == 200

    # Step 3 — Extract response body
    update_response = response.json

    # Step 4 — Structure validation
    customer_model = assert_valid_customer_response(update_response)

    # Step 5 — Identity validation
    # Ensure we updated the correct customer
    assert_customer_identity(
        customer_model,
        customer_id,
        updated_email
    )

    # Step 6 — Business field validation
    # Validate that the update actually modified the first_name
    assert customer_model.first_name == updated_first_name, (
        f"❌ First name update failed. Expected '{updated_first_name}', "
        f"got '{customer_model.first_name}'"
    )

    logger.info(
        "✅ Customer update verified: ID=%s first_name=%s email=%s",
        customer_model.id,
        customer_model.first_name,
        customer_model.email
    )


@pytest.mark.negative_test
@pytest.mark.tcid21
@pytest.mark.parametrize("case", INVALID_UPDATE_PAYLOADS, ids=[c["name"] for c in INVALID_UPDATE_PAYLOADS])
def test_update_customer_invalid_inputs(customer_helper, customers_dao, create_valid_customer, update_payload,
                                        expected_status):
    """
    Verify that invalid customer updates are rejected.

    Validates that:
        - API returns the correct error response for invalid payloads
        - Error payload follows the expected schema
        - Customer data in the database remains unchanged

    Test flow:
        1. Create a valid customer
        2. Attempt update with invalid payload
        3. Validate error response structure
        4. Confirm database record was not modified
    """

    # Step 1 — Create customer used for update test (one to update, one as duplicate)
    logger.info("🛠 Creating a test customer via factory fixture.")
    # To keep the customer in the DB (i.e., skip deletion), set: customer = create_customer_for_test(skip_cleanup=True)
    original_customer = create_valid_customer()  # Default: skip_cleanup=False, validate_response=True
    # No need to assert ID/email. The fixture already does it: customer_helper.assert_valid_customer_response(customer)

    customer_id = original_customer["id"]
    original_email = original_customer["email"]

    # Step 2 — Prepare payload (avoid mutating parametrize input)
    payload = {**update_payload}

    # Inject duplicate email when required by test case
    if payload.get("email") == "DUPLICATE_EMAIL":
        duplicate_customer = create_valid_customer()
        payload["email"] = duplicate_customer["email"]

        logger.info("🔁 Using duplicate email: %s", payload["email"])

    logger.info(f"🚫 Attempting to update customer ID={customer_id} with payload: {update_payload}")

    # Step 3 — Attempt update (expected to fail)
    # Use the shared api_client fixture for the raw call; pass expected_status so the client returns/parses the
    # error payload.

    response = customer_helper.update_customer(
        customer_id,
        payload=payload,
        expected_status_code=expected_status
    )
    # Now assert the error structure
    assert isinstance(response, dict), f"❌ Expected error response as dict, got: {type(response)}"
    assert response["code"], f"❌ Missing 'code' in response: {response}"
    assert response["message"], f"❌ Missing 'message' in response: {response}"
    validate(instance=response, schema=error_schema)

    # Step 4 — Ensure database record was not modified

    # It is highly recommended when the API call could potentially mutate data if not properly guarded — like in
    # update, delete or PATCH partial operations.
    # You're attempting to mutate existing data (via PUT). There's risk of a partial update or bug in backend
    # validation logic. Verifying that nothing changed is part of what makes it a strong regression test.
    # ✅ Best practice: Keep the DB check here. It's essential.
    db_customer = customers_dao.get_customer_by_email(email=original_email)
    assert db_customer is not None, "❌ Original customer no longer in DB after failed update"
    assert db_customer["ID"] == customer_id, "❌ Customer ID mismatch"
    assert db_customer["user_email"] == original_email, "❌ Email was changed after failed update"
    logger.info("✅ Original customer record remains unchanged after failed update.")


def test_validate_date_modified_and_date_modified_gmt():
    """
    Verify that date_modified and date_modified_gmt change after updating a customer.
    """
    pass
