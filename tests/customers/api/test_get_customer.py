import pytest
import logging

from jsonschema import validate
from json import loads

from tests.shared.schemas.customer import error_schema
from EcommerceAPI.src.customers.schemas.customer_schema_validator import validate_customer_response_schema
from EcommerceAPI.src.customers.validators.customer_validators import (assert_customer_not_found_error,
                                                                       assert_customer_retrieved_successfully,
                                                                       assert_customer_exists_and_matches_api,
                                                                       assert_customer_identity,
                                                                       assert_single_customer_by_email)

logger = logging.getLogger(__name__)
#  logger.setLevel(logging.DEBUG)  # already set in pytest.ini

pytestmark = [pytest.mark.customers, pytest.mark.regresion]


@pytest.mark.customers
@pytest.mark.tcid13
def test_get_customer_by_email(customer_helper, customers_dao, create_valid_customer):
    """
    !!!!!we have the same to create customer i.e. tcid03, perhaps this test should only retrieve the customer!!!!

    Validate that a created customer can be retrieved by email (a custom query like GET /customers?email={email}).
    It validates the following aspects:
        - API response structure (schema validation) after POST /customers
        - Critical fields (`id`, `email`, etc.) are present and correct
        - Customer appears in GET /customers endpoint and matches DB
        - API response matches DB record
        - Logging and traceability (via logger + correlation_id where applicable)
        - Cleanup is automatic unless explicitly skipped
        - Generates unique correlation ID for logs for better traceability

    🔧 Behind the scenes:
    - It uses a factory fixture: `create_valid_customer(...)` which calls:
        - `customer_helper.create_customer(...)` → handles API POST
        - Automatically validates:
            - Response schema via `validate_customer_response_schema(...)`
            - Critical fields via `assert_valid_customer_response(...) such as email and ID`
            - Registers the customer for teardown (unless skip_cleanup=True)
    - Returns full customer dict (e.g., `{"id": 123, "email": ..., "username": ...}`)

    Test authors:
    Access to helpers and DAOs is made via fixtures
        - Do NOT instantiate helpers
        - Do NOT delete customers manually
        - Do NOT query DB directly without DAO
    """
    # -------------------------------------------
    # ✅ Create customer using factory fixture
    # -------------------------------------------
    logger.info("🛠 Creating a test customer via factory fixture.")
    # To keep the customer in the DB (i.e., skip deletion), set: customer = create_customer_for_test(skip_cleanup=True)
    customer = create_valid_customer()  # Default: skip_cleanup=False, validate_response=True
    # No need to assert ID/email. The fixture already does it: customer_helper.assert_valid_customer_response(customer)

    customer_id = customer["id"]
    email = customer["email"]

    # ------------------------------------------------------------
    # 🔍 Get customer by EMAIL and validate
    # ------------------------------------------------------------
    logger.info(f"🔎 Fetching customer by email: {email}")
    response = customer_helper.get_customer_by_email(
        email=email,
        return_http_response=True
    )

    # ✅ Transport validation (tests own status validation)
    assert response.status_code == 200

    # WooCommerce returns a LIST when filtering by email
    customers = response.json

    # Extract correct customer using validator.
    # This endpoint returns a list, so we must enforce exactly one match.
    customer_from_get = assert_single_customer_by_email(customers, email)

    # Validate identity
    assert_customer_identity(customer_from_get, customer_id, email)

    logger.info(
        f"✅ Fetched customer by email matches created one: ID={customer_id}, Email={email}"
    )
    # ------------------------------------------------------------------
    # 📋 Schema Validation (GET response)
    # ------------------------------------------------------------------

    # ---------------------------------------------------------------------------------------------------------
    # 🔍 Confirm customer exists in DB and API GET response matches DB.
    # 🧩 Schema Validation (it checks that the GET response is valid).
    # ---------------------------------------------------------------------------------------------------------
    # 1️⃣ Fetch (helper responsibility)
    customers = customer_helper.list_customers_paginated(email=email)

    # 2️⃣ DB
    db_customer = customers_dao.get_customer_by_email(email)

    # 3️⃣ Assert (assertion layer)
    assert_customer_exists_and_matches_api(customers, email, db_customer)

    logger.info("🎯 Full validation complete for customer ID: %r", customer_id)


