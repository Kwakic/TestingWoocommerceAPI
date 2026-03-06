import pytest
import logging

from jsonschema import validate
from json import loads

from tests.shared.schemas.customer import error_schema

from EcommerceAPI.src.customers.validators.customer_validators import (assert_customer_not_found_error,
                                                                       assert_customer_retrieved_successfully,
                                                                       assert_customer_identity,
                                                                       assert_single_customer_by_email,
                                                                       assert_valid_customer_response)

logger = logging.getLogger(__name__)
#  logger.setLevel(logging.DEBUG)  # already set in pytest.ini

pytestmark = [pytest.mark.customers, pytest.mark.regresion]


@pytest.mark.customers
@pytest.mark.tcid13
def test_get_customer_by_email(customer_helper, customers_dao, create_valid_customer):
    """
    Verify that a created customer can be retrieved using the query endpoint:
        GET /customers?email={email}

    This test validates the full retrieval workflow across multiple layers:

    1️⃣ Customer creation (handled by fixture)
    2️⃣ Transport layer correctness (HTTP status code)
    3️⃣ API response correctness
    4️⃣ Identity validation (returned customer matches created one)
    5️⃣ API ↔ DB consistency validation

    IMPORTANT:
    - The fixture `create_valid_customer()` already validates the POST response
      (structure + critical fields) and registers cleanup.
    - Therefore, this test focuses ONLY on validating the GET endpoint behavior.

    Validation coverage:
        ✔ Transport validation (status_code)
        ✔ Dataset validation (list endpoint)
        ✔ Identity validation
        ✔ API ↔ DB consistency
    """

    # -------------------------------------------
    # 🛠 Step 1 — Create a valid customer
    # -------------------------------------------
    logger.info("🛠 Creating a test customer via factory fixture.")

    # Fixture handles:
    #   - POST /customers
    #   - Pydantic validation
    #   - automatic cleanup registration
    customer = create_valid_customer()

    customer_id = customer["id"]
    email = customer["email"]

    # -------------------------------------------
    # 🔎 Step 2 — Retrieve customer via email filter
    # -------------------------------------------
    logger.info("🔎 Fetching customer by email: %s", email)

    # return_http_response=True allows us to validate transport layer
    response = customer_helper.get_customer_by_email(
        email=email,
        return_http_response=True
    )

    # -------------------------------------------
    # 🚦 Step 3 — Transport validation (FAIL FAST)
    # -------------------------------------------
    # Enterprise rule:
    # Tests validate status codes explicitly.
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )

    # -------------------------------------------
    # 📦 Step 4 — Extract dataset
    # -------------------------------------------
    # This endpoint returns a LIST of customers.
    customers = response.json

    # -------------------------------------------
    # 🔍 Step 5 — Extract the correct customer
    # -------------------------------------------
    # Since the endpoint returns a dataset, we enforce that exactly ONE customer exists for the queried email.
    # Extract correct customer from dataset (dict)
    customer_model = assert_single_customer_by_email(
        customers,
        email
    )
    # -------------------------------------------
    # 🧠 Step 6 — Identity validation
    # -------------------------------------------
    # Convert raw dict → validated CustomerModel
    # Ensure the retrieved customer matches the one we created.
    assert_customer_identity(customer_model, customer_id, email)

    logger.info(
        "✅ Fetched customer matches created one: ID=%s, Email=%s",
        customer_id,
        email
    )

    # -------------------------------------------
    # 🗄 Step 7 — API vs DB consistency validation
    # -------------------------------------------
    # Helper orchestrates:
    #   - API fetch
    #   - DB lookup
    #   - API ↔ DB validation
    customer_helper.assert_customer_exists_and_matches_db(
        email,
        customers_dao
    )

    logger.info("🎯 Full validation complete for customer ID: %r", customer_id)


@pytest.mark.tcid14
def test_get_customer_by_id(customer_helper, customers_dao, create_valid_customer):
    """
    Validate that a created customer can be retrieved by ID (GET /customers/{id}).

    What this test validates:
        - Customer can be fetched via API after creation
        - Transport layer status code is correct
        - API response structure is valid (Pydantic validation)
        - Returned customer matches the created one
        - API data is consistent with DB

    NOTE:
        The fixture `create_valid_customer()` already validates the POST response.
        Therefore, this test only validates the GET endpoint behavior.
    """

    # -------------------------------------------
    # 🛠 Step 1 — Create a valid customer
    # -------------------------------------------
    logger.info("🛠 Creating a test customer via factory fixture.")

    # The fixture already validates POST response and registers cleanup.
    customer = create_valid_customer()

    customer_id = customer["id"]
    email = customer["email"]

    # -------------------------------------------
    # 🔎 Step 2 — Retrieve customer via API
    # -------------------------------------------
    logger.info(f"🔎 Fetching customer by ID: {customer_id}")

    # return_http_response=True gives us the HttpResponse wrapper which allows status code validation and debugging.
    response = customer_helper.get_customer_by_id(
        customer_id,
        return_http_response=True
    )

    # -------------------------------------------
    # 🚦 Step 3 — Transport + structure validation
    # -------------------------------------------
    # This validator performs:
    #   1️⃣ status_code validation (fail-fast)
    #   2️⃣ Pydantic structure validation
    #   3️⃣ returns a typed CustomerModel
    customer_model = assert_customer_retrieved_successfully(response)

    # -------------------------------------------
    # 🔍 Step 4 — Business validation
    # -------------------------------------------
    # Ensure we retrieved the correct customer
    assert_customer_identity(customer_model, customer_id, email)

    logger.info(
        "✅ Fetched customer matches created one: ID=%s, Email=%s",
        customer_id,
        email
    )
    # -------------------------------------------
    # 🗄 Step 5 — API vs DB consistency validation
    # -------------------------------------------
    # Helper orchestrates:
    #   - GET /customers list
    #   - DB lookup via DAO
    #   - API vs DB validation
    customer_helper.assert_customer_exists_and_matches_db(
        email,
        customers_dao
    )

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
