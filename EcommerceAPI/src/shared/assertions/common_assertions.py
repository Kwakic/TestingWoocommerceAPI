"""
INTERNAL ENGINE (DO NOT USE DIRECTLY)

Base Validators (Generic, Reusable Across All Entities)

This module contains generic assertion helpers that can be reused across
multiple microservices (customers, orders, products, etc.).

🎯 Purpose:
- Provide a single source of truth for common validation patterns
- Eliminate duplication across entity-specific validators
- Enforce consistent assertion style across the framework

🧠 Design Principles:
- Follow the same philosophy as customer_assertions:
    ✔ Structure first (validated elsewhere)
    ✔ Business logic here
    ✔ Fail fast with clear errors
- Use strict access (obj["field"]) once structure is guaranteed
- Keep naming explicit and domain-oriented (entity, not resource)

📌 How to Use:
- DO NOT use these directly in tests ❌
- Use them via entity-specific wrappers (e.g., customer_validators.py) ✅

Example:
    # In customer_validators.py
    def assert_customer_exists_in_api(customers, email):
        return assert_resource_exists(customers, identifier=email, field="email")

This keeps business meaning at the domain level while reusing core logic.

✔ Purpose
    - Reusable generic logic
    - Avoid duplication

✔ Used by
    - customer_validators.py (optional)
    - NOT tests
    - NOT helpers
"""

from typing import List, Dict, Any


# ------------------------------------------------------------------
# 🧱 STRUCTURE VALIDATION (Schema / Contract Layer)
# structure validation must be done BEFORE business validation
# ------------------------------------------------------------------
# These helpers answer:
# 👉 "Is the response well-formed?"
# They validate presence + type of fields.
# They should FAIL FAST before any business logic runs.
# ------------------------------------------------------------------
def assert_is_dict(obj: Any, name: str = "object") -> None:
    """
    Ensure object is a dictionary.

    Args:
        obj: Object to validate
        name: Logical name for error message
    """
    assert isinstance(obj, dict), f"❌ {name} must be a dict. Got: {type(obj)}"


def assert_has_key(field: str, obj: Dict[str, Any]) -> None:
    """
    Ensure field exists in an object.
    """
    assert (
        field in obj
    ), f"❌ Missing required field '{field}'. Got keys: {list(obj.keys())}"


def assert_has_int(field: str, obj: Dict[str, Any]) -> None:
    """
    Ensure the field exists and is int.
    """
    assert_has_key(field, obj)
    value = obj[field]

    assert isinstance(
        value, int
    ), f"❌ Field '{field}' must be int. Got: {value} ({type(value)})"


def assert_has_str(field: str, obj: Dict[str, Any]) -> None:
    """
    Ensure the field exists and is str.
    """
    assert_has_key(field, obj)
    value = obj[field]

    assert isinstance(
        value, str
    ), f"❌ Field '{field}' must be str. Got: {value} ({type(value)})"


# ------------------------------------------------------------------
# GENERIC: ASSERT RESOURCE EXISTS (API LEVEL)
# ------------------------------------------------------------------
def assert_entity_exists_in_api(
    entities: List[Dict[str, Any]],
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
        entities (List[Dict[str, Any]]): List of resources returned from API
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
        customers = assert_resource_exists(customers, identifier=email, field="email")
    """

    assert entities, f"❌ Entity not found for {field}={identifier}"

    entity = entities[0]

    # ✅ Strict access (structure assumed valid)
    assert (
        entity[field] == identifier
    ), f"❌ {field} mismatch: expected {identifier}, got {entity[field]}"

    assert (
        isinstance(entity["id"], int) and entity["id"] > 0
    ), f"❌ Invalid entity ID: {entity['id']}"

    return entity


# ------------------------------------------------------------------
# GENERIC: ASSERT RESOURCE MATCHES DATABASE
# ------------------------------------------------------------------
def assert_entity_matches_db(
    entity: Dict[str, Any],
    db_entity: Dict[str, Any],
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
        entity (Dict[str, Any]): Resource returned by API
        db_entity (Dict[str, Any]): Resource fetched from DB via DAO
        id_field_api (str): ID field name in API response (default: "id")
        id_field_db (str): ID field name in DB (default: "ID")
        email_field_api (str): Email field name in API (default: "email")
        email_field_db (str): Email field name in DB (default: "user_email")

    Raises:
        AssertionError:
            - If DB record is missing
            - If ID mismatch between API and DB
            - If email mismatch between API and DB

    Assumes:
    - Structure already validated

    Example:
        assert_resource_matches_db(customers, db_customer)
    """

    assert db_entity, "❌ No DB record found"

    assert str(db_entity[id_field_db]) == str(
        entity[id_field_api]
    ), "❌ DB ID does not match API ID"

    assert (
        db_entity[email_field_db] == entity[email_field_api]
    ), "❌ DB email does not match API email"


# ------------------------------------------------------------------
# GENERIC: ASSERT UNIQUENESS (FULL DATASET SCAN)
# ------------------------------------------------------------------
def assert_single_entity_by_field(
    entities: List[Dict[str, Any]],
    value: str,
    field: str = "email",
) -> Dict[str, Any]:
    """
    Assert that exactly ONE entity exists for a given field value.

    This is used for deep validation scenarios where:
    - You fetch ALL resources (pagination)
    - You validate shared uniqueness (not trusting API filters)

    Example flow:
        GET /customers?page=1...N
        → filter locally by email
        → assert only one exists

    Args:
        entities (List[Dict[str, Any]]): Full dataset (unfiltered API response)
        value (str): Expected value (e.g., email)
        field (str): Field name used for matching (default: "email")

    Returns:
        Dict[str, Any]: The single matching resource

    Raises:
    AssertionError:
        - If no matches found
        - If more than one match found (duplicate detection)

    It uses:
        - .get() for safe filtering
        - strict validation after selection

    ⚠️ Performance Note:
        This method assumes a FULL dataset scan and may be slow on large datasets.
        Use only in deep validation tests (not in every test).
    """

    # ✅ Filtering → safe access
    matches = [e for e in entities if e.get(field) == value]
    # Equivalent for loop version:
    # matches = []
    # for c in customers:
    #     if c.get("email") == email:
    #         matches.append(c)

    assert (
        len(matches) == 1
    ), f"❌ Expected exactly 1 entity for {field}={value}, found {len(matches)}"

    entity = matches[0]

    # ✅ Now strict access
    assert (
        entity[field] == value
    ), f"❌ {field} mismatch after filtering: {entity[field]}"

    return entity


def assert_status_code(http_response, expected_status: int) -> None:
    """
    Assert HTTP status code from HttpResponse.

    This is a TRANSPORT-level validation and should be used in:
        - contract tests
        - negative tests
        - raw API tests

    Args:
        http_response: HttpResponse object
        expected_status (int): Expected HTTP status code

    Raises:
        AssertionError: If status code does not match
    """
    actual = http_response.status_code

    assert actual == expected_status, (
        f"❌ Expected status {expected_status}, got {actual}. "
        f"URL: {http_response.url} "
        f"Response: {http_response.text[:300]}"
    )
