import pytest
import logging

from jsonschema import validate
from json import loads


from tests.shared.schemas.customer import error_schema
from EcommerceAPI.src.validators.customers.customer_schema_validator import validate_customer_response_schema

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

    # ---------------------------------------------------------------------------------------------------------
    # 🔍 Confirm customer exists in DB and API GET response matches DB.
    # 🧩 Schema Validation (it checks that the GET response is valid).
    # ---------------------------------------------------------------------------------------------------------
    customer_helper.validate_customer_exists_fast(email=email, dao=customers_dao)
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


    """

    # ✅ Create customer using factory fixture
    # -------------------------------------------
    logger.info("🛠 Creating a test customer via factory fixture.")
    # To keep the customer in the DB (i.e., skip deletion), set: customer = create_customer_for_test(skip_cleanup=True)
    customer = create_valid_customer()  # Default: skip_cleanup=False, validate_response=True
    # No need to assert ID/email. The fixture already does it: customer_helper.assert_valid_customer_response(customer)

    customer_id = customer["id"]
    email = customer["email"]

    # ------------------------------------------------------------
    # 🔍 Get customer by ID and validate
    # ------------------------------------------------------------
    logger.info(f"🔎 Fetching customer by ID: {customer_id}")
    customer_from_get = customer_helper.call_get_customer_by_id(customer_id)
    assert customer_from_get["id"] == customer_id, (f"❌ Mismatched ID: Expected {customer_id}, "
                                                    f"got {customer_from_get['id']}")
    assert customer_from_get["email"] == email, (f"❌ Mismatched email: Expected {email}, "
                                                 f"got {customer_from_get['email']}")
    logger.info(f"✅ Fetched customer by ID matches created one: ID={customer_id}, Email={email}")

    # ------------------------------------------------------------------
    # 📋 Schema Validation (GET response)
    # ------------------------------------------------------------------
    # The validate_customer_response_schema(customer_from_get) is validating the response from:GET /customers/{id}
    validate_customer_response_schema(customer=customer_from_get)

    # ---------------------------------------------------------------------------------------------------------
    # 🔍 Confirm customer exists in DB and API GET response matches DB.
    # 🧩 Schema Validation (it checks that the GET response is valid).
    # ---------------------------------------------------------------------------------------------------------
    customer_helper.validate_customer_exists_fast(email=email, dao=customers_dao)
    logger.info("🎯 Full validation complete for customer ID: %r", customer_id)


@pytest.mark.negative_test
@pytest.mark.tcid17
def test_retrieve_nonexistent_customer_returns_404(all_resources, create_valid_customer):
    """
     🚫  Attempt to GET a nonexistent customer.
    - Expect 404
    - Validate error schema
    """
    customer_helper = all_resources.customer.helper
    fake_customer_id = 99999999

    logger.info(f"🚫 Retrieving non-existent customer ID: {fake_customer_id}")
    response = customer_helper.call_get_customer_by_id(customer_id=fake_customer_id, expected_status_code=404)

    if isinstance(response, str):
        response = loads(response)

    assert response['code'] == 'woocommerce_rest_invalid_id', "❌ Error 'code' should not be empty"
    assert response['message'], "❌ Error 'message' should not be empty"

    validate(instance=response, schema=error_schema)
    logger.info("✅ Error response schema validated for non-existent customer fetch")




