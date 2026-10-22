"""Negative integration tests for WooCommerce Order creation.

These tests send intentionally invalid payloads through order_api_raw so they
can inspect the HTTP response from POST /orders. The valid Order fixture is
not used because it builds valid data and asserts successful creation.
"""

import logging

import pytest

from EcommerceAPI.src.entities.orders.validators.order_validators import (
    assert_order_creation_failed,
)


logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.orders, pytest.mark.integration]


# ---------------------------
# ⚠️ Test: Invalid Order Status
# ---------------------------
@pytest.mark.negative
@pytest.mark.contract
@pytest.mark.regression
def test_create_order_with_invalid_status(
    create_valid_product,
    order_api_raw,
):
    """Reject an Order creation request with an unsupported status.

    Test flow:

        1. Create a valid Product to satisfy the Order line-item requirement.
        2. Send an Order payload with an unsupported status.
        3. Verify HTTP 400 and the WooCommerce error response contract.
    """

    # -------------------------------------------
    # Step 1 — Create a Product for the Order
    # -------------------------------------------
    product = create_valid_product()
    product_id = product["id"]

    # -------------------------------------------
    # Step 2 — Send an Order payload with invalid status
    # -------------------------------------------
    payload = {
        "status": "not-a-valid-order-status",
        "line_items": [
            {
                "product_id": product_id,
                "quantity": 1,
            }
        ],
    }
    http_response = order_api_raw.post(
        endpoint="orders",
        payload=payload,
    )

    # -------------------------------------------
    # Step 3 — Verify the transport and error contracts
    # -------------------------------------------
    assert http_response.status_code == 400, (
        "Expected HTTP 400 for an unsupported Order status, "
        f"got {http_response.status_code}. "
        f"Response: {http_response.text[:300]}"
    )

    response = http_response.json
    assert_order_creation_failed(response)

    logger.info(
        "Invalid Order status rejected with error code: %s",
        response["code"],
    )


# ---------------------------
# ⚠️ Test: Malformed Order Line Items
# ---------------------------
@pytest.mark.negative
@pytest.mark.contract
@pytest.mark.regression
def test_create_order_with_malformed_line_items(order_api_raw):
    """Reject an Order payload whose line_items field is not a list.

    WooCommerce expects line_items to be an array of line-item objects. This
    test sends a string to exercise request-schema validation before a valid
    Order can be created.
    """

    # -------------------------------------------
    # Step 1 — Send a malformed Order payload
    # -------------------------------------------
    payload = {
        "line_items": "not-a-list",
    }
    http_response = order_api_raw.post(
        endpoint="orders",
        payload=payload,
    )

    # -------------------------------------------
    # Step 2 — Verify the transport and error contracts
    # -------------------------------------------
    assert http_response.status_code == 400, (
        "Expected HTTP 400 for malformed Order line_items, "
        f"got {http_response.status_code}. "
        f"Response: {http_response.text[:300]}"
    )

    response = http_response.json
    assert_order_creation_failed(response)

    logger.info(
        "Malformed Order line_items rejected with error code: %s",
        response["code"],
    )
