"""
Customer response assertions.

This module contains semantic assertions for customer objects.
Assertions here are reusable across helpers and tests.
"""
from typing import List, Dict, Any

import logging

logger = logging.getLogger(__name__)


def assert_valid_customer_response(customer: dict) -> None:
    # It tells readers (and type checkers like mypy/pyright) that the function does not return anything.
    """
    ✅ Validates the structure and schema of a successful customer creation response (id, email, username present).
    Useful to centralize repeated checks across tests.

    - Raises AssertionError if invalid.
    - It ensures schema and domain rules are never forgotten or duplicated.
    - Centralizes your happy-path response validation in one place.
    - It reduces clutter in tests.
    - It honors separation of concerns (test ≠ validation logic).
    - It keeps your test code clean-no need to separately call the schema validator and then structural/assertion
    checks.

    Args:
        customer (dict): API response for created customer

    Raises:
        AssertionError or jsonschema.ValidationError on failure.
    """
    # ------------------------------------------------------------------
    # 📋 Schema Validation first (It checks that the POST response is valid)
    # ------------------------------------------------------------------

    if not isinstance(customer, dict):
        raise AssertionError(f"Response is not a dict. Got: {type(customer)}")

    if "id" not in customer or not isinstance(customer["id"], int):
        raise AssertionError(f"Invalid or missing customer ID. Got: {customer.get('id')}")
    if "email" not in customer or not isinstance(customer["email"], str):
        raise AssertionError(f"Invalid or missing email. Got: {customer.get('email')}")
    if "username" not in customer:
        raise AssertionError(f"Missing username. Got: {customer.get('username')}")

    logger.info("✅ Customer ID and email validated: %s, %s", customer["id"], customer["email"])

    # # Early assert for id and email ensures immediate failure if response is malformed.
    # assert customer_id is not None, "❌ Customer ID not returned"
    # assert email is not None, "❌ Customer Email not returned"
    # logger.info(f"✅ Assertion passed: Customer created: ID={customer_id}, Email={email}")


# ------------------------
# API VALIDATION
# ------------------------
def assert_customer_exists_in_api(customers: List[Dict[str, Any]], email: str) -> Dict[str, Any]:
    assert customers, f"❌ Customer not found via API for email {email}"

    customer = customers[0]

    assert customer.get("email") == email, f"❌ Email mismatch for {email}"

    assert isinstance(customer.get("id"), int) and customer["id"] > 0, \
        "❌ Invalid or missing customer ID"

    return customer


# ------------------------
# DB VALIDATION
# ------------------------
def assert_customer_matches_db(customer: Dict[str, Any], db_customer: Dict[str, Any]) -> None:
    assert db_customer, "❌ No DB record found"

    assert str(db_customer["ID"]) == str(customer["id"]), \
        "❌ DB ID does not match API ID"

    assert db_customer.get("user_email") == customer["email"], \
        "❌ DB email does not match API email"


# ------------------------
# UNIQUENESS VALIDATION
# ------------------------
def assert_single_customer_with_email(
        customers: List[Dict[str, Any]],
        email: str
) -> Dict[str, Any]:

    matches = [c for c in customers if c.get("email") == email]

    assert len(matches) == 1, \
        f"❌ Expected exactly 1 customer, found {len(matches)} for {email}"

    return matches[0]
