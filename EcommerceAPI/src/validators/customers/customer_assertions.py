"""
Customer response assertions.

This module contains semantic assertions for customer objects.
Assertions here are reusable across helpers and tests.

Design principles:
- Use pure `assert` for pytest introspection
- Split STRUCTURE vs BUSINESS validation (very important)
- Fail fast with clear, precise errors
- Keep assertions small and composable
"""
from typing import List, Dict, Any

import logging

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# 🧱 STRUCTURE VALIDATION (Schema / Contract Layer)
# ------------------------------------------------------------------
# These helpers answer:
# 👉 "Is the response well-formed?"
# They validate presence + type of fields.
# They should FAIL FAST before any business logic runs.
# ------------------------------------------------------------------

def assert_is_dict(obj: Any, name: str = "object") -> None:
    assert isinstance(obj, dict), f"{name} must be a dict. Got: {type(obj)}"


def assert_has_int(field: str, obj: Dict[str, Any]) -> None:
    value = obj.get(field)
    assert isinstance(value, int), \
        f"Invalid or missing '{field}'. Got: {value}"


def assert_has_str(field: str, obj: Dict[str, Any]) -> None:
    value = obj.get(field)
    assert isinstance(value, str), \
        f"Invalid or missing '{field}'. Got: {value}"


def assert_has_key(field: str, obj: Dict[str, Any]) -> None:
    assert field in obj, \
        f"Missing required field '{field}'. Got: {obj}"


# ------------------------------------------------------------------
# 🧪 CUSTOMER RESPONSE (STRUCTURE ENTRY POINT)
# ------------------------------------------------------------------
# This is your main "schema validation" for customer responses.
# It ensures the API contract is respected BEFORE any deeper checks.
# ------------------------------------------------------------------
def assert_valid_customer_response(customer: dict) -> None:
    """
    Validates the structure of a successful customer response.

    Required:
    - id: int
    - email: str
    - username: present

    Args:
        customer (dict): API response for created customer

    """
    # ------------------------------------------------------------------
    # 📋 Schema Validation first (It checks that the POST response is valid)
    # ------------------------------------------------------------------

    # 🧱 STRUCTURE VALIDATION
    assert_is_dict(customer, "customer")

    assert_has_int("id", customer)
    assert_has_str("email", customer)
    assert_has_key("username", customer)

    logger.info("✅ Customer ID and email validated: %s, %s", customer["id"], customer["email"])


# ------------------------------------------------------------------
# 🌐 API VALIDATION (STRUCTURE + LIGHT BUSINESS)
# ------------------------------------------------------------------
# Still mostly structural, but includes simple correctness checks
# like "email matches what we queried".
# ------------------------------------------------------------------
def assert_customer_exists_in_api(customers: List[Dict[str, Any]], email: str) -> Dict[str, Any]:
    """
    Ensures API returned at least one customer and it matches the email.
    """

    assert customers, f"❌ No customers returned for email: {email}"

    customer = customers[0]

    # 🧱 STRUCTURE FIRST (fail fast if broken)
    assert_has_str("email", customer)
    assert_has_int("id", customer)

    # 🧪 BUSINESS VALIDATION
    assert customer["email"] == email, \
        f"❌ Email mismatch. Expected: {email}, Got: {customer['email']}"

    assert customer["id"] > 0, \
        "❌ Customer ID must be > 0"

    return customer


# ------------------------------------------------------------------
# 🗄️ DB VALIDATION (PURE BUSINESS LOGIC)
# ------------------------------------------------------------------
# IMPORTANT:
# At this stage we ASSUME structure is already validated.
# So we use strict access (obj["key"]) instead of .get() to enforce contract correctness.
# ------------------------------------------------------------------
def assert_customer_matches_db(customer: Dict[str, Any], db_customer: Dict[str, Any]) -> None:
    """
    Ensures API response matches DB record.
    """
    assert db_customer, "❌ No DB record found"

    # 🧪 BUSINESS VALIDATION ONLY (structure already guaranteed)
    assert str(db_customer["ID"]) == str(customer["id"]), "❌ DB ID does not match API ID"

    assert db_customer["user_email"] == customer["email"], "❌ DB email does not match API email"


# ------------------------------------------------------------------
# 🔁 UNIQUENESS VALIDATION (BUSINESS RULE)
# ------------------------------------------------------------------
# Pure domain logic: "there must be exactly one"
# ------------------------------------------------------------------
def assert_single_customer_with_email(customers: List[Dict[str, Any]], email: str) -> Dict[str, Any]:
    """
    Ensures exactly one customer exists for given email.
    """
    matches = [c for c in customers if c.get("email") == email]
    # Equivalent for loop version:
    # matches = []
    # for c in customers:
    #     if c.get("email") == email:
    #         matches.append(c)

    assert len(matches) == 1, f"❌ Expected exactly 1 customer, found {len(matches)} for {email}"

    return matches[0]
