"""Integration tests for applying WooCommerce coupons to Orders.

Valid Coupons and Products are created through their domain fixtures. The
valid Order is provisioned through create_valid_order, which validates and
registers it for cleanup. The minimum-spend failure is sent through the raw
Orders API fixture so the test can inspect WooCommerce's HTTP error response.
"""

import logging
from decimal import Decimal

import pytest

from EcommerceAPI.src.entities.orders.validators.order_validators import (
    assert_order_error_response,
    assert_order_line_items,
    assert_valid_order_response,
)


logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.orders, pytest.mark.integration]


# ---------------------------------------
# 🧪 Test: Coupon Applies to Eligible Order
# ---------------------------------------
@pytest.mark.sanity
@pytest.mark.smoke
@pytest.mark.contract
def test_valid_coupon_applies_50_percent_discount(
    create_valid_coupon,
    create_valid_product,
    create_valid_order,
    order_helper,
):
    """Apply a 50% coupon when the Order meets its minimum spend.

    Test flow:

        1. Create a Coupon requiring at least 35.00 in Order value.
        2. Create a Product priced at 40.00.
        3. Create an Order containing the Product and Coupon.
        4. Retrieve the Order and verify the Coupon and discount totals.
    """

    # -------------------------------------------
    # Step 1 — Create a Coupon with a minimum spend
    # -------------------------------------------
    coupon = create_valid_coupon(
        discount_type="percent",
        amount="50.00",
        minimum_amount="35.00",
    )
    coupon_id = coupon["id"]
    coupon_code = coupon["code"]

    # -------------------------------------------
    # Step 2 — Create a Product above the minimum spend
    # -------------------------------------------
    product = create_valid_product(
        regular_price="40.00",
    )
    product_id = product["id"]
    product_price = Decimal(product["price"])

    # -------------------------------------------
    # Step 3 — Create an Order with the Coupon
    # -------------------------------------------
    order = create_valid_order(
        product_id=product_id,
        coupon_lines=[{"code": coupon_code}],
    )
    order_id = order["id"]

    # -------------------------------------------
    # Step 4 — Retrieve and validate the Order
    # -------------------------------------------
    api_order_data = order_helper.get_order_by_id(order_id=order_id)
    api_order = assert_valid_order_response(api_order_data)

    assert_order_line_items(
        api_order,
        expected_line_items=[{"product_id": product_id, "quantity": 1}],
    )

    applied_coupon_lines = [
        coupon_line
        for coupon_line in api_order.coupon_lines or []
        if coupon_line.code and coupon_line.code.lower() == coupon_code.lower()
    ]
    assert len(applied_coupon_lines) == 1, (
        f"Expected Coupon {coupon_code!r} on Order ID={order_id}, "
        f"found {len(applied_coupon_lines)} coupon line(s)."
    )

    coupon_line = applied_coupon_lines[0]
    expected_discount = (
        product_price * Decimal(coupon["amount"]) / Decimal("100")
    ).quantize(Decimal("0.01"))

    assert (
        coupon_line.discount is not None
    ), f"Expected a discount for Coupon {coupon_code!r} on Order ID={order_id}."
    assert Decimal(coupon_line.discount) == expected_discount, (
        f"Expected Coupon discount {expected_discount}, " f"got {coupon_line.discount}."
    )
    assert Decimal(api_order.discount_total or "0.00") == expected_discount, (
        f"Expected Order discount_total {expected_discount}, "
        f"got {api_order.discount_total}."
    )

    logger.info(
        "Coupon ID=%r (%s) applied to Order ID=%r with discount %s.",
        coupon_id,
        coupon_code,
        order_id,
        expected_discount,
    )


# ---------------------------------------
# ⚠️ Test: Coupon Below Minimum Spend
# ---------------------------------------
@pytest.mark.negative
@pytest.mark.contract
@pytest.mark.regression
def test_coupon_is_rejected_below_minimum_amount(
    create_valid_coupon,
    create_valid_product,
    create_valid_order,
    order_api_raw,
):
    """Reject a Coupon application when the Order is below its minimum spend.

    A valid Order is created first and registered for teardown cleanup. The
    invalid update then exercises the Coupon restriction without relying on
    an unsuccessful create request that could leave an unowned Order record.
    """

    # -------------------------------------------
    # Step 1 — Create a Coupon with a minimum spend
    # -------------------------------------------
    minimum_amount = Decimal("50.00")
    coupon = create_valid_coupon(
        discount_type="percent",
        amount="30.00",
        minimum_amount=str(minimum_amount),
    )
    coupon_code = coupon["code"]

    # -------------------------------------------
    # Step 2 — Create a Product priced below the minimum
    # -------------------------------------------
    product = create_valid_product(
        regular_price="20.00",
    )
    product_id = product["id"]

    # -------------------------------------------
    # Step 3 — Create an eligible-to-create Order without the Coupon
    # -------------------------------------------
    order = create_valid_order(product_id=product_id)
    order_id = order["id"]

    # -------------------------------------------
    # Step 4 — Attempt to apply the ineligible Coupon
    # -------------------------------------------
    payload = {
        "coupon_lines": [{"code": coupon_code}],
    }
    http_response = order_api_raw.put(
        endpoint=f"orders/{order_id}",
        payload=payload,
    )

    # -------------------------------------------
    # Step 5 — Validate the WooCommerce error response
    # -------------------------------------------
    assert http_response.status_code == 400, (
        "Expected HTTP 400 when applying a Coupon below its minimum spend, "
        f"got {http_response.status_code}. "
        f"Response: {http_response.text[:300]}"
    )

    response = http_response.json
    assert_order_error_response(response, expected_status=400)
    assert response["code"] == "woocommerce_rest_invalid_coupon", (
        "Expected WooCommerce's invalid-coupon error, " f"got {response['code']!r}."
    )
    assert "minimum spend" in response["message"].lower(), (
        "Expected the error message to identify the minimum-spend restriction, "
        f"got {response['message']!r}."
    )

    logger.info(
        "Coupon %s was correctly rejected for Order ID=%r below minimum %s.",
        coupon_code,
        order_id,
        minimum_amount,
    )
