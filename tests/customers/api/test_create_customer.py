import pytest
import logging

from faker import Faker  # To avoid hardcoding, we use faker to generate fake data for us

from EcommerceAPI.src.utilities.bulk_ops import bulk_create_and_validate_resources
from EcommerceAPI.src.customers.validators.customer_validators import assert_customer_creation_failed
from jsonschema import validate
from tests.shared.schemas.customers.error_schema import error_schema

faker = Faker()

logger = logging.getLogger(__name__)  # logger.setLevel(logging.DEBUG) --> Already set in pytest.ini

pytestmark = [pytest.mark.customers, pytest.mark.regression]

INVALID_EMAIL_PAYLOADS = [
    pytest.param(
        {"email": "plainaddress", "password": "TestPass1"}, 400, id="no-at-symbol"),
    pytest.param(
        {"email": "@no-local-part.com", "password": "TestPass1"}, 400, id="missing-local-part"),
    pytest.param(
        {"email": "Outlook Contact <outlook-contact@domain.com>", "password": "TestPass1"}, 400, id="name-included"
    ),
    pytest.param(
        {"email": "no-at.domain.com", "password": "TestPass1"}, 400, id="missing-at"),
    pytest.param(
        {"email": "user@gmail", "password": "TestPass1"}, 400, id="missing-Top-Level Domain"),
    pytest.param(
        {}, 400, id="missing-email-field")  # ❌ Missing email (the only required field).)
]


# ---------------------------
# 🚀 Test: Bulk Create Customers
# ---------------------------
@pytest.mark.tcid01
@pytest.mark.bulk
@pytest.mark.parametrize("qty", [1, 3, 5])
def test_bulk_create_customers(qty, customer_helper, customers_dao, create_valid_customer):
    """
    Test bulk creation of customers.

    Creates multiple customers using the factory fixture and verifies that
    each created customers exists in both API and database.

    What the fixture `create_valid_customer` already does:
        - Sends POST /customers
        - Validates HTTP status code (201)
        - Validates response structure using Pydantic
        - Registers created customers for cleanup

    Test flow:
        1. Create N customers using bulk utility
        2. Verify each customers exists via API
        3. Verify API data matches database record
    """

    # ------------------------
    # Create function
    # ------------------------
    # Called by the bulk utility to create one customers.
    # The fixture already performs POST validation and cleanup registration.

    def create_fn():
        # Create a valid customers via the fixture.
        # Default: skip_cleanup=False, validate_response=True
        customer = create_valid_customer(
            billing={
                "first_name": "John", "last_name": "Doe",
                "address_1": "123 Test St", "city": "Austin",
                "state": "TX", "postcode": "73301", "country": "US"
            },
            shipping={
                "first_name": "John", "last_name": "Doe",
                "address_1": "123 Test St", "city": "Austin",
                "state": "TX", "postcode": "73301", "country": "US"
            }
        )

        # Extract identifiers used later for validation
        email = customer["email"]
        customer_id = customer["id"]

        # 📦 Return identifiers and metadata (for teardown registration). Email: used as identifier to later validate
        # that customers exists. Metadata (like ID) is optional, but useful for debugging or future logging.
        return email, {"id": customer_id, "resource_type": "customers"}

    # ------------------------
    # ✅ Validate function
    # ------------------------
    # It encapsulates/summarize the logic to check that the created customers is visible via GET /customers and matches
    # DB (via DAO).
    def validate_fn(email):
        """
        Verify that the customers exists and matches database data.

        Steps:
            1. Fetch customers via API
            2. Fetch customers from database
            3. Compare both records
        """

        # API Fetch + API VALIDATION + DB FETCH + DB VALIDATION
        customer_helper.assert_customer_exists_and_matches_db(
            email=email,
            dao=customers_dao
        )

    # -------------------------------------------------------
    # 🚀 Run the bulk utility: create + validate + teardown
    # -------------------------------------------------------
    bulk_create_and_validate_resources(
        create_fn=create_fn,
        validate_fn=validate_fn,
        qty=qty,
        label="customers"
    )


