
import pytest
import logging

from jsonschema import validate

from EcommerceAPI.src.customers.validators.customer_validators import (assert_customer_identity,
                                                                       assert_valid_customer_response)
from tests.shared.schemas.customer import error_schema

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.customers, pytest.mark.regression]

# ------------------------------------------------------------------
# Invalid payloads used for negative update tests
# ------------------------------------------------------------------
# Each case contains:
#   name            → used by pytest for readable test IDs
#   payload         → update payload sent to the API
#   expected_status → expected HTTP status code
#
# NOTE:
# "DUPLICATE_EMAIL" is a placeholder replaced during test execution
# with the email of another created customer.
# ------------------------------------------------------------------

INVALID_UPDATE_PAYLOADS = [
    {
        "name": "invalid-email-no-at",
        "payload": {"email": "not-an-email"},
        "expected_status": 400,
    },
    {
        "name": "invalid-email-missing-domain",
        "payload": {"email": "dty@not-an-email"},
        "expected_status": 400,
    },
    {
        "name": "invalid-email-missing-local",
        "payload": {"email": "@missing-local.com"},
        "expected_status": 400,
    },
    {
        "name": "duplicate-email",
        "payload": {"email": "DUPLICATE_EMAIL"},
        "expected_status": 400,
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
@pytest.mark.parametrize(
    "case",
    INVALID_UPDATE_PAYLOADS,
    ids=[c["name"] for c in INVALID_UPDATE_PAYLOADS],
)
def test_update_customer_invalid_inputs(
    customer_helper,
    customers_dao,
    create_valid_customer,
    case,
):
    """
    Verify that invalid customer updates are rejected by the API.

    This test ensures that:

    • Invalid update payloads return the correct error response
    • Error responses follow the expected schema
    • The original customer record in the database remains unchanged

    Test flow:
        1. Create a valid customer
        2. Attempt to update the customer with an invalid payload
        3. Validate the returned error structure
        4. Confirm the database record was not modified
    """

    # ------------------------------------------------------------------
    # Step 1 — Extract test case data
    # ------------------------------------------------------------------
    update_payload = case["payload"]
    expected_status = case["expected_status"]

    # ------------------------------------------------------------------
    # Step 2 — Create baseline customer (fixture performs validation)
    # ------------------------------------------------------------------
    logger.info("🛠 Creating a baseline customer for update test")

    original_customer = create_valid_customer()

    customer_id = original_customer["id"]
    original_email = original_customer["email"]

    # ------------------------------------------------------------------
    # Step 3 — Prepare payload safely
    # ------------------------------------------------------------------
    # Avoid mutating the shared parametrized dataset.
    payload = dict(update_payload)

    # Special case: duplicate email validation
    if payload.get("email") == "DUPLICATE_EMAIL":
        duplicate_customer = create_valid_customer()
        payload["email"] = duplicate_customer["email"]

        logger.info("🔁 Using duplicate email: %s", payload["email"])

    logger.info(
        "🚫 Attempting invalid update for customer_id=%s payload=%s",
        customer_id,
        payload,
    )

    # ------------------------------------------------------------------
    # Step 4 — Execute update request (expected to fail)
    # ------------------------------------------------------------------
    response = customer_helper.update_customer(
        customer_id,
        payload=payload,
        expected_status_code=expected_status,
    )

    # ------------------------------------------------------------------
    # Step 5 — Validate error response structure
    # ------------------------------------------------------------------
    assert isinstance(response, dict), (
        f"❌ Expected error response as dict, got: {type(response)}"
    )

    assert "code" in response, f"❌ Missing 'code' in response: {response}"
    assert "message" in response, f"❌ Missing 'message' in response: {response}"

    validate(instance=response, schema=error_schema)

    # ------------------------------------------------------------------
    # Step 6 — Verify database record was NOT modified
    # ------------------------------------------------------------------
    # Important for update tests:
    # even when validation fails, backend bugs could still mutate data.
    # This check guarantees the original record remains intact.

    db_customer = customers_dao.get_customer_by_email(email=original_email)

    assert db_customer is not None, (
        "❌ Original customer no longer exists in the database"
    )

    assert db_customer["ID"] == customer_id, (
        "❌ Customer ID mismatch after failed update"
    )

    assert db_customer["user_email"] == original_email, (
        "❌ Customer email was modified after failed update"
    )

    logger.info(
        "✅ Database record remains unchanged after rejected update (customer_id=%s)",
        customer_id,
    )


def test_validate_date_modified_and_date_modified_gmt():
    """
    Verify that date_modified and date_modified_gmt change after updating a customer.
    """
    pass
