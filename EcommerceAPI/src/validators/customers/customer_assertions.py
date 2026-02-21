# EcommerceAPI/src/validators/customers/customer_assertions.py
"""
MAIN VALIDATION LAYER (CUSTOMERS)

This module is the SINGLE ENTRY POINT for all customer validations.

🎯 Purpose:
- Provide clear, readable, domain-level assertions
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

from EcommerceAPI.src.validators.shared.base_validators import (
    assert_is_dict,
    assert_has_int,
    assert_has_str,
    assert_has_key,
    assert_entity_matches_db,
)

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# 🧱 STRUCTURE ENTRY POINT (SAFE VALIDATION) FOR CUSTOMER RESPONSE
# ------------------------------------------------------------------
# It ensures the API contract is respected BEFORE any deeper checks.
# ------------------------------------------------------------------
def assert_valid_customer_response(customer: dict) -> None:
    """
    Validate the structure of a customer response.

    This MUST be called before any deeper validation.

    Ensures:
        - customer is a dict
        - required fields exist
        - types are correct

    Args:
        customer (dict): API response for created customer

    """

    # 🧱 STRUCTURE VALIDATION
    assert_is_dict(customer, "customer")
    assert_has_int("id", customer)
    assert_has_str("email", customer)
    assert_has_key("username", customer)

    logger.info("✅ Customer structure valid: id=%s, email=%s", customer["id"], customer["email"])


# ------------------------------------------------------------------
# 🌐 API VALIDATION (STRUCTURE + LIGHT BUSINESS)
# ------------------------------------------------------------------
# Still mostly structural, but includes simple correctness checks like "email matches what we queried".
# ------------------------------------------------------------------
def assert_valid_customer_in_api(customers: List[Dict[str, Any]], email: str) -> Dict[str, Any]:
    """
    Validate that customer exists in API response.

    SAFE:
        - Validates structure
        - Validates business logic

    Returns:
        customer dict
    """

    assert customers, f"❌ No customers returned for email: {email}"

    customer = customers[0]

    # 🧱 STRUCTURE FIRST (fail fast if broken)
    assert_valid_customer_response(customer)

    # 🧪 BUSINESS VALIDATION
    assert customer["email"] == email, f"❌ Email mismatch. Expected: {email}, got: {customer['email']}"

    assert customer["id"] > 0, "❌ Customer ID must be > 0"

    return customer


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

    assert response["code"] in {
        "woocommerce_rest_invalid_id",
        "wc_user_invalid_id"
    }

    assert response['code'] == "wc_user_invalid_id", (f"Invalid Error code. Current: '{response['code']}', "
                                                      f"Expected: 'wc_user_invalid_id' ")

    # assert response['message'], "❌ Error 'message' should not be empty"

    assert response['message'] == "Invalid user ID.", (f"Invalid Error message. Current: '{response['message']}', "
                                                       f"Expected: 'Invalid user ID'")

    assert response['data'] == {'status': 404}, (f"Invalid data. Current: {response['data']}, "
                                                 f"Expected: {{'status': 404}}")