# ---------------------------
# ⚠️ Test: Edge Cases for Bulk Create
# ---------------------------
@pytest.mark.tcid02
@pytest.mark.bulk
@pytest.mark.skip(reason="Edge case validation for qty=0 and qty=101; run manually when needed")
@pytest.mark.parametrize("qty", [0, 101])
def test_bulk_create_customers_edge_cases(qty, customer_helper, customers_dao, create_valid_customer):
    """
    Edge case test for bulk creation.

    Runs the bulk utility with extreme quantities (0 and 101)
    to ensure the framework handles boundary conditions correctly.

    Fixture responsibilities:
        - POST validation
        - response structure validation
        - automatic cleanup registration
    """

    # ------------------------
    # ✅ Create function
    # ------------------------
    # Called by the bulk utility to create one customers.
    # The fixture already performs POST validation and cleanup registration.
    def create_fn():
        customer = create_valid_customer()  # Default: skip_cleanup=False, validate_response=True

        email = customer["email"]
        customer_id = customer["id"]

        # 📦 Return identifiers and metadata (for teardown registration). Email: used as identifier to later validate
        # that customers exists. Metadata (like ID) is optional, but useful for debugging or future logging.
        return email, {"id": customer_id, "resource_type": "customers"}

    # ------------------------
    # ✅ Validate function
    # ------------------------
    # It encapsulates/summarize the logic to check that the created customers is visible via GET /customers and matches
    # DB (via DAO).
    def validate_fn(email):
        """
        Validates that the customers:
        - API GET /customers can find the customers.
        - The response is valid JSON/schema.
        - The data matches what’s stored in the DB.
        Args:
            email (str): Unique identifier used to search for the customers
        """
        # API Fetch + API VALIDATION + DB FETCH + DB VALIDATION
        customer_helper.assert_customer_exists_and_matches_db(
            email=email,
            dao=customers_dao
        )

    # -------------------------------------------------------
    # 🚀 Run the bulk utility: create + validate + teardown
    # -------------------------------------------------------
    bulk_create_and_validate_resources(
        create_fn=create_fn,
        validate_fn=validate_fn,
        qty=qty,
        label=f"customer_edge_case_{qty}"
    )


# ---------------------------
# 🧪 Test: Minimal Customer Creation
# ---------------------------
@pytest.mark.tcid03
def test_create_single_customer_with_email_and_password_only(customer_helper, customers_dao, create_valid_customer):
    """
    Create a customers using the minimum valid payload.

    The fixture `create_valid_customer` already performs:
        - POST /customers
        - status code validation (201)
        - response structure validation (Pydantic)
        - cleanup registration

    Test flow:
        1. Create a customers
        2. Fetch customers via API
        3. Verify API data matches database record
    """

    # Step 1 — Create customers (fixture performs POST validation)
    logger.info("🛠 Creating a test customers via factory fixture.")
    # To keep the customers in the DB(i.e., skip deletion), set: customers = create_customer_for_test(skip_cleanup=True)
    customer = create_valid_customer()  # Default: skip_cleanup=False, validate_response=True

    customer_id = customer["id"]
    email = customer["email"]

    # Step 2 — Verify API response matches database record
    customer_helper.assert_customer_exists_and_matches_db(
        email=email,
        dao=customers_dao
    )

    logger.info("🎯 Full validation complete for customers ID: %r", customer_id)


# below partial payload perhaps can be moved to customers's data file????
def generate_address_pairs():
    return [
        (
            {
                "first_name": faker.first_name(),
                "last_name": faker.last_name(),
                "address_1": faker.street_address(),
                "city": faker.city(),
                "state": "MADRID",
                "postcode": faker.postcode(),
                "country": "SPAIN",
            },
            {
                "first_name": faker.first_name(),
                "last_name": faker.last_name(),
                "address_1": faker.street_address(),
                "city": faker.city(),
                "state": "NY",
                "postcode": faker.postcode(),
                "country": "US",
            },
        ),
        (
            {
                "first_name": faker.first_name(),
                "last_name": faker.last_name(),
                "address_1": faker.street_address(),
                "city": faker.city(),
                "state": "N/A",
                "postcode": faker.postcode(),
                "country": "GERMANY",
            },
            {
                "first_name": faker.first_name(),
                "last_name": faker.last_name(),
                "address_1": faker.street_address(),
                "city": faker.city(),
                "state": "BOLOGNA",
                "postcode": faker.postcode(),
                "country": "ITALY",
            },
        ),
    ]


@pytest.mark.skip(reason="Billing/shipping fields optional — no functional difference tested.")
@pytest.mark.tcid04
@pytest.mark.parametrize("billing, shipping", generate_address_pairs())
def test_create_customer_with_varied_addresses(
        customer_helper,
        customers_dao,
        billing,
        shipping,
        create_valid_customer
):
    """
    Create customers with different billing and shipping addresses.

    Validates that address variations are accepted and stored correctly.

    Test flow:
        1. Create customers with parameterized addresses
        2. Verify customers exists via API
        3. Verify API data matches database record
    """

    # ✅ Create customers using fixture factory
    logger.debug(f"📦 Billing data: {billing}")
    logger.debug(f"📦 Shipping data: {shipping}")
    # # 🧠 Optional: Pretty Print for Readability
    # # If the billing/shipping data is large, consider formatting them with json.dumps():
    # import json
    # logger.debug(f"📦 Billing data: {json.dumps(billing, indent=2)}")
    # # This makes the logs more readable, especially for nested or complex payloads

    # -------------------------------------------
    # ✅ Create customers via fixture factory
    # -------------------------------------------
    logger.info("🛠 Creating a test customers via factory fixture with parameterized billing and shipping addresses")
    # To keep the customers in the DB(i.e.,skip deletion), pass: customers = create_customer_for_test(skip_cleanup=True)
    customer = create_valid_customer(billing=billing, shipping=shipping)
    customer_id = customer["id"]
    email = customer["email"]

    # Verify API response matches database record
    customer_helper.assert_customer_exists_and_matches_db(
        email=email,
        dao=customers_dao
    )

    logger.info("🎯 Full validation complete for customers ID: %r", customer_id)


