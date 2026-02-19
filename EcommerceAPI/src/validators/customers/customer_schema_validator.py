"""
Customer schema validators.

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

from tests.shared.schemas.customer import customer_schema, error_schema

logger = logging.getLogger(__name__)


def validate_customer_response_schema(customer: dict) -> None:
    # It tells readers (and type checkers like mypy/pyright) that the function does not return anything.
    """
    Validates the structure of a single customer object against the customer JSON schema.
    Ensures your API returned valid data upon creation. Useful for unit test level.
    Immediately after customer creation, you're validating that the response structure from the creation endpoint
    is correct — i.e., all required fields (id, email, billing, shipping, etc.) are present and typed correctly.

     Args:
        customer (dict): Customer data to validate.

    Raises:
        jsonschema.ValidationError: If validation fails.
    """
    validate(instance=customer, schema=customer_schema)  # validate comes from the jsonschema Python library.
    # It’s used to validate a JSON object against a predefined schema.
    # instance: the actual JSON data you want to validate. In your code, customer is a Python dictionary
    # returned by the API.
    # schema: the JSON Schema that defines the structure, required fields, types, and constraints.
    # In your code, this is customer_schema.
    logger.info("✅ Customer response schema validated successfully")


def validate_customer_error_response_schema(response: dict) -> None:
    """
    📋 Validates the structure of a failed customer creation response using error schema.

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
    validate(instance=response, schema=error_schema)
    # validate comes from the jsonschema Python library. It’s used to validate a JSON object against a predefined
    # schema.
    # instance: the actual JSON data you want to validate.
    # schema: the JSON Schema that defines the structure, required fields, types, and constraints.
