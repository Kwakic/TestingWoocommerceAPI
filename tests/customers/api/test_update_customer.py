import pytest
import logging

from jsonschema import validate
from datetime import timezone

from EcommerceAPI.src.customers.validators.customer_validators import (
    assert_customer_identity,
    assert_valid_customer_response,
    assert_customer_error_response,
)
from EcommerceAPI.src.utils.generic_utilities import generate_random_email_and_password

from EcommerceAPI.src.utils.date_timestamp_utils import precise_parse_utc_datetime

from tests.shared.contracts.error_schema import error_schema

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.integration]

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
# with the email of another created customers.
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


@pytest.mark.tcid12
@pytest.mark.smoke
@pytest.mark.contract
def test_update_customer_first_name(
    customer_helper, customers_dao, create_valid_customer
):
    """
    Verify that a customers can be updated successfully.

    Validates that:
        - PUT /customers/{id} returns a successful response
        - Updated fields are reflected in the API response
        - Returned customers structure is valid (Pydantic validation)

    Test flow:
        1. Create customers via fixture
        2. Update first_name and email
        3. Validate response structure
        4. Verify updated values
    """

    # Step 1 — Create customers (POST handled by fixture)
    logger.info("🛠 Creating a test customers for updating name and email.")
    # To keep the customers in the DB (i.e.,skip deletion), set: customers = create_customer_for_test(skip_cleanup=True)
    customer = (
        create_valid_customer()
    )  # Default: skip_cleanup=False, validate_response=True

    customer_id = customer["id"]
    # original_email = customers["email"]

    # Define update payload
    updated_first_name = "QAUpdated"
    updated_email = "mart_hanz@golp.com"

    logger.info(
        f"🔁 Updating customers ID={customer_id} with first_name='{updated_first_name}' "
        f"and email='{updated_email}'"
    )

    # Use the helper's injected api_client (singular) to perform raw update call
    response = customer_helper.update_customer(
        customer_id,
        payload={"first_name": updated_first_name, "email": updated_email},
        return_http_response=True,
    )

    assert response.status_code == 200, (
        f"PUT /customers updating failed. "
        f"Expected 201, got {response.status_code}. "
        f"Response: {response.text}"
    )

    # Step 3 — Extract response body
    update_response = response.json

    # Step 4 — Structure validation
    customer_model = assert_valid_customer_response(update_response)

    # Step 5 — Identity validation
    # Ensure we updated the correct customers
    assert_customer_identity(customer_model, customer_id, updated_email)

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
        customer_model.email,
    )


