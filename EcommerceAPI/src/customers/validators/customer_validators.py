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
    assert_valid_customer_response → structure
    _find_customer_by_email → locating entity
    assert_valid_customer_in_api → API validation
    assert_customer_integrity
    assert_customer_creation_failed
    assert_customer_not_found_error
    assert_customer_retrieved_successfully
    assert_customer_exists_and_matches_api
"""

from typing import List, Dict, Any
import logging

from EcommerceAPI.src.core.http_response import HttpResponse
from EcommerceAPI.src.customers.schemas.customer_schema_validator import validate_customer_response_schema
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


def _find_customer_by_email(
    customers: List[Dict[str, Any]],
    email: str
) -> CustomerModel:
    """
    Internal helper that finds a customer by email and validates structure.

    This function centralizes the logic for locating a customer
    in an API response and converting it into a validated Pydantic model.

    It guarantees:
        - Exactly one customer exists
        - Structure is valid
    """

    matches = [c for c in customers if c.get("email") == email]

    assert matches, f"❌ No customer found for email: {email}"

    assert len(matches) == 1, (
        f"❌ Expected 1 customer, found {len(matches)} for {email}"
    )

    raw_customer = matches[0]

    return assert_valid_customer_response(raw_customer)


# ------------------------------------------------------------------
# 🧪 API RESPONSE VALIDATION (STRUCTURE + BUSINESS)
# ------------------------------------------------------------------
def assert_valid_customer_in_api(
    customers: List[Dict[str, Any]],
    email: str
) -> CustomerModel:

    customer = _find_customer_by_email(customers, email)

    assert customer.email == email

    logger.info(
        "✅ Assertion passed: Customer exists in API response "
        "(id=%s, email=%s)",
        customer.id,
        customer.email
    )

    return customer


def assert_customer_integrity(
    helper,
    dao,
    email: str
) -> CustomerModel:
    """
    High-level validator that verifies customer integrity
    across API and database.

    This validator performs the full validation pipeline:

        1️⃣ Fetch customer via API
        2️⃣ Validate API response structure + business logic
        3️⃣ Fetch DB record
        4️⃣ Validate API ↔ DB consistency

    Args:
        helper:
            CustomersHelper instance

        dao:
            CustomersDao instance

        email (str):
            Customer email used as identifier

    Returns:
        CustomerModel:
            Validated customer object

    Example usage in tests:

        assert_customer_integrity(customer_helper, customers_dao, email)
    """

    # -------------------------------------------------------
    # 🌐 API FETCH
    # -------------------------------------------------------
    customers = helper.list_customers_paginated(email=email)

    # -------------------------------------------------------
    # API VALIDATION
    # -------------------------------------------------------
    customer = assert_valid_customer_in_api(customers, email)

    # -------------------------------------------------------
    # DB FETCH
    # -------------------------------------------------------
    db_customer = dao.get_customer_by_email(email)

    # -------------------------------------------------------
    # DB VALIDATION
    # -------------------------------------------------------
    assert_customer_matches_db(customer, db_customer)

    return customer


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


def assert_customer_retrieved_successfully(response: HttpResponse) -> dict:  # The response parameter is expected to be
    # an instance of HttpResponse
    """
    A thin domain-level assertion
    """
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )

    # Extract JSON to validate body
    data = response.json

    # later → replace with Pydantic
    validate_customer_response_schema(data)

    return data


def assert_customer_exists_and_matches_api(
        customers: List[Dict[str, Any]],
        email: str,
        db_customer: Dict[str, Any],
) -> None:
    """
    Validate that a customer exists in the API response
    and matches the corresponding database record.

    This validator performs two layers of checks:

    1️⃣ API VALIDATION
        - Ensures the customer exists in the API response
        - Validates structure using Pydantic
        - Validates basic business rules

    2️⃣ DATABASE VALIDATION
        - Confirms API response matches the database record

    This function is commonly used in integration and
    end-to-end tests where both API and DB correctness
    must be verified.

    Args:
        customers (List[Dict[str, Any]]):
            List of customers returned by the API.

        email (str):
            Expected customer email.

        db_customer (Dict[str, Any]):
            Database record retrieved via DAO.

    Raises:
        AssertionError:
            If API data or DB data are inconsistent.
    """

    logger.debug("⚙️ Validating existence of customer by email: %s", email)

    # -------------------------------------------------------
    # 🌐 API VALIDATION
    # -------------------------------------------------------
    # This ensures the customer exists and structure is valid.
    customer = assert_valid_customer_in_api(customers, email)

    logger.info(
        "✅ Assertion passed: Customer found via API (id=%s)",
        customer.id
    )

    # -------------------------------------------------------
    # 🗄️ DB VALIDATION
    # -------------------------------------------------------
    # Convert model to dictionary only if needed by DB validator.
    assert_customer_matches_db(customer, db_customer)

    logger.info(
        "✅ Assertion passed: Customer record validated in DB for ID=%s",
        db_customer["ID"]
    )
