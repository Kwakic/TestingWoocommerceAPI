# EcommerceAPI/src/validators/customers/customer_validators.py
# business validation
"""
MAIN VALIDATION LAYER (CUSTOMERS)

This module is the SINGLE ENTRY POINT for all customer validations (business rules).

🎯 Purpose:
- Provide clear, readable, domain-level validators
- Combine structure + business validation safely
- Hide generic/base validators from users

🧠 Design Rules:
- ALWAYS validate structure first
- THEN validate business logic
- Use strict access (obj["field"]) after structure validation
- Keep functions small, explicit, and easy to use

✔ Used by:
    - Helpers ✅
    - Tests (optional) ✅

API + business:
    assert_valid_customer_response → Structure validation
    assert_single_customer_by_email → API validation
    assert_customer_creation_failed → error validation
    assert_customer_not_found_error → error validation
    assert_customer_retrieved_successfully → Transport validation
    assert_customer_exists_and_matches_api → API + DB validation (low level)
    assert_customer_identity() → Identity validation

------------------------------------------------------------------
In enterprise test frameworks the usual rule is:
    - Validators should NOT fetch data.
    - Validators should only validate.
------------------------------------------------------------------

Tests / helpers responsible for:
    fetching
    orchestration
    workflow

Validators responsible for:
    data validation
    business rules
    consistency checks
------------------------------------------------------------------

The correct architecture is:

    TEST / HELPER
         ↓
    FETCH DATA (API / DAO)
         ↓
    VALIDATORS
         ↓
    SCHEMAS (Pydantic)

------------------------------------------------------------------

Flow:

    TEST
     ↓
    HELPER
     ↓
    API CLIENT
     ↓
    HttpResponse
     ↓
    VALIDATORS
     ↓
    PYDANTIC
     ↓
    DB VALIDATORS

------------------------------------------------------------------
The validator file should contain:

    STRUCTURE
    ---------
    assert_valid_customer_response

    API VALIDATION
    --------------
    assert_valid_customer_in_api
    assert_customer_exists_and_matches_api

    ERROR VALIDATION
    ----------------
    assert_customer_creation_failed
    assert_customer_not_found_error
    assert_customer_retrieved_successfully

------------------------------------------------------------------

POST /customers            → schema validation
GET /customers/{id}        → schema validation
GET /customers?filters     → identity + DB validation

That is exactly what enterprise QA frameworks do.

------------------------------------------------------------------

Tests should NOT orchestrate API + DB + validators manually.
Helpers should provide a single verification entrypoint.

The test should not orchestrate DB + API together.
Helper should e.g. def assert_customer_exists_and_matches_db(self, email: str, dao)
------------------------------------------------------------------
Your framework becomes:

Transport validation
    ↓
HttpResponse

Validator layer
    ↓
assert_customer_retrieved_successfully()

Structure validation
    ↓
CustomerModel (Pydantic)

Business validation
    ↓
assert_customer_identity()

Integration validation
    ↓
assert_customer_exists_and_matches_db()

------------------------------------------------------------------

"""

from typing import List, Dict, Any
import logging

from EcommerceAPI.src.core.http_response import HttpResponse
from EcommerceAPI.src.customers.validators.customer_db_validators import (
    assert_customer_matches_db
)

from EcommerceAPI.src.customers.schemas.customer_model import CustomerModel

logger = logging.getLogger(__name__)


# -------------------------------------------------------
# 🧱 STRUCTURE VALIDATION
# -------------------------------------------------------
def assert_valid_customer_response(customer: Dict[str, Any]) -> CustomerModel:
    """
    Validate the structure of a customer API response using Pydantic.

    This function represents the **STRUCTURE VALIDATION LAYER**.

    It ensures that:
        - The input is a valid customer object
        - Required fields exist
        - Field types are correct
        - Email format is valid

    Internally it uses the Pydantic model `CustomerModel`.

    Why this function exists:
        - Tests and helpers should NOT instantiate Pydantic models directly
        - All validation should pass through the assertion layer
        - This keeps the framework consistent and junior-friendly

    Args:
        customer (Dict[str, Any]):
            Raw customer dictionary returned by the API.

    Returns:
        CustomerModel:
            Validated and typed customer object.

            Example:
                customer_model.id
                customer_model.email
                customer_model.username

    Raises:
        pydantic.ValidationError:
            If the response structure is invalid.
    """

    # Pydantic parses and validates the dictionary.
    # If anything is wrong (missing fields, wrong types, invalid email) Pydantic raises a ValidationError immediately.
    customer_model = CustomerModel(**customer)  # This is a dictionary unpacking. Take all key-value pairs from the
    # customer dict and pass them as named arguments.

    logger.info(
        "✅ Customer structure valid: id=%s, email=%s",
        customer_model.id,
        customer_model.email
    )

    # -------------------------------------------------------
    # 📦 Return typed object
    # -------------------------------------------------------
    # Returning the model allows downstream assertions to safely access fields using dot notation.
    return customer_model  # example: CustomerModel(id=1452, email='testuser_cfitmuyfvq@supersqa.com',
    # username='testuser_cfitmuyfvq')


