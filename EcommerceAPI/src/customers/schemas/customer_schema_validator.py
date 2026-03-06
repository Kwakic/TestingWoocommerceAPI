# schemas/customer_schema_validator.py
# contract validation
"""
Customer error payload schema validators.

Used ONLY for validating API error responses.

Success responses are validated via Pydantic models.

This module contains ONLY JSON schema validation logic.
It knows nothing about HTTP, helpers, or test fixtures.

✔ Purpose
    - Validate API contract (JSON schema)
    - Types, required fields, format

✔ Used when
    - After API call (POST/GET)
    - Contract testing

❗ Rule
    ❌ No business logic
    ❌ No DB logic

Note:
    JSON Schema validation only
    No “business meaning”
    Raises SchemaValidationError
"""

import logging

from jsonschema import validate

from tests.shared.schemas.customer import error_schema

logger = logging.getLogger(__name__)


def validate_customer_error_response_schema(response: dict) -> None:
    """
    📋 Validates the structure of a failed customer creation response using error schema.

    Expected format:
    {
        "code": "...",
        "message": "...",
        "data": {"status": int}
    }

    This static helper is useful in tests that assert on error payload structure.

    Args:
        response (dict): The JSON response from the API.

    Raises:
        AssertionError: If schema is invalid or required fields are missing.
    """
    # It uses: TypeError for incorrect types and AssertionError for missing fields. These are explicit and
    # semantically correct, which improves debugging and integrates better with pytest error reporting.
    # It avoids emojis, noisy messages and unnecessary verbosity.
    if not isinstance(response, dict):
        raise TypeError(f"Expected dict error response, got {type(response)}")
    if not response.get("code"):
        raise AssertionError(f"Missing 'code' in error response: {type(response)}")
    if not response.get("message"):
        raise AssertionError(f"Missing 'message' in error response: {type(response)}")
    if not response.get("data"):
        raise AssertionError(f"Missing 'data' in error response: {type(response)}")
    validate(instance=response, schema=error_schema)
    # validate comes from the jsonschema Python library. It’s used to validate a JSON object against a predefined
    # schema.
    # instance: the actual JSON data you want to validate.
    # schema: the JSON Schema that defines the structure, required fields, types, and constraints.
