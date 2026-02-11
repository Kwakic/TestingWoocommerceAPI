"""
Customer schema validators.

This module contains ONLY JSON schema validation logic.
It knows nothing about HTTP, helpers, or test fixtures.

Note:
    JSON Schema validation only
    No “business meaning”
    Raises SchemaValidationError
"""

from typing import Dict, Any
import logging

from jsonschema import validate

from tests.shared.schemas.customer import customer_schema, error_schema
from EcommerceAPI.src.utilities.exceptions import SchemaValidationError

logger = logging.getLogger(__name__)


def validate_customer_schema(payload: Dict[str, Any]) -> None:
    """
    Validate a successful customer response against the customer schema.

    Args:
        payload (dict): Parsed JSON customer response.

    Raises:
        SchemaValidationError: If schema validation fails.
    """
    try:
        validate(instance=payload, schema=customer_schema)
    except Exception as exc:
        logger.error("Customer schema validation failed")
        raise SchemaValidationError(
            message="Customer schema validation failed",
            response_json=payload,
        ) from exc


def validate_customer_error_schema(payload: Dict[str, Any]) -> None:
    """
    Validate an error response against the customer error schema.

    Args:
        payload (dict): Parsed JSON error response.

    Raises:
        SchemaValidationError: If schema validation fails.
    """
    try:
        validate(instance=payload, schema=error_schema)
    except Exception as exc:
        logger.error("Customer error schema validation failed")
        raise SchemaValidationError(
            message="Customer error schema validation failed",
            response_json=payload,
        ) from exc