@pytest.mark.negative_test
@pytest.mark.tcid15
@pytest.mark.parametrize("payload, expected_status_code", INVALID_EMAIL_PAYLOADS)
def test_create_customer_email_field_validation(customer_helper, customers_dao, customer_api_raw, payload,
                                                expected_status_code):
    """
    Negative test for invalid email values during customers creation.

    This test bypasses the factory fixture because invalid payloads
    should return HTTP 400 responses.

    Test flow:
        1. Send POST /customers with invalid email
        2. Validate HTTP 400 response
        3. Validate error response structure

    Args:
        customers_dao: Fixture providing customers DAO.
        customer_helper: Fixture providing customers API helper.
        customer_api_raw(Callable): .Fixture providing low-level access t tests that need to inspect raw
        responses.
        payload (dict): Test input payload with malformed or missing email/password fields.
        expected_status_code (int): Expected HTTP response code.
    """

    # -------------------------------------------
    # 📦 Extract email/password from payload
    # -------------------------------------------
    email = payload.get("email")

    logger.info(f"🧪 Testing customers creation with invalid email: '{email}'")

    # -------------------------------------------
    # 📞 Call customers creation using factory method
    # -------------------------------------------

    http_response = customer_api_raw.post(endpoint="customers", payload=payload)

    response = http_response.json

    assert http_response.status_code == expected_status_code

    # --------------------------------------------
    # 📋 Validate error schema and contents
    # --------------------------------------------
    validate(instance=response, schema=error_schema)

    logger.info(f"✅ Proper error returned for payload: {payload} → {response['code']}: {response['message']}")


@pytest.mark.negative_test
@pytest.mark.tcid16
def test_create_customer_fail_for_existing_email(create_valid_customer, customer_api_raw, customer_helper,
                                                 customers_dao):
    """
    Negative test: creating a customers with an already existing email.

    Test flow:
        1. Create a valid customers
        2. Attempt to create another customers with the same email
        3. Expect HTTP 400 with duplicate email error
        4. Verify the original customers still exists

    Args:
        create_valid_customer (Callable): Factory fixture to create valid WooCommerce customers
        customer_api_raw (Raw APIClient): Fixture for low-level API calls used for negative testing
        customer_helper: Provides customers's helper
        customers_dao: Provides customers's DAOs
    """

    # -------------------------------
    #  ✅ Create customers via fixture factory
    # -------------------------------
    logger.info("🛠 Creating a negative test when it is expected to fail for existing email.")
    existing_customer = create_valid_customer()  # Default: skip_cleanup=False, validate_response=True
    # To keep the customers in the DB(i.e.,skip deletion), pass: customers = create_customer_for_test(skip_cleanup=True)

    email = existing_customer['email']

    # -------------------------------
    #  ✅ Re-create customers via fixture factory
    # -------------------------------
    logger.info(f"⚠️ Attempt to re-create the customers using existing email: {email}")

    payload = {
        "email": email,
        "password": "Password1"  # must pass something, doesn't need to match
    }

    # -------------------------------------------
    # 📞 Call customers creation using factory method
    # -------------------------------------------
    http_response = customer_api_raw.post(
        endpoint="customers",
        payload=payload,  # or inline--> payload = {"email": "invalid", "password": "Password1"}
    )

    response = http_response.json

    # -------------------------------------------
    # ✅ Transport validation (EXPLICIT)
    # -------------------------------------------
    assert http_response.status_code == 400, (
        f"Expected 400, got {http_response.status_code}. "
        f"Response: {http_response.text[:300]}"
    )

    # ✅ Business validation (customers's validator responsibility)
    assert_customer_creation_failed(response)

    logger.info("🧪 Validating response for duplicate email error...")

    response = http_response.json

    # API Fetch + API VALIDATION + DB FETCH + DB VALIDATION
    customer_helper.assert_customer_exists_and_matches_db(
        email=email,
        dao=customers_dao
    )

    # --------------------------------------------
    # 📋 Validate error schema and contents
    # --------------------------------------------
    validate(instance=response, schema=error_schema)
    logger.info(f"✅ Proper error returned for payload: {payload} → {response['code']}: {response['message']}")