@pytest.mark.tcid21
@pytest.mark.negative
@pytest.mark.contract
@pytest.mark.regression
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
    Verify that invalid customers updates are rejected by the API.

    This test ensures that:

    • Invalid update payloads return the correct error response
    • Error responses follow the expected schema
    • The original customers record in the database remains unchanged

    Test flow:
        1. Create a valid customers
        2. Attempt to update the customers with an invalid payload
        3. Validate the returned error structure
        4. Confirm the database record was not modified
    """

    # ------------------------------------------------------------------
    # Step 1 — Extract test case data
    # ------------------------------------------------------------------
    update_payload = case["payload"]
    expected_status = case["expected_status"]

    # ------------------------------------------------------------------
    # Step 2 — Create baseline customers (fixture performs validation)
    # ------------------------------------------------------------------
    logger.info("🛠 Creating a baseline customers for update test")

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
    assert_customer_error_response(response)

    validate(instance=response, schema=error_schema)

    # ------------------------------------------------------------------
    # Step 6 — Verify database record was NOT modified
    # ------------------------------------------------------------------
    # Important for update tests:
    # even when validation fails, backend bugs could still mutate data.
    # This check guarantees the original record remains intact.

    db_customer = customers_dao.get_customer_by_email(email=original_email)

    assert (
        db_customer is not None
    ), "❌ Original customers no longer exists in the database"

    assert (
        db_customer["ID"] == customer_id
    ), "❌ Customer ID mismatch after failed update"

    assert (
        db_customer["user_email"] == original_email
    ), "❌ Customer email was modified after failed update"

    logger.info(
        "✅ Database record remains unchanged after rejected update (customer_id=%s)",
        customer_id,
    )


@pytest.mark.tcid29
@pytest.mark.regression
def test_validate_date_modified_and_date_modified_gmt(customer_helper, customers_dao):
    """
    Verify that customer modification timestamps are consistent between API and database.

    This test validates the following:

    1. Updating a customer changes the modification timestamp.
    2. The API `date_modified` field matches the database `last_update` timestamp.
    3. The original `date_created` value remains unchanged after update.

    Important notes about timestamps:

    • WordPress stores `user_registered` in site-local time.
    • WooCommerce REST API returns timestamps in UTC.
    • Therefore we allow a timezone tolerance when comparing creation timestamps.

    Test flow:
        1. Fetch a random active customer from DB
        2. Capture DB timestamps before update
        3. Update the customer via API
        4. Validate identity and business changes
        5. Validate timestamp consistency between API and DB
    """

    # -------------------------------------------------------------
    # Step 1 — Retrieve a random active customer from the database
    # -------------------------------------------------------------
    logger.info("🛠 Retrieving random active customer from DB.")
    customer = customers_dao.get_random_customer_from_db(
        qty=1, filters={"user_status": 0}
    )

    if not customer:
        pytest.skip("No active customer found in DB")

    existing_customer = customer[0]

    db_id = existing_customer["ID"]
    db_email = existing_customer["user_email"]

    # WordPress stores this as site-local time (no timezone)
    db_created_at = existing_customer["user_registered"].replace(microsecond=0)

    # Capture DB modification timestamp BEFORE update
    db_modified_before = customers_dao.get_customers_updated_date(db_id)

    # -------------------------------------------------------------
    # Step 2 — Update customer via API
    # -------------------------------------------------------------
    rand_email = generate_random_email_and_password()["email"]

    payload = {"email": rand_email, "billing": {"phone": "36555888666"}}

    response = customer_helper.update_customer(
        customer_id=db_id, payload=payload, return_http_response=True
    )

    # Fail fast if update request failed
    assert response.status_code == 200, f"PUT /customers update failed: {response.text}"

    # -------------------------------------------------------------
    # Step 3 — Validate response structure
    # -------------------------------------------------------------
    updated_customer = response.json
    customer_model = assert_valid_customer_response(updated_customer)

    # Parse API timestamps (API always returns UTC ISO timestamps)
    api_created_at = precise_parse_utc_datetime(customer_model.date_created)
    api_modified_at = precise_parse_utc_datetime(customer_model.date_modified)

    # -------------------------------------------------------------
    # Step 4 — Validate identity and business change
    # -------------------------------------------------------------
    assert_customer_identity(customer_model, db_id, customer_model.email)

    # Ensure update actually changed the email
    assert (
        db_email != customer_model.email
    ), f"❌ Customer email mismatch: expected change from {db_email} to {customer_model.email}"

    # -------------------------------------------------------------
    # Step 5 — Validate creation timestamp remains unchanged
    # -------------------------------------------------------------
    # DB timestamp is stored in site-local timezone.
    # API timestamp is returned in UTC.
    # Therefore we allow a tolerance window (usually 1 hour).
    db_created_at_utc = db_created_at.replace(tzinfo=timezone.utc)

    delta_seconds = abs((api_created_at - db_created_at_utc).total_seconds())

    assert delta_seconds <= 3600, (
        f"❌ Customer created_at mismatch beyond timezone tolerance: "
        f"DB={db_created_at_utc}, API={api_created_at}"
    )

    # -------------------------------------------------------------
    # Step 6 — Validate DB modification timestamp changed
    # -------------------------------------------------------------
    db_modified_after = customers_dao.get_customers_updated_date(db_id)

    assert (
        db_modified_after != db_modified_before
    ), "❌ DB modified timestamp did not change after update"

    # -------------------------------------------------------------
    # Step 7 — Validate API modification timestamp matches DB
    # -------------------------------------------------------------
    assert (
        api_modified_at == db_modified_after
    ), f"❌ Modified timestamp mismatch: DB={db_modified_after}, API={api_modified_at}"
