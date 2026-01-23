import pytest
import logging


logger = logging.getLogger(__name__)  # logger.setLevel(logging.DEBUG) --> Already set in pytest.ini


pytestmark = [pytest.mark.customers, pytest.mark.regresion]


# ---------------------------
# 🧪 Test: Minimal Customer Creation
# ---------------------------
@pytest.mark.tcid333
def test_create_single_customer_with_email_and_password_only(customer_helper, customers_dao, create_valid_customer):
    """
    ✅ Test Summary:
    This test creates a customer using the minimum valid payload (email + password only)
    and validates API + DB integrity.

    It validates the following aspects:
        - API response structure (schema validation) after POST /customers
        - Critical fields (`id`, `email`, etc.) are present and correct
        - Customer appears in GET /customers endpoint and matches DB
        - API response matches DB record
        - Logging and traceability (via logger + correlation_id where applicable)
        - Cleanup is automatic unless explicitly skipped

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
    customer_helper.validate_customer_exists_and_matches(email=email, dao=customers_dao)
    logger.info(f"🎯 Full validation complete for customer ID={customer_id}")



