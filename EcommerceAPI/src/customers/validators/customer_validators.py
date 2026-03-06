# EcommerceAPI/src/validators/customers/customer_validators.py
# business validation
"""
Customer Validation Layer

This module contains domain-level validators for the Customers API.

Responsibilities
----------------
• Validate API response structure using Pydantic
• Validate dataset responses (list endpoints)
• Validate business rules
• Validate API + database consistency

Important design rule:
Validators ONLY validate data.

They must NOT:
    - call APIs
    - query databases
    - orchestrate workflows

Data fetching is handled by:
    Tests or Helpers.

Architecture
------------
TEST / HELPER
      ↓
API CLIENT
      ↓
HttpResponse
      ↓
VALIDATORS
      ↓
Pydantic Models
      ↓
DB Validators

assert_valid_customer_response → Structure validation (STRUCTURE)
assert_single_customer_by_email → API validation (DATASET)
assert_customer_creation_failed → error validation
assert_customer_not_found_error → error validation
assert_customer_retrieved_successfully → Transport validation (TRANSPORT)
assert_customer_exists_and_matches_api → API + DB validation (INTEGRATION)
assert_customer_identity() → Identity validation (BUSINESS)

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
    Validate the structure of a customer API response.

    This function performs **structure validation** using the Pydantic
    `CustomerModel`.

    Purpose:
        - Ensure required fields exist
        - Ensure correct field types
        - Validate email format

    Args:
        customer:
            Raw customer dictionary returned by the API.

    Returns:
        CustomerModel:
            Validated customer object.

    Raises:
        ValidationError:
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
    Validate that exactly ONE customer exists for a given email in a dataset response (list endpoint).

    Typical use cases:
        - GET /customers
        - GET /customers?email=
        - paginated dataset responses

    This validator performs:
        1. Filter dataset by email
        2. Ensure exactly one match exists
        3. Validate structure using Pydantic

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

    Expected response structure:
    {
        "code": "...",
        "message": "...",
        "data": {"status": 400}
    }
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
    Validate response for a non-existing customer.

    Expected:
        code: wc_user_invalid_id
        message: "Invalid user ID."
        status: 404
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

    Steps:
        1. Validate HTTP status code
        2. Validate response structure using Pydantic

    Returns:
        CustomerModel
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
    Validate that the returned customer matches the expected identity.

    Used when a single customer object should be returned by the API.

    This validator performs two layers of validation:

    1️⃣ API VALIDATION
        - Ensures exactly one customer exists in the dataset
        - Validates structure via Pydantic
        - Returns a typed CustomerModel

    2️⃣ DATABASE VALIDATION
        - Confirms API data matches the database record

    This validator is commonly used in integration and end-to-end tests where both API and DB correctness
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


# -------------------------------------------------------
# 🧠 BUSINESS VALIDATION
# -------------------------------------------------------
def assert_customer_identity(
    customer: CustomerModel,
    expected_id: int,
    expected_email: str
) -> None:
    """
    Validate that the returned customer matches the expected identity.

    This validator ensures that the API returned the correct resource.

    Typical use cases:
        - GET /customers/{id}
        - GET /customers?email=
        - responses where a SINGLE customer object is expected

    Why this validator exists:
        - Removes duplicated assertions across tests
        - Improves readability for junior engineers
        - Provides consistent error messages
        - Works with validated Pydantic models

    Args:
        customer (CustomerModel):
            Validated customer object returned by API.

        expected_id (int):
            ID of the customer that should have been returned.

        expected_email (str):
            Email of the customer that should have been returned.

    Raises:
        AssertionError:
            If returned customer does not match expected identity.
    """

    # -------------------------------------------------------
    # Validate customer ID
    # -------------------------------------------------------
    assert customer.id == expected_id, (
        f"❌ Customer ID mismatch: expected {expected_id}, got {customer.id}"
    )

    # -------------------------------------------------------
    # Validate customer email
    # -------------------------------------------------------
    assert customer.email == expected_email, (
        f"❌ Customer email mismatch: expected {expected_email}, got {customer.email}"
    )

    logger.info(
        "✅ Customer identity verified (id=%s, email=%s)",
        customer.id,
        customer.email
    )
