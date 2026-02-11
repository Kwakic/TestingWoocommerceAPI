"""
Customer response assertions.

This module contains semantic assertions for customer objects.
Assertions here are reusable across helpers and tests.
"""

from typing import Dict, Any
import logging

from EcommerceAPI.src.utilities.date_timestamp_utils import safe_parse_utc_datetime

logger = logging.getLogger(__name__)


def assert_valid_customer_response(
    customer: Dict[str, Any],
    expected_payload: Dict[str, Any] | None = None,
) -> None:
    """
    Assert that a customer response is structurally and semantically valid.

    Args:
        customer (dict): Parsed customer response from API.
        expected_payload (dict, optional):
            Original payload used to create the customer.
            If provided, critical fields are compared.

    Raises:
        AssertionError: If validation fails.

    Note:
        Still NO HTTP, NO fixtures
        Semantic assertions
    """
    assert isinstance(customer, dict), "Customer response must be a dict"
    assert "id" in customer, "Customer response missing 'id'"

    # Basic identity checks
    assert customer["id"], "Customer id is empty"

    # Timestamp sanity checks (if present)
    if "date_created" in customer:
        safe_parse_utc_datetime(customer["date_created"])

    if "date_modified" in customer:
        safe_parse_utc_datetime(customer["date_modified"])

    # Cross-check payload vs response (if provided)
    if expected_payload:
        for field in ("email",):
            if field in expected_payload:
                assert customer.get(field) == expected_payload[field], (
                    f"Customer field mismatch: {field}"
                )
