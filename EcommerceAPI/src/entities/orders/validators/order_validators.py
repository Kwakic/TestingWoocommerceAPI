"""
Order Validation Layer

This module contains domain-level validators for the WooCommerce Orders API.

Responsibilities
----------------
• Validate API response structure using Pydantic
• Validate order datasets returned by list endpoints
• Validate successful create, retrieve, update, and list responses
• Validate order-specific expectations such as identity, customer, status,
  and line items
• Validate response and error data contracts

Important design rule:
Validators ONLY validate data.

They must NOT:
    - call APIs
    - query databases
    - create test data
    - orchestrate workflows

Data fetching is handled by:
    Tests or Helpers.

Architecture
------------
TEST / HELPER
      ↓
OrdersApi
      ↓
HttpResponse
      ↓
ORDER VALIDATORS
      ↓
OrderModel
      ↓
DB validation is performed by ``order_db_validators.py`` using records
retrieved by the test or helper through ``OrdersDAO``.

assert_valid_order_response → Structure validation (STRUCTURE)
assert_single_order_by_id → API dataset validation (DATASET)
assert_order_created_successfully → Create response validation (TRANSPORT)
assert_order_retrieved_successfully → Retrieve response validation (TRANSPORT)
assert_order_updated_successfully → Update response validation (TRANSPORT)
assert_orders_listed_successfully → List response validation (TRANSPORT)
assert_order_error_response → Error response validation (BASE)
assert_order_creation_failed → Create error validation (SCENARIOS)
assert_order_not_found_error → Not-found validation (SCENARIOS)
assert_order_identity → Identity validation (BUSINESS)
assert_order_customer_id → Customer association validation (BUSINESS)
assert_order_status → Status validation (BUSINESS)
assert_order_line_items → Line-item validation (BUSINESS)
assert_order_matches_db (order_db_validators.py) → API + DB validation
                                                   (INTEGRATION)

"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Mapping, Optional

from EcommerceAPI.src.core.http_response import HttpResponse

from EcommerceAPI.src.entities.orders.models.order_model import OrderModel

logger = logging.getLogger(__name__)


# ================================================================
# STRUCTURE VALIDATION
# ================================================================


def assert_valid_order_response(order: Dict[str, Any]) -> OrderModel:
    """Validate the structure of one Order API response.

    ``OrderModel`` checks the required response fields and nested Order data.
    Scenario-specific values, such as the expected customer or products, are
    checked by the business validators below.

    Args:
        order: Parsed JSON object returned by a single-Order API endpoint.

    Returns:
        The response represented as a validated ``OrderModel``.

    Raises:
        AssertionError: If ``order`` is not a JSON object.
        pydantic.ValidationError: If the response does not match ``OrderModel``.
    """
    assert isinstance(
        order, dict
    ), f"Expected Order response to be a dict, got {type(order).__name__}"

    order_model = OrderModel.model_validate(order)

    logger.info(
        "Order structure valid: id=%s status=%s customer_id=%s",
        order_model.id,
        order_model.status,
        order_model.customer_id,
    )

    return order_model


# ================================================================
# DATASET VALIDATION
# ================================================================


def assert_single_order_by_id(
    orders: List[Dict[str, Any]],
    order_id: int,
) -> OrderModel:
    """Find and validate exactly one Order in a list response by ID.

    Args:
        orders: Parsed list returned by ``GET /orders``.
        order_id: ID of the Order expected in the list.

    Returns:
        The matching Order as a validated ``OrderModel``.

    Raises:
        AssertionError: If ``orders`` is not a list or does not contain
            exactly one matching Order.
        pydantic.ValidationError: If the matching response has an invalid
            structure.
    """
    assert isinstance(
        orders, list
    ), f"Expected Orders dataset to be a list, got {type(orders).__name__}"
    assert all(
        isinstance(order, dict) for order in orders
    ), "Expected every item in the Orders dataset to be a dict"

    matches = [order for order in orders if order.get("id") == order_id]

    assert (
        len(matches) == 1
    ), f"Expected exactly one Order with ID={order_id}, found {len(matches)}"

    order_model = assert_valid_order_response(matches[0])

    logger.info(
        "Order found in dataset: id=%s status=%s",
        order_model.id,
        order_model.status,
    )

    return order_model


# ================================================================
# SUCCESSFUL API RESPONSES
# ================================================================


def assert_order_created_successfully(response: HttpResponse) -> OrderModel:
    """Validate a successful ``POST /orders`` response.

    A successful WooCommerce create request returns HTTP 201 and a complete
    Order object. This validator also checks that the server assigned a
    positive Order ID and a non-empty Order key.

    Args:
        response: Complete response returned by ``OrdersApi.create_order``.

    Returns:
        The created Order as a validated ``OrderModel``.

    Raises:
        AssertionError: If the HTTP status or generated Order identity is
            invalid.
        pydantic.ValidationError: If the response body does not match
            ``OrderModel``.
    """
    assert response.status_code == 201, (
        "POST /orders failed. "
        f"Expected 201, got {response.status_code}. "
        f"Response: {response.text}"
    )

    order = assert_valid_order_response(response.json)

    assert order.id > 0, f"Created Order ID must be positive, got {order.id}"
    assert order.order_key.strip(), "Created Order has an empty 'order_key'"

    logger.info(
        "Order created successfully: id=%s customer_id=%s",
        order.id,
        order.customer_id,
    )

    return order


def assert_order_retrieved_successfully(response: HttpResponse) -> OrderModel:
    """Validate a successful ``GET /orders/{id}`` response.

    Args:
        response: Complete response returned by ``OrdersApi.get_order``.

    Returns:
        The retrieved Order as a validated ``OrderModel``.

    Raises:
        AssertionError: If the HTTP status is not 200 or the body is not an
            Order object.
        pydantic.ValidationError: If the response body does not match
            ``OrderModel``.
    """
    assert response.status_code == 200, (
        "GET /orders/{id} failed. "
        f"Expected 200, got {response.status_code}. "
        f"Response: {response.text}"
    )

    return assert_valid_order_response(response.json)


def assert_order_updated_successfully(response: HttpResponse) -> OrderModel:
    """Validate a successful ``PUT /orders/{id}`` response.

    WooCommerce returns the updated Order representation. The HTTP status and
    response structure are validated here; expected field changes are checked
    with the relevant Order expectation validators.

    Args:
        response: Complete response returned by ``OrdersApi.update_order``.

    Returns:
        The updated Order as a validated ``OrderModel``.

    Raises:
        AssertionError: If the HTTP status is not 200 or the body is not an
            Order object.
        pydantic.ValidationError: If the response body does not match
            ``OrderModel``.
    """
    assert response.status_code == 200, (
        "PUT /orders/{id} failed. "
        f"Expected 200, got {response.status_code}. "
        f"Response: {response.text}"
    )

    return assert_valid_order_response(response.json)


def assert_orders_listed_successfully(
    response: HttpResponse,
) -> List[OrderModel]:
    """Validate a successful ``GET /orders`` list response.

    Args:
        response: Complete response returned by ``OrdersApi.list_orders``.

    Returns:
        The returned Orders as validated ``OrderModel`` objects.

    Raises:
        AssertionError: If the HTTP status is not 200 or the body is not a
            list of Order objects.
        pydantic.ValidationError: If any Order in the response has an invalid
            structure.
    """
    assert response.status_code == 200, (
        "GET /orders failed. "
        f"Expected 200, got {response.status_code}. "
        f"Response: {response.text}"
    )
    assert isinstance(response.json, list), (
        "Expected GET /orders response body to be a list, "
        f"got {type(response.json).__name__}"
    )

    orders = [assert_valid_order_response(order) for order in response.json]

    logger.info("Orders list validated: count=%s", len(orders))

    return orders


# ================================================================
# ORDER EXPECTATION VALIDATION
# ================================================================


def assert_order_identity(
    order: OrderModel,
    expected_id: int,
) -> None:
    """Check that the Order has the expected server-assigned ID.

    Args:
        order: Structurally validated Order response.
        expected_id: ID of the Order expected by the test.

    Raises:
        AssertionError: If the Order ID differs from the expectation.
    """
    assert (
        order.id == expected_id
    ), f"Order ID mismatch. Expected {expected_id}, got {order.id}"

    logger.info(
        "Order identity verified: id=%s",
        order.id,
    )


def assert_order_customer_id(
    order: OrderModel,
    expected_customer_id: int,
) -> None:
    """Check that the Order is associated with the expected customer.

    Guest Orders use ``customer_id=0``. The validator accepts that value when
    it is the expected scenario and does not require a registered customer.

    Args:
        order: Structurally validated Order response.
        expected_customer_id: Expected customer ID, or ``0`` for a guest.

    Raises:
        AssertionError: If the Order's customer ID differs from the
            expectation.
    """
    assert order.customer_id == expected_customer_id, (
        "Order customer_id mismatch. "
        f"Expected {expected_customer_id}, got {order.customer_id}"
    )

    logger.info(
        "Order customer association verified: id=%s customer_id=%s",
        order.id,
        order.customer_id,
    )


def assert_order_status(
    order: OrderModel,
    expected_status: str,
) -> None:
    """Check that an Order has the status expected by the scenario.

    The validator compares the response to the supplied expectation instead
    of restricting statuses to a fixed list. WooCommerce installations may
    register additional Order statuses.

    Args:
        order: Structurally validated Order response.
        expected_status: Status expected for this test scenario.

    Raises:
        AssertionError: If the returned status differs from the expectation.
    """
    assert (
        order.status == expected_status
    ), f"Order status mismatch. Expected '{expected_status}', got '{order.status}'"

    logger.info(
        "Order status verified: id=%s status=%s",
        order.id,
        order.status,
    )


def assert_order_line_items(
    order: OrderModel,
    expected_line_items: List[Dict[str, Any]],
) -> None:
    """Check that an Order contains the expected products and quantities.

    Each expected line item must include ``product_id`` and ``quantity``.
    ``variation_id`` may also be supplied when a specific product variation
    is expected. Items are matched by these values, so the API response does
    not need to preserve the request's item order. Repeated products are
    handled as separate line items.

    Args:
        order: Structurally validated Order response.
        expected_line_items: Request-side product and quantity expectations.

    Raises:
        AssertionError: If the item count, required expectation fields, or
            any product, quantity, or supplied variation differs.
    """
    assert isinstance(expected_line_items, list), (
        "Expected line items must be a list, "
        f"got {type(expected_line_items).__name__}"
    )
    assert len(order.line_items) == len(expected_line_items), (
        f"Order line-item count mismatch. Expected {len(expected_line_items)}, "
        f"got {len(order.line_items)}"
    )

    unmatched_items = list(order.line_items)

    for index, expected_item in enumerate(expected_line_items):
        assert isinstance(expected_item, Mapping), (
            f"Expected line item at index {index} must be a mapping, "
            f"got {type(expected_item).__name__}"
        )
        assert (
            "product_id" in expected_item
        ), f"Expected line item at index {index} is missing 'product_id'"
        assert (
            "quantity" in expected_item
        ), f"Expected line item at index {index} is missing 'quantity'"

        matching_index = next(
            (
                item_index
                for item_index, item in enumerate(unmatched_items)
                if item.product_id == expected_item["product_id"]
                and item.quantity == expected_item["quantity"]
                and (
                    "variation_id" not in expected_item
                    or item.variation_id == expected_item["variation_id"]
                )
            ),
            None,
        )

        assert matching_index is not None, (
            f"Expected Order line item {dict(expected_item)} was not found. "
            f"Remaining items: "
            f"{[(item.product_id, item.variation_id, item.quantity) for item in unmatched_items]}"
        )

        unmatched_items.pop(matching_index)

    logger.info(
        "Order line items verified: id=%s item_count=%s",
        order.id,
        len(order.line_items),
    )


# ================================================================
# ERROR RESPONSE VALIDATION
# ================================================================


def assert_order_error_response(
    response: Dict[str, Any],
    expected_status: Optional[int] = None,
) -> None:
    """Validate the common WooCommerce REST API error response structure.

    Expected response shape::

        {
            "code": "...",
            "message": "...",
            "data": {"status": 400}
        }

    The function validates the error contract without requiring a particular
    code or message, which can vary by failure scenario or WooCommerce setup.

    Args:
        response: Parsed JSON error response.
        expected_status: Optional HTTP status embedded in ``data.status``.

    Raises:
        AssertionError: If the error payload is incomplete or its embedded
            status differs from the supplied expectation.
    """
    assert isinstance(
        response, dict
    ), f"Expected error response to be a dict, got {type(response).__name__}"
    assert "code" in response, f"Missing 'code' in error response: {response}"
    assert "message" in response, f"Missing 'message' in error response: {response}"
    assert "data" in response, f"Missing 'data' in error response: {response}"
    assert response["code"], "Error 'code' must not be empty"
    assert response["message"], "Error 'message' must not be empty"
    assert isinstance(response["data"], dict), (
        "Expected error response 'data' to be a dict, "
        f"got {type(response['data']).__name__}"
    )
    assert (
        "status" in response["data"]
    ), f"Missing 'status' in error response data: {response}"

    actual_status = response["data"]["status"]
    if expected_status is not None:
        assert (
            actual_status == expected_status
        ), f"Expected error status {expected_status}, got {actual_status}"

    logger.info(
        "Valid Order error response: code=%s status=%s",
        response["code"],
        actual_status,
    )


def assert_order_creation_failed(response: Dict[str, Any]) -> None:
    """Validate the error payload returned for a rejected Order creation.

    This checks the standard WooCommerce error contract and its embedded
    status. Tests should separately assert the actual HTTP response status.

    Args:
        response: Parsed JSON error response from ``POST /orders``.

    Raises:
        AssertionError: If the error contract is invalid or its embedded
            status is not 400.
    """
    assert_order_error_response(response, expected_status=400)

    logger.info(
        "Order creation failure validated: code=%s",
        response["code"],
    )


def assert_order_not_found_error(response: Dict[str, Any]) -> None:
    """Validate an Order not-found error without hard-coding its wording.

    Args:
        response: Parsed JSON error response from an Order lookup.

    Raises:
        AssertionError: If the error contract is invalid or its embedded
            status is not 404.
    """
    assert_order_error_response(response, expected_status=404)

    logger.info(
        "Order not-found error validated: code=%s",
        response["code"],
    )