@pytest.mark.tcid14
def test_get_customer_by_id(customer_helper, customers_dao, create_valid_customer):
    """
    Validate that a created customer can be retrieved by ID (validates the endpoint GET /customers/{id}).

    It validates the following aspects:
        - API response structure (schema validation) after POST /customers
        - Critical fields (`id`, `email`, etc.) are present and correct
        - Customer appears in GET /customers endpoint and matches DB
        - API response matches DB record
        - Logging and traceability (via logger + correlation_id where applicable)
        - Cleanup is automatic unless explicitly skipped
        - Generates unique correlation ID for logs for better traceability

    🔧 Behind the scenes:
    - It uses a factory fixture: `create_valid_customer(...)` which calls:
        - `customer_helper.create_customer(...)` → handles API POST
        - Automatically validates:
            - Response schema via `validate_customer_response_schema(...)`
            - Critical fields via `assert_valid_customer_response(...) such as email and ID`
            - Registers the customer for teardown (unless skip_cleanup=True)
    - Returns full customer dict (e.g., `{"id": 123, "email": ..., "username": ...}`)

    Test authors:
    Access to helpers and DAOs is made via fixtures
        - Do NOT instantiate helpers
        - Do NOT delete customers manually
        - Do NOT query DB directly without DAO

    Verify that a customer can be retrieved by ID.

    🧠 FLOW:
    --------
    1. Create a valid customer using fixture (already validated & safe)
    2. Call GET endpoint using helper (HttpResponse mode)
    3. Validate transport layer (status_code)
    4. Extract JSON body
    5. Validate business data

    WHY:
    ----
    - Fixture ensures valid setup (no need to revalidate creation)
    - Test owns status_code validation (fail-fast)
    - Business validators remain clean and focused

    EXPECTED:
    ---------
    - Status code: 200
    - Returned customer matches created customer

    NOTE related to create_valid_customer() fixture:
    To keep the customer in the DB (i.e., skip deletion), set: customer = create_customer_for_test(skip_cleanup=True)
    No need to assert ID/email. The fixture already does it: customer_helper.assert_valid_customer_response(customer)
    Default: skip_cleanup=False, validate_response=True
    """
    # -------------------------------------------
    # Setup (fixture handles POST 201)
    # -------------------------------------------
    logger.info("🛠 Creating a test customer via factory fixture.")
    # Create customer using factory fixture
    customer = create_valid_customer()

    # ------------------------------------------------------------
    # Act (GET) Get customer by ID and validate
    # ------------------------------------------------------------
    customer_id = customer["id"]
    email = customer["email"]

    logger.info(f"🔎 Fetching customer by ID: {customer_id}")
    # By setting flag "return_http_response=True" it returns HttpResponse necessary to validate status_code, headers...
    # This endpoint returns ONE object, not list So assert_single_customer_by_email() should NOT be used.
    response = customer_helper.get_customer_by_id(
        customer_id,
        return_http_response=True
    )

    # ------------------------------------------------------------
    # Transport validation (TEST responsibility - FAIL FAST)
    # Extract JSON to validate body
    # ------------------------------------------------------------
    customer_data = assert_customer_retrieved_successfully(response)

    # ------------------------------------------------------------
    # 🔍 Get customer by ID and validate
    # ------------------------------------------------------------

    assert_customer_identity(customer_data, customer_id, email)

    logger.info(f"✅ Fetched customer by ID matches created one: ID={customer_id}, Email={email}")

    # ------------------------------------------------------------------
    # 📋 Schema Validation (GET response)
    # ------------------------------------------------------------------
    # The validate_customer_response_schema(customer_from_get) is validating the response from:GET /customers/{id}
    validate_customer_response_schema(customer=customer_data)

    # ---------------------------------------------------------------------------------------------------------
    # 🔍 Confirm customer exists in DB and API GET response matches DB.
    # 🧩 Schema Validation (it checks that the GET response is valid).
    # ---------------------------------------------------------------------------------------------------------
    # 1️⃣ Fetch (helper responsibility)
    customers = customer_helper.list_customers_paginated(email=email)

    # 2️⃣ DB
    db_customer = customers_dao.get_customer_by_email(email)

    # 3️⃣ Assert (assertion layer)
    assert_customer_exists_and_matches_api(customers, email, db_customer)

    logger.info("🎯 Full validation complete for customer ID: %r", customer_id)


@pytest.mark.negative_test
@pytest.mark.tcid17
def test_get_customer_not_found(customer_helper, customers_dao, create_valid_customer):
    """
    Verify API returns 404 when customer does not exist.

    🧠 WHY THIS TEST:
    -----------------
    - Ensures proper error handling
    - Validates API contract for missing resources

    IMPORTANT:
    ----------
    - Do NOT use fixture (fixture always creates valid customer)
    - Use helper in HttpResponse mode
    """

    non_existing_id = 99999999

    logger.info(f"🚫 Retrieving non-existent customer ID: {non_existing_id}")

    response = customer_helper.get_customer_by_id(customer_id=non_existing_id)

    if isinstance(response, str):
        response = loads(response)

    assert_customer_not_found_error(response)  # It validates: data: status 404, code, error message

    validate(instance=response, schema=error_schema)
    logger.info("✅ Error response schema validated for non-existent customer fetch")
