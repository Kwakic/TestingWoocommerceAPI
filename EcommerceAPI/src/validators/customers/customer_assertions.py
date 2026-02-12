"""
Customer response assertions.

This module contains semantic assertions for customer objects.
Assertions here are reusable across helpers and tests.
"""

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
