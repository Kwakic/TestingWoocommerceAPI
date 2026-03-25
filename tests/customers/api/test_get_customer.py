import pytest
import logging

from jsonschema import validate
from json import loads

from tests.shared.contracts.error_schema import error_schema

from EcommerceAPI.src.customers.validators.customer_validators import (
    assert_customer_not_found_error,
    assert_customer_retrieved_successfully,
    assert_customer_identity,
    assert_single_customer_by_email,
)

logger = logging.getLogger(__name__)
#  logger.setLevel(logging.DEBUG)  # already set in pytest.ini

pytestmark = [pytest.mark.integration]


@pytest.mark.tcid13
@pytest.mark.smoke  # Critical → smoke
@pytest.mark.sanity  # Fast → sanity
def test_get_customer_by_email(customer_helper, customers_dao, create_valid_customer):
    """
    Verify that a customers can be retrieved using the email filter.

    Endpoint tested:
        GET /customers?email={email}

    Fixture responsibilities (`create_valid_customer`):
        - POST /customers
        - response validation (Pydantic)
        - automatic cleanup registration

    Test flow:
        1. Create a customers
        2. Retrieve customers using email filter
        3. Validate returned dataset
        4. Verify returned customers identity
        5. Verify API data matches database
    """

    # -------------------------------------------
    # 🛠 Step 1 — Create a valid customers
    # -------------------------------------------
    logger.info("🛠 Creating a test customers via factory fixture.")

    # Fixture handles:
    #   - POST /customers
    #   - Pydantic validation
    #   - automatic cleanup registration
    customer = create_valid_customer()

    customer_id = customer["id"]
    email = customer["email"]

    # -------------------------------------------
    # 🔎 Step 2 — Retrieve customers via email filter
    # -------------------------------------------
    logger.info("🔎 Fetching customers by email: %s", email)

    # Request HttpResponse wrapper so we can validate status code (return_http_response=True)
    response = customer_helper.get_customer_by_email(
        email=email, return_http_response=True
    )

    # -------------------------------------------
    # 🚦 Step 3 — Transport validation (FAIL FAST)
    # -------------------------------------------
    assert (
        response.status_code == 200
    ), f"Expected 200, got {response.status_code}. Response: {response.text}"

    # -------------------------------------------
    # 📦 Step 4 — Extract dataset
    # -------------------------------------------
    # This endpoint returns a LIST of customers.
    customers = response.json

    # -------------------------------------------
    # 🔍 Step 5 — Extract the correct customers from dataset
    # -------------------------------------------
    customer_model = assert_single_customer_by_email(customers, email)
    # -------------------------------------------
    # 🧠 Step 6 — Identity validation
    # -------------------------------------------
    # Convert raw dict → validated CustomerModel
    # Ensure the retrieved customers matches the one we created.
    assert_customer_identity(customer_model, customer_id, email)

    logger.info(
        "✅ Fetched customers matches created one: ID=%s, Email=%s", customer_id, email
    )

    # -------------------------------------------
    # 🗄 Step 7 — API vs DB consistency validation
    # -------------------------------------------
    # Helper orchestrates:
    #   - API fetch
    #   - DB lookup
    #   - API ↔ DB validation
    customer_helper.assert_customer_exists_and_matches_db(email, customers_dao)

    logger.info("🎯 Full validation complete for customers ID: %r", customer_id)


@pytest.mark.tcid14
@pytest.mark.smoke  # critical endpoint → smoke
@pytest.mark.contract  # includes response validation → contract
def test_get_customer_by_id(customer_helper, customers_dao, create_valid_customer):
    """
    Verify that a customers can be retrieved by ID.

    Endpoint tested:
        GET /customers/{id}

    Fixture responsibilities:
        - POST /customers
        - response validation (Pydantic)
        - cleanup registration

    Test flow:
        1. Create customers
        2. Retrieve customers by ID
        3. Validate response structure
        4. Verify returned customers identity
        5. Verify API data matches database
    """

    # -------------------------------------------
    # 🛠 Step 1 — Create a valid customers
    # -------------------------------------------
    logger.info("🛠 Creating a test customers via factory fixture.")

    # The fixture already validates POST response and registers cleanup.
    customer = create_valid_customer()

    customer_id = customer["id"]
    email = customer["email"]

    # -------------------------------------------
    # 🔎 Step 2 — Retrieve customers via API
    # -------------------------------------------
    logger.info(f"🔎 Fetching customers by ID: {customer_id}")

    # Request HttpResponse wrapper so we can validate status code (return_http_response=True)
    response = customer_helper.get_customer_by_id(
        customer_id, return_http_response=True
    )

    # -------------------------------------------
    # 🚦 Step 3 — Validate status code + response structure
    # -------------------------------------------
    customer_model = assert_customer_retrieved_successfully(response)

    # -------------------------------------------
    # 🔍 Step 4 — Business validation
    # -------------------------------------------
    # Ensure we retrieved the correct customers
    assert_customer_identity(customer_model, customer_id, email)

    logger.info(
        "✅ Fetched customers matches created one: ID=%s, Email=%s", customer_id, email
    )
    # -------------------------------------------
    # 🗄 Step 5 — API vs DB consistency validation
    # -------------------------------------------
    # Helper orchestrates:
    #   - GET /customers list
    #   - DB lookup via DAO
    #   - API vs DB validation
    customer_helper.assert_customer_exists_and_matches_db(email, customers_dao)

    logger.info("🎯 Full validation complete for customers ID: %r", customer_id)


@pytest.mark.tcid17
@pytest.mark.negative
@pytest.mark.contract
@pytest.mark.regression  # not fast / edge → regression
def test_get_customer_not_found(customer_helper, customers_dao, create_valid_customer):
    """
    Negative test for retrieving a non-existing customers.

    Endpoint tested:
        GET /customers/{id}

    Test flow:
        1. Request non-existing customers ID
        2. Validate API returns correct error response
        3. Validate error schema
    """

    non_existing_id = 99999999

    logger.info(f"🚫 Retrieving non-existent customers ID: {non_existing_id}")

    # Without return_http_response=True because the validator expects the JSON error payload. Just keep it consistent
    # across negative tests.
    response = customer_helper.get_customer_by_id(customer_id=non_existing_id)

    # Normalize response to dictionary
    response = loads(response) if isinstance(response, str) else response
    # Validate API error response
    assert_customer_not_found_error(response)

    validate(instance=response, schema=error_schema)
    logger.info("✅ Error response schema validated for non-existent customers fetch")
