# EcommerceAPI/src/validators/customers/customer_assertions.py
"""
MAIN VALIDATION LAYER (CUSTOMERS)

This module is the SINGLE ENTRY POINT for all customer validations.

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

❗ Do NOT import base_validators in tests
"""

from typing import List, Dict, Any
import logging

from EcommerceAPI.src.core.http_response import HttpResponse
from EcommerceAPI.src.customers.schemas.customer_schema_validator import validate_customer_response_schema

# from EcommerceAPI.src.validators.shared.base_validators import (
#     assert_entity_matches_db,
# )
from EcommerceAPI.src.customers.schemas.customer_model import CustomerModel

logger = logging.getLogger(__name__)


def assert_valid_customer_response(customer: dict) -> None:
    """
    Validate the structure of a customer response using Pydantic.

    This replaces manual structure validation (base_validators).

    Ensures:
        - customer is a dict
        - required fields exist
        - types are correct (id=int, email valid, username exists)

    Raises:
        ValidationError: if structure is invalid
    """

    # 🧱 STRUCTURE VALIDATION (Pydantic)
    validated = CustomerModel(**customer)  # This is a dictionary unpacking. Take all key-value pairs from the
    # customer dict and pass them as named arguments.

    logger.info("✅ Customer structure valid: id=%s, email=%s", validated.id, validated.email)


# ------------------------------------------------------------------
# 🌐 API VALIDATION (STRUCTURE + LIGHT BUSINESS)
# ------------------------------------------------------------------
# Still mostly structural, but includes simple correctness checks like "email matches what we queried".
# ------------------------------------------------------------------
def assert_valid_customer_in_api(customers: List[Dict[str, Any]], email: str) -> CustomerModel:
    """
    Validate that customer exists in API response.

    SAFE:
        - Validates structure (Pydantic)
        - Validates business logic

    Returns:
        CustomerModel (validated + typed object)
    """

    assert customers, f"❌ No customers returned for email: {email}"

    raw_customer = customers[0]

    # 🧱 STRUCTURE (Pydantic)
    customer = CustomerModel(**raw_customer)

    # 🧪 BUSINESS VALIDATION
    assert customer.email == email, (
        f"❌ Email mismatch. Expected: {email}, got: {customer.email}"
    )

    assert customer.id > 0, "❌ Customer ID must be > 0"

    return customer


def assert_customer_uniqueness_and_consistency(
    customers: List[Dict[str, Any]],
    email: str,
    db_customer: Dict[str, Any],
) -> None:
    """
        Validates that:
        - Exactly ONE customer exists with given email (full dataset scan)
        - API response is valid (schema)
        - DB record matches API data
        - Detects duplicates
        - Independent of API correctness (filter in Python)

        You are testing the SYSTEM, not the endpoint:
        - Is my system data correct regardless of API behavior?

        When to use it:
        Deep method (10% of tests)
        🧠 Deep → System correctness
            ✔ duplicate detection
            ✔ regression
            ✔ data integrity checks
            ✔ Migration / cleanup tests
                - import data
                - restore DB
                - run cleanup jobs
            NOTE:
    - Assumes customers list is already fetched (helper responsibility)
    - Structure validation handled inside lower-level assertions
    """

    logger.debug("🟢 Validating uniqueness of customer by email: %s", email)

    # ✅ Uniqueness validation
    customer = assert_single_customer_by_email(customers, email)

    logger.info("✅ Assertion passed: Exactly one customer found in full dataset scan")

    # ✅ DB validation
    assert_valid_customer_matches_db(customer, db_customer)

    logger.info("✅ Assertion passed: Customer record validated in DB for ID=%s", db_customer["ID"])


def assert_customer_exists_and_matches_api(
    customers: List[Dict[str, Any]],
    email: str,
    db_customer: Dict[str, Any],
) -> None:
    """
    Validate:
    - customer exists in API response
    - customer matches DB record

    Use for:
        - fast validation (API filter)
        - integration tests
        - regression checks

    NOTE:
    - Assumes customers list already fetched (helper responsibility)
    """

    logger.debug("⚙️ Validating existence of customer by email: %s", email)

    # ✅ API validation
    customer = assert_valid_customer_in_api(customers, email)

    logger.info("✅ Assertion passed: Customer found via API")

    # ✅ DB validation
    assert_valid_customer_matches_db(customer.model_dump(), db_customer)

    logger.info("✅ Assertion passed: Customer record validated in DB for ID=%s", db_customer["ID"])


# ------------------------------------------------------------------
# 🗄️ DB VALIDATION (PURE BUSINESS LOGIC)
# ------------------------------------------------------------------
# IMPORTANT:
# At this stage we ASSUME structure is already validated.
# So we use strict access (obj["key"]) instead of .get() to enforce contract correctness.
# ------------------------------------------------------------------
def assert_valid_customer_matches_db(customer: Dict[str, Any], db_customer: Dict[str, Any]) -> None:
    """
    Validate API response matches DB record.

    SAFE:
        - Validates structure
        - Delegates business logic to base validator
    """
    # 🧱 STRUCTURE
    assert_valid_customer_response(customer)

    # # 🧪 BUSINESS (reused generic logic)
    # assert_entity_matches_db(
    #     entity=customer,
    #     db_entity=db_customer,
    #     id_field_api="id",
    #     id_field_db="ID",
    #     email_field_api="email",
    #     email_field_db="user_email",
    # )

    # The same above, you can use the block above from generic logic (shared validator)
    assert db_customer, "❌ No DB record found"

    # 🧪 BUSINESS VALIDATION ONLY (structure already guaranteed)
    assert str(db_customer["ID"]) == str(customer["id"]), "❌ DB ID does not match API ID"

    assert db_customer["user_email"] == customer["email"], "❌ DB email does not match API email"


# ------------------------------------------------------------------
# 🔁 UNIQUENESS VALIDATION (BUSINESS RULE)
# ------------------------------------------------------------------
# Pure domain logic: "there must be exactly one"
# ------------------------------------------------------------------
def assert_single_customer_by_email(customers: List[Dict[str, Any]], email: str) -> Dict[str, Any]:
    """
    Ensure exactly ONE customer exists for a given email.

    Use this ONLY when validating full dataset (pagination).

    SAFE:
        - Filtering uses .get()
        - Final validation uses strict access
    """
    matches = [c for c in customers if c.get("email") == email]
    # Equivalent for loop version:
    # matches = []
    # for c in customers:
    #     if c.get("email") == email:
    #         matches.append(c)

    assert len(matches) == 1, f"❌ Expected 1 customer, found {len(matches)} for {email}"

    customer = matches[0]

    # 🧱 STRUCTURE
    assert_valid_customer_response(customer)

    return customer


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