def assert_single_customer_by_email(
    customers: List[Dict[str, Any]],
    email: str
) -> CustomerModel:
    """
    Validate that exactly ONE customer exists for a given email
    in a dataset response (list endpoint).

    Typical use cases:
        - GET /customers
        - GET /customers?email=
        - paginated dataset responses

    This validator performs:

        1️⃣ Dataset filtering
        2️⃣ Uniqueness validation
        3️⃣ Structure validation (Pydantic)

    Returns:
        CustomerModel (validated object)
    """

    matches = [c for c in customers if c.get("email") == email]

    assert len(matches) == 1, (
        f"❌ Expected 1 customer for {email}, found {len(matches)}"
    )

    # Validate structure via Pydantic
    customer_model = assert_valid_customer_response(matches[0])

    logger.info(
        "✅ Customer found in dataset: id=%s email=%s",
        customer_model.id,
        customer_model.email
    )

    return customer_model


def assert_customer_creation_failed(response: dict):
    """
    Validate customer creation failure (business + contract level).

    IMPORTANT:
    - This function expects a parsed JSON dict (NOT HttpResponse)
    - Status code must be validated BEFORE calling this function

    Validates:
        - error code
        - error message
        - response data structure
    """
    assert response['data'] == {'status': 400}, (f"Invalid data. Current: {response['data']}, "
                                                 f"Expected: {{'status': 400}}"
                                                 )

    assert response['code'], "❌ Error 'code' should not be empty"

    assert response['code'] == "registration-error-email-exists", (
        f"Invalid Error code. Current: '{response['code']}', "
        f"Expected: 'registration-error-email-exists'"
    )

    assert response['message'], "❌ Error 'message' should not be empty"
    assert "An account is already registered" in str(response['message'])


def assert_customer_not_found_error(response):
    """
    It validates:
        - data: status 404
        - code
        - error message

    :param response: customer response
    """

    assert response['code'] == "wc_user_invalid_id", (f"Invalid Error code. Current: '{response['code']}', "
                                                      f"Expected: 'wc_user_invalid_id' ")

    assert response['message'], "❌ Error 'message' should not be empty"

    assert response['message'] == "Invalid user ID.", (f"Invalid Error message. Current: '{response['message']}', "
                                                       f"Expected: 'Invalid user ID'")

    assert response['data'] == {'status': 404}, (f"Invalid data. Current: {response['data']}, "
                                                 f"Expected: {{'status': 404}}")


def assert_customer_retrieved_successfully(response: HttpResponse) -> CustomerModel:
    """
    Validate successful GET /customers/{id} response.

    Flow:
        1️⃣ Transport validation
        2️⃣ Structure validation (Pydantic)
        3️⃣ Return typed model
    """

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )

    data = response.json

    # 🔒 Structure validation via Pydantic
    customer_model = assert_valid_customer_response(data)

    return customer_model


def assert_customer_exists_and_matches_api(
        customers: List[Dict[str, Any]],
        email: str,
        db_customer: Dict[str, Any],
) -> None:
    """
    Validate that a customer exists in the API response and that
    the returned data matches the database record.

    This validator performs two layers of validation:

    1️⃣ API VALIDATION
        - Ensures exactly one customer exists in the dataset
        - Validates structure via Pydantic
        - Returns a typed CustomerModel

    2️⃣ DATABASE VALIDATION
        - Confirms API data matches the database record

    This validator is commonly used in integration and
    end-to-end tests where both API and DB correctness
    must be verified.

    Args:
        customers:
            Dataset returned by API (GET /customers).

        email:
            Expected customer email.

        db_customer:
            Database record retrieved via DAO.

    Raises:
        AssertionError:
            If API data or DB data are inconsistent.
    """

    logger.debug("⚙️ Validating existence of customer by email: %s", email)

    # -------------------------------------------------------
    # 1️⃣ DATASET VALIDATION
    # -------------------------------------------------------
    # Ensure exactly one customer exists in API dataset and validate structure using Pydantic.
    customer = assert_single_customer_by_email(customers, email)

    logger.info(
        "✅ Customer found in API response (id=%s, email=%s)",
        customer.id,
        customer.email
    )

    # -------------------------------------------------------
    # 2️⃣ DATABASE VALIDATION
    # -------------------------------------------------------
    # Compare API response with database record
    assert_customer_matches_db(customer, db_customer)

    logger.info(
        "✅ Customer matches database record (ID=%s)",
        db_customer["ID"]
    )


def assert_customer_identity(
    customer: CustomerModel,
    expected_id: int,
    expected_email: str
) -> None:
    """
    Validate that returned customer matches expected identity.

    Works with Pydantic CustomerModel.
    """

    assert customer.id == expected_id, (
        f"❌ Mismatched ID: expected {expected_id}, got {customer.id}"
    )

    assert customer.email == expected_email, (
        f"❌ Mismatched email: expected {expected_email}, got {customer.email}"
    )
