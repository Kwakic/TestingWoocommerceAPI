import pytest
import logging

from faker import Faker  # To avoid hardcoding, we use faker to generate fake data for us

from EcommerceAPI.src.utilities.bulk_ops import bulk_create_and_validate_resources
from EcommerceAPI.src.validators.customers.customer_schema_validator import validate_customer_error_response_schema
from EcommerceAPI.src.validators.customers.customer_assertions import assert_customer_creation_failed
from EcommerceAPI.src.validators.shared.base_validators import assert_status_code

faker = Faker()

logger = logging.getLogger(__name__)  # logger.setLevel(logging.DEBUG) --> Already set in pytest.ini


pytestmark = [pytest.mark.customers, pytest.mark.regresion]


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
        {"email": "@missing-local.org", "password": "TestPass1"}, 400, id="missing-local-org"),
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
    📌 Test: Bulk creation of customer accounts.

    This test creates a customer/s using the minimum valid payload (email + password only)
    and validates API + DB integrity.

    This test uses a generic bulk utility to:
    - Create multiple customers via API
    - Registers each customer for teardown via factory fixture
    - Parametrized to run with different quantities (1, 3, 5)
    - Generates unique correlation ID for logs for better traceability

     Args: qty: This test will run multiple times: once with qty = 1, once with qty = 3, once with qty = 5.
            customer_helper: Provides customer's helper
            customers_dao: Provides customer's DAOs
            create_valid_customer: The test will call it inside create_fn.It creates a single customer with unique
            name/email. Automatically registered for teardown inside the fixture. It handles both happy and error paths.
            Validates POST schema.

    🔁 DRY design pattern: Uses externalized create/validate/register functions to keep test reusable and clean.

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

    # ------------------------
    # ✅ CREATE FUNCTION
    # ------------------------
    # It encapsulates/summarize the logic to create one customer via the create_valid_customer fixture, perform
    # immediate asserts, validate POST response schema, and return identifiers for teardown.

    def create_fn():
        # 🧪 Calls the fixture to create one customer
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

        # 🔐 Extract primary identifiers
        email = customer["email"]
        customer_id = customer["id"]

        # 📦 Return identifiers and metadata (for teardown registration). Email: used as identifier to later validate
        # that customer exists. Metadata (like ID) is optional, but useful for debugging or future logging.
        return email, {"id": customer_id, "resource_type": "customers"}

    # ------------------------
    # ✅ Validate function
    # ------------------------
    # It encapsulates/summarize the logic to check that the created customer is visible via GET /customers and matches
    # DB (via DAO).
    def validate_fn(email):
        """
        Validates that the customer:
        - API GET /customers can find the customer.
        - The response is valid JSON/schema.
        - The data matches what’s stored in the DB.
        Args:
            email (str): Unique identifier used to search for the customer
        """
        customer_helper.validate_customer_exists_and_matches_api(email=email, dao=customers_dao)

    # -------------------------------------------------------
    # 🚀 Run the bulk utility: create + validate + teardown
    # -------------------------------------------------------
    bulk_create_and_validate_resources(
        create_fn=create_fn,
        validate_fn=validate_fn,
        qty=qty,
        label="customer"
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
    📌 Edge Case Test: Bulk creation with 0 and 101 customers.

    This test uses a generic bulk utility to:
    - Create 0 or 101 customers via API
    - Validate POST response schema immediately after creation
    - Confirm presence via GET /customers
    - Assert correct data is stored in the database via DAO
    - Handles pagination if applicable
    - Logs with correlation IDs for traceability
    - Parametrized to run with edge quantities: 0 and 101

    Args:
        qty: Number of customers to create (0 and 101 for edge cases)
        customer_helper: Provides customer's helper
        customers_dao: Provides customer's DAOs
        create_valid_customer: Fixture that creates a single customer and registers teardown

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
    """

    # ------------------------
    # ✅ Create function
    # ------------------------
    def create_fn():
        customer = create_valid_customer()  # Default: skip_cleanup=False, validate_response=True
        # No need to assert ID/email. The fixture already does it: customer_helper.assert_valid_customer_response()

        email = customer["email"]
        customer_id = customer["id"]

        # 📦 Return identifiers and metadata (for teardown registration). Email: used as identifier to later validate
        # that customer exists. Metadata (like ID) is optional, but useful for debugging or future logging.
        return email, {"id": customer_id, "resource_type": "customers"}

    # ------------------------
    # ✅ Validate function
    # ------------------------
    # It encapsulates/summarize the logic to check that the created customer is visible via GET /customers and matches
    # DB (via DAO).
    def validate_fn(email):
        """
        Validates that the customer:
        - API GET /customers can find the customer.
        - The response is valid JSON/schema.
        - The data matches what’s stored in the DB.
        Args:
            email (str): Unique identifier used to search for the customer
        """
        customer_helper.validate_customer_exists_and_matches_api(email=email, dao=customers_dao)

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
    This test creates a customer using the minimum valid payload (email + password only)
    and validates API + DB integrity.

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
    customer_helper.validate_customer_exists_and_matches_api(email=email, dao=customers_dao)
    logger.info("🎯 Full validation complete for customer ID: %r", customer_id)


# below partial payload perhaps can be moved to customer's data file????
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
    Validates:
    - Customer created via factory fixture with randomized address data
    - Parameterized address formats
    - API response structure (schema validation) after POST /customers
    - Critical fields (`id`, `email`, etc.) are present and correct
    - Customer appears in GET /customers endpoint and matches DB
    - API response matches DB record
    - Logging and traceability (via logger + correlation_id where applicable)
    - Cleanup is automatic unless explicitly skipped
    - Generates unique correlation ID for logs for better traceability
    """

    # ✅ Create customer using fixture factory
    logger.debug(f"📦 Billing data: {billing}")
    logger.debug(f"📦 Shipping data: {shipping}")
    # # 🧠 Optional: Pretty Print for Readability
    # # If the billing/shipping data is large, consider formatting them with json.dumps():
    # import json
    # logger.debug(f"📦 Billing data: {json.dumps(billing, indent=2)}")
    # # This makes the logs more readable, especially for nested or complex payloads

    # -------------------------------------------
    # ✅ Create customer via fixture factory
    # -------------------------------------------
    logger.info("🛠 Creating a test customer via factory fixture with parameterized billing and shipping addresses")
    # To keep the customer in the DB (i.e., skip deletion), pass: customer = create_customer_for_test(skip_cleanup=True)
    customer = create_valid_customer(billing=billing, shipping=shipping)
    customer_id = customer["id"]
    customer_email = customer["email"]

    # ---------------------------------------------------------------------------------------------------------
    # 🔍 Confirm customer exists in DB and API GET response matches DB.
    # 🧩 Schema Validation (it checks that the GET response is valid).
    # ---------------------------------------------------------------------------------------------------------
    customer_helper.validate_customer_exists_and_matches_api(email=customer_email, dao=customers_dao)
    logger.info("🎯 Full validation complete for customer ID: %r", customer_id)


@pytest.mark.negative_test
@pytest.mark.tcid15
@pytest.mark.parametrize("payload, expected_status_code", INVALID_EMAIL_PAYLOADS)
def test_create_customer_email_field_validation(customer_helper, customers_dao, raw_customer_api, payload,
                                                expected_status_code):
    """
    ❌ Negative Test: Validate WooCommerce customer creation with malformed or missing email field.
    This version does NOT use fixture create_valid_customer, because we expect 400 responses for invalid payloads.

    This test verifies:
    - ❌ Invalid/malformed or missing emails result in HTTP 400
    - 📋 Error responses conform to expected schema
    - ⚠️ Error codes and messages are present and not empty
    - ✅ If no error is expected, customer response matches schema and input

    ✅ Best Practice Approach (Recommended for negative test)
    🔁 DO NOT use create_valid_customer for negative tests where:
       - You expect a 400 (or similar non-2xx),
       - You're passing deliberately malformed data (e.g., "not-an-email", missing email),
       - You don’t want any auto-generated fallback like email or password.
    Instead, for negative tests like this, follow the same model as your test_update_customer_invalid_inputs().
    The test_update_customer_invalid_inputs() already follows best practice for negative testing:
    it calls the lower-level requests_utility directly and explicitly validates the structure of an expected error
    response.

    Args:
        customers_dao: Fixture providing customer DAO.
        customer_helper: Fixture providing customer API helper.
        raw_customer_api (Callable): .Fixture providing low-level access t tests that need to inspect raw responses.
        payload (dict): Test input payload with malformed or missing email/password fields.
        expected_status_code (int): Expected HTTP response code.
    """

    # -------------------------------------------
    # 📦 Extract email/password from payload
    # -------------------------------------------
    email = payload.get("email")

    logger.info(f"🧪 Testing customer creation with invalid email: '{email}'")

    # -------------------------------------------
    # 📞 Call customer creation using factory method
    # -------------------------------------------

    http_response = raw_customer_api.post(endpoint="customers", payload=payload)

    response = http_response.json

    assert http_response.status_code == expected_status_code

    # --------------------------------------------
    # 📋 Validate error schema and contents
    # --------------------------------------------
    validate_customer_error_response_schema(response)

    logger.info(f"✅ Proper error returned for payload: {payload} → {response['code']}: {response['message']}")


@pytest.mark.negative_test
@pytest.mark.tcid16
def test_create_customer_fail_for_existing_email(create_valid_customer, raw_customer_api, customer_helper,
                                                 customers_dao):
    """
    ❌ Negative Test: Attempt to create a customer with an email that already exists.

    Test verifies:
    - HTTP 400 returned for duplicate email
    - Error code: 'registration-error-email-exists'
    - The Error message is informative and matches expected

    Args:
        create_valid_customer (Callable): Factory fixture to create valid WooCommerce customers
        raw_customer_api (RawAPIClient): Fixture for low-level API calls used for negative testing
        customer_helper: Provides customer's helper
        customers_dao: Provides customer's DAOs

    🔧 Behind the scenes:
    - It uses a factory fixture: `create_valid_customer(...)` which calls:
        - `customer_helper.create_customer(...)` → handles API POST
        - Automatically validates:
            - Response schema via `validate_customer_response_schema(...)`
            - Critical fields via `assert_valid_customer_response(...) such as email and ID`
            - Registers the customer for teardown (unless skip_cleanup=True)
    - Returns full customer dict (e.g., `{"id": 123, "email": ..., "username": ...}`)

    """

    # -------------------------------
    #  ✅ Create customer via fixture factory
    # -------------------------------
    logger.info("🛠 Creating a negative test when it is expected to fail for existing email.")
    existing_customer = create_valid_customer()  # Default: skip_cleanup=False, validate_response=True
    # To keep the customer in the DB (i.e., skip deletion), pass: customer = create_customer_for_test(skip_cleanup=True)

    email = existing_customer['email']

    # -------------------------------
    #  ✅ Re-create customer via fixture factory
    # -------------------------------
    logger.info(f"⚠️ Attempt to re-create the customer using existing email: {email}")

    payload = {
        "email": email,
        "password": "Password1"  # must pass something, doesn't need to match
    }

    # -------------------------------------------
    # 📞 Call customer creation using factory method
    # -------------------------------------------
    http_response = raw_customer_api.post(
        endpoint="customers",
        payload=payload,  # or inline--> payload = {"email": "invalid", "password": "Password1"}
    )

    response = http_response.json

    # ✅ Transport validation (shared validator responsibility)
    assert_status_code(http_response, 400)  # Benefits: Standardized across ALL tests and Better
    # error messages: ❌ Expected status 400, got 500. URL: /customers

    # The following is a bad practice to do it directly here --> assert http_response.status_code == 400
    # The problems with that: No URL in error, harder debugging, Inconsistent across tests, Junior engineers will
    # copy/paste different styles, Harder to improve globally later.

    # ⚖️ When to Use Each Style
    # ✅ Use assert_status_code(...) (DEFAULT)
    # ✔ Negative tests
    # ✔ Contract tests
    # ✔ Raw API tests
    # ✔ Anywhere using HttpResponse

    # 🟡 Use raw assert ONLY when:
    # ✔ One-off debugging
    # ✔ Temporary test
    # ✔ Extremely simple cases

    # ✅ Business validation (customer's validator responsibility)
    assert_customer_creation_failed(response)

    logger.info("🧪 Validating response for duplicate email error...")

    # ---------------------------------------------------------------------------------------------------------
    # 🔍 Confirm customer exists in DB and API GET response matches DB.
    # 🧩 Schema Validation (it checks that the GET response is valid).
    # ---------------------------------------------------------------------------------------------------------
    # The method "validate_customer_uniqueness_and_consistency" ensures only 1 exists and detects backend bugs
    customer_helper.validate_customer_uniqueness_and_consistency(email, customers_dao)

    # --------------------------------------------
    # 📋 Validate error schema and contents
    # --------------------------------------------
    validate_customer_error_response_schema(response)
    logger.info(f"✅ Proper error returned for payload: {payload} → {response['code']}: {response['message']}")

# # Calls:
# # test
# #  └─ create_valid_customer()
# #      └─ CustomersHelper.create_customer()
# #          └─ RequestUtility.post("customers")
# #              └─ _build_url()
# #                  └─ POST /wc/v3/customers
# #                      └─ WooCommerce API
# #                          └─ 201 + { id: ... }

# # Test
# #   ↓
# # Helper (customers)
# #   ↓   "customers"
# # RequestUtility
# #   ↓   base_url + endpoint
# # HTTP request


# # High-Level Flow (One Sentence)

# # Pytest discovers the test → loads conftests by directory ancestry → builds fixtures → injects RequestUtility →
# # helper builds endpoint → RequestUtility builds URL → HTTP POST → response validated → test asserts


# # 🧠 FULL CONSOLIDATED CALL STACK (ONE DIAGRAM)
# # pytest
# #  │
# #  ▼
# # test_create_customer.py
# #  │
# #  ▼
# # create_valid_customer (fixture)
# #  │
# #  ▼
# # Validators (customer_schema_validator + customer_assertions + base validator)
# #  │
# #  ▼
# # CustomersHelper.create_customer()
# #  │
# #  ▼
# # CustomersApi()
# #  │
# #  ▼
# # RequestUtility.post()
# #  │
# #  ▼
# # _request_with_backoff()
# #  │
# #  ▼
# # _request()
# #  │
# #  ▼
# # _build_url("customers")
# #  │
# #  ▼
# # HTTP POST /wp-json/wc/v3/customers
# #  │
# #  ▼
# # _handle_response()
# #  │
# #  ▼
# # return customer dict
# #  │
# #  ▼
# # assert_valid_customer_response()
# #  │
# #  ▼
# # TEST ASSERTS ✅
#

# 🔄 Your NEW flow (after refactor)
# ✅ Transport layer (always the same)
# test / helper / raw_api
#         ↓
# RequestUtility.post()
#         ↓
# _request_with_backoff()
#         ↓
# HttpClient.request()  → returns requests.Response
#         ↓
# HttpResponse.from_requests()
#         ↓
# 👉 returns HttpResponse
#
# ✔ This happens for EVERY call
# ✔ No exceptions
# ✔ No "sometimes dict / sometimes response"


# HttpClient (LOW LEVEL)
#     ↓
# RequestUtility (ORCHESTRATOR)
#     ↓
# CustomersApi (ENDPOINTS ONLY)
#     ↓
# CustomersHelper (PAYLOAD + FLOW)
#     ↓
# Validators (ASSERTIONS)


# RequestUtility → HttpResponse ✅
# API → extracts .json ✅
# Helper → dict ✅
# Validator → dict ✅
# Tests → unchanged ✅


# 👉 Helpers return dict
# 👉 API / RequestUtility return HttpResponse


# 🚀 PATTERN YOU SHOULD FOLLOW EVERYWHERE
# ✅ Positive test
# customer = customer_helper.create_customer(...)
# assert_valid_customer_response(customer)

# ✅ Negative test
# response = customer_helper.call_get_customer_by_id(...)
# assert_customer_not_found_error(response)

# ✅ Raw API (only when needed)
# http_response = raw_customer_api.get(...)
# assert http_response.status_code == 404

# “Enterprise companies — where do they validate status?”

# 👉 Answer:

# ✔ Tests OR validators
# ❌ NEVER in HTTP client


# 🧠 Final mental model (SUPER IMPORTANT)
# 🔵 Transport layer (HttpResponse)
# status_code
# headers
# timing
# raw info

# 🟢 Business layer (dict)
# id
# email
# error code
# schema


# Do we use HttpResponse only for negative tests?
# ❌ NO

# 👉 It is ALWAYS used internally
# 👉 But:

# | Case    | You see      |
# | ------- | ------------ |
# | Helper  | dict         |
# | Raw API | HttpResponse |

# 🧠 KEY DISTINCTION (VERY IMPORTANT)
# | Concept                 | Where it happens                 |
# | ----------------------- | -------------------------------- |
# | ✅ Send JSON (request)   | HttpClient (`json=payload`)      |
# | ✅ Parse JSON (response) | HttpResponse (`response.json()`) |

# ✅ FINAL ARCHITECTURE (LOCK THIS IN)
# 🧱 Transport layer (RequestUtility)
#
# ✔ returns → HttpResponse
#
# 🌐 API layer (CustomersApi)
#
# ✔ returns → HttpResponse
# ❌ NEVER .json


# 🧠 Helper layer (CustomersHelper)

# ✔ returns → dict
# ✔ does .json extraction
# ✔ handles negative exceptions

# 🧪 Tests
# Positive → use helper (dict)
# Negative → use raw API (HttpResponse)
# 📌 RULE (VERY IMPORTANT)
# 👉 API = transport object
# 👉 Helper = business-friendly object


# 🧠 MENTAL MODEL (SUPER IMPORTANT)
# 🔵 Positive flow
# Test
#   ↓
# Helper
#   ↓
# API
#   ↓
# RequestUtility
#   ↓
# HttpResponse
#   ↓
# Helper extracts .json ✅
#   ↓
# Test receives dict ✅

# 🔴 Negative flow
# Test
#   ↓
# raw_customer_api
#   ↓
# API
#   ↓
# RequestUtility
#   ↓
# HttpResponse ✅
#   ↓
# Test asserts status_code + json


# 🧠 THE REAL RULE (FINAL, NO MORE CONFUSION)
# Let’s lock this 100% clearly:
# | Layer          | What it RETURNS            | What it DOES              |
# | -------------- | -------------------------- | ------------------------- |
# | RequestUtility | HttpResponse               | transport only            |
# | API            | HttpResponse               | endpoint definition only  |
# | Helper         | dict (response.json)       | business + orchestration  |
# | Validators     | dict                       | schema + assertions       |
# | Tests          | mix (dict OR HttpResponse) | depending on type of test |

