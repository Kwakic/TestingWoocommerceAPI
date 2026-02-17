"""
Base Validators (Generic, Reusable Across All Entities)

This module contains generic assertion helpers that can be reused across
multiple microservices (customers, orders, products, etc.).

🎯 Purpose:
- Provide a single source of truth for common validation patterns
- Eliminate duplication across entity-specific validators
- Enforce consistent assertion style across the framework

🧠 Design Principles:
- These functions are ENTITY-AGNOSTIC (no customer/order-specific logic)
- They operate on generic dictionaries returned by API/DAO layers
- They rely on configurable field names (e.g., "id", "email", etc.)
- They use Python `assert` for clean pytest integration

📌 How to Use:
- DO NOT use these directly in tests ❌
- Use them via entity-specific wrappers (e.g., customer_validators.py) ✅

Example:
    # In customer_validators.py
    def assert_customer_exists_in_api(customers, email):
        return assert_resource_exists(customers, identifier=email, field="email")

This keeps business meaning at the domain level while reusing core logic.
"""

from typing import List, Dict, Any


# ------------------------------------------------------------------
# GENERIC: ASSERT RESOURCE EXISTS (API LEVEL)
# ------------------------------------------------------------------
def assert_resource_exists(
    resources: List[Dict[str, Any]],
    identifier: str,
    field: str = "email",
) -> Dict[str, Any]:
    """
    Assert that at least one resource exists in API response and matches identifier.

    This function is typically used after a filtered API call such as:
        GET /resource?email=value

    It validates:
    - The response is not empty
    - The first item matches the expected identifier
    - The resource has a valid ID

    Args:
        resources (List[Dict[str, Any]]): List of resources returned from API
        identifier (str): Expected value (e.g., email, id, username)
        field (str): Field name used for matching (default: "email")

    Returns:
        Dict[str, Any]: The first matching resource

    Raises:
        AssertionError:
            - If no resources are returned
            - If the field does not match the identifier
            - If the resource has invalid/missing ID

    Example:
        customer = assert_resource_exists(customers, identifier=email, field="email")
    """

    assert resources, f"❌ Resource not found for {field}={identifier}"

    resource = resources[0]

    assert resource.get(field) == identifier, \
        f"❌ {field} mismatch: expected {identifier}, got {resource.get(field)}"

    assert isinstance(resource.get("id"), int) and resource["id"] > 0, \
        "❌ Invalid or missing resource ID"

    return resource


# ------------------------------------------------------------------
# GENERIC: ASSERT RESOURCE MATCHES DATABASE
# ------------------------------------------------------------------
def assert_resource_matches_db(
    resource: Dict[str, Any],
    db_resource: Dict[str, Any],
    *,
    id_field_api: str = "id",
    id_field_db: str = "ID",
    email_field_api: str = "email",
    email_field_db: str = "user_email",
) -> None:
    """
    Assert that API resource matches corresponding DB record.

    This validates cross-layer consistency between:
        - API response (what the service returns)
        - Database record (ground truth)

    Args:
        resource (Dict[str, Any]): Resource returned by API
        db_resource (Dict[str, Any]): Resource fetched from DB via DAO
        id_field_api (str): ID field name in API response (default: "id")
        id_field_db (str): ID field name in DB (default: "ID")
        email_field_api (str): Email field name in API (default: "email")
        email_field_db (str): Email field name in DB (default: "user_email")

    Raises:
        AssertionError:
            - If DB record is missing
            - If ID mismatch between API and DB
            - If email mismatch between API and DB

    Example:
        assert_resource_matches_db(customer, db_customer)
    """

    assert db_resource, "❌ No DB record found"

    assert str(db_resource[id_field_db]) == str(resource[id_field_api]), \
        "❌ DB ID does not match API ID"

    assert db_resource[email_field_db] == resource[email_field_api], \
        "❌ DB email does not match API email"


# ------------------------------------------------------------------
# GENERIC: ASSERT UNIQUENESS (FULL DATASET SCAN)
# ------------------------------------------------------------------
def assert_single_resource_by_field(
    resources: List[Dict[str, Any]],
    value: str,
    field: str = "email",
) -> Dict[str, Any]:
    """
    Assert that exactly ONE resource exists for a given field value.

    This is used for deep validation scenarios where:
    - You fetch ALL resources (pagination)
    - You validate shared uniqueness (not trusting API filters)

    Example flow:
        GET /customers?page=1...N
        → filter locally by email
        → assert only one exists

    Args:
        resources (List[Dict[str, Any]]): Full dataset (unfiltered API response)
        value (str): Expected value (e.g., email)
        field (str): Field name used for matching (default: "email")

    Returns:
        Dict[str, Any]: The single matching resource

    Raises:
        AssertionError:
            - If no matches found
            - If more than one match found (duplicate detection)

    Example:
        customer = assert_single_resource_by_field(all_customers, email, field="email")

    ⚠️ Performance Note:
        This method assumes a FULL dataset scan and may be slow on large datasets.
        Use only in deep validation tests (not in every test).
    """

    matches = [r for r in resources if r.get(field) == value]

    assert len(matches) == 1, \
        f"❌ Expected exactly 1 resource for {field}={value}, found {len(matches)}"

    return matches[0]
