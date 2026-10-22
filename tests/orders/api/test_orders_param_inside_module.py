"""Parameterized integration tests for Coupon behavior on WooCommerce Orders.

Coupon and Product setup uses the entity fixtures. Eligible scenarios create
an Order with the Coupon through create_valid_order and verify its calculated
discount and shipping amount.

Below-minimum scenarios create a valid Order first, then attempt to apply the
Coupon through OrderStateBuilder and OrderStateProvisioner. This keeps the
Order registered for cleanup if WooCommerce rejects the update.
"""

import logging
from decimal import Decimal

import pytest

from EcommerceAPI.src.entities.orders.validators.order_validators import (
    assert_order_error_response,
    assert_order_line_items,
    assert_valid_order_response,
)
from EcommerceAPI.src.test_data.builders.orders.order_state_builder import (
    OrderStateBuilder,
)
from EcommerceAPI.src.test_data.provisioning.orders.order_state_provisioner import (
    OrderStateProvisioner,
)


logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.orders, pytest.mark.integration]


# ---------------------------------------
# 🧪 Test: Eligible Coupon Scenarios
# ---------------------------------------
@pytest.mark.contract
@pytest.mark.regression
@pytest.mark.parametrize(
    "discount_type, amount, minimum_amount, product_price_offset, free_shipping",
    [
        pytest.param(
            "percent",
            "50.00",
            "35.00",
            "5.00",
            False,
            id="percentage-discount",
        ),
        pytest.param(
            "fixed_cart",
            "15.00",
            "30.00",
            "10.00",
            False,
            id="fixed-cart-discount",
        ),
        pytest.param(
            "fixed_cart",
            "0.00",
            "0.00",
            "5.00",
            True,
            id="free-shipping-only",
        ),
    ],
)
def test_apply_eligible_coupon_to_order(
    discount_type,
    amount,
    minimum_amount,
    product_price_offset,
    free_shipping,
    create_valid_coupon,
    create_valid_product,
    create_valid_order,
    order_helper,
):
    """Apply an eligible Coupon and verify its Order discount and shipping.

    The Product price is derived from the Coupon minimum plus the scenario
    offset. The fixture pipeline owns creation and cleanup for the Coupon,
    Product, and Order.
    """

    # -------------------------------------------
    # Step 1 — Create the Coupon for this scenario
    # -------------------------------------------
    coupon = create_valid_coupon(
        discount_type=discount_type,
        amount=amount,
        minimum_amount=minimum_amount,
        free_shipping=free_shipping,
    )
    coupon_id = coupon["id"]
    coupon_code = coupon["code"]

    # -------------------------------------------
    # Step 2 — Create a Product that meets the minimum spend
    # -------------------------------------------
    product_price = (Decimal(minimum_amount) + Decimal(product_price_offset)).quantize(
        Decimal("0.01")
    )
    product = create_valid_product(
        regular_price=f"{product_price:.2f}",
    )
    product_id = product["id"]

    # -------------------------------------------
    # Step 3 — Create an Order with the Coupon and shipping line
    # -------------------------------------------
    shipping_total = Decimal("0.00") if free_shipping else Decimal("5.00")
    shipping_lines = [
        {
            "method_id": "flat_rate",
            "method_title": "Flat Rate",
            "total": f"{shipping_total:.2f}",
        }
    ]
    order = create_valid_order(
        product_id=product_id,
        shipping_lines=shipping_lines,
        coupon_lines=[{"code": coupon_code}],
    )
    order_id = order["id"]

    # -------------------------------------------
    # Step 4 — Retrieve the Order and validate its structure
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

    # -------------------------------------------
    # Step 5 — Verify the discount and shipping totals
    # -------------------------------------------
    if discount_type == "percent":
        expected_discount = product_price * Decimal(amount) / Decimal("100")
    else:
        expected_discount = min(Decimal(amount), product_price)

    expected_discount = expected_discount.quantize(Decimal("0.01"))
    coupon_line = applied_coupon_lines[0]

    assert (
        coupon_line.discount is not None
    ), f"Expected a discount amount for Coupon {coupon_code!r}."
    assert Decimal(coupon_line.discount) == expected_discount, (
        f"Expected Coupon discount {expected_discount}, " f"got {coupon_line.discount}."
    )
    assert Decimal(api_order.discount_total or "0.00") == expected_discount, (
        f"Expected Order discount_total {expected_discount}, "
        f"got {api_order.discount_total}."
    )
    assert Decimal(api_order.shipping_total or "0.00") == shipping_total, (
        f"Expected shipping_total {shipping_total}, " f"got {api_order.shipping_total}."
    )

    logger.info(
        "Scenario %s applied Coupon ID=%r to Order ID=%r "
        "(discount=%s, shipping=%s).",
        discount_type,
        coupon_id,
        order_id,
        expected_discount,
        shipping_total,
    )


# ---------------------------------------
# ⚠️ Test: Coupon Rejected Below Minimum
# ---------------------------------------
@pytest.mark.negative
@pytest.mark.contract
@pytest.mark.regression
@pytest.mark.parametrize(
    "discount_type, amount, minimum_amount, product_price_offset",
    [
        pytest.param(
            "percent",
            "50.00",
            "35.00",
            "-10.00",
            id="percentage-below-minimum",
        ),
        pytest.param(
            "fixed_cart",
            "10.00",
            "40.00",
            "-5.00",
            id="fixed-cart-below-minimum",
        ),
    ],
)
def test_coupon_application_rejected_below_minimum(
    discount_type,
    amount,
    minimum_amount,
    product_price_offset,
    create_valid_coupon,
    create_valid_product,
    create_valid_order,
    order_helper,
):
    """Reject applying a Coupon when the Order is below its minimum spend.

    The Order is created without a Coupon and registered by create_valid_order.
    The negative operation updates that existing Order, so the resource
    remains owned by the fixture even when WooCommerce rejects the Coupon.
    """

    # -------------------------------------------
    # Step 1 — Create a Coupon with a minimum spend
    # -------------------------------------------
    coupon = create_valid_coupon(
        discount_type=discount_type,
        amount=amount,
        minimum_amount=minimum_amount,
    )
    coupon_code = coupon["code"]

    # -------------------------------------------
    # Step 2 — Create a Product below the minimum spend
    # -------------------------------------------
    product_price = (Decimal(minimum_amount) + Decimal(product_price_offset)).quantize(
        Decimal("0.01")
    )
    product = create_valid_product(
        regular_price=f"{product_price:.2f}",
    )
    product_id = product["id"]

    # -------------------------------------------
    # Step 3 — Create the Order without the Coupon
    # -------------------------------------------
    order = create_valid_order(product_id=product_id)
    order_id = order["id"]

    # -------------------------------------------
    # Step 4 — Attempt to add the ineligible Coupon
    # -------------------------------------------
    order_state = OrderStateBuilder().with_coupon_lines([{"code": coupon_code}]).build()
    order_state_provisioner = OrderStateProvisioner(order_helper)
    response = order_state_provisioner.provision(
        order_id=order_id,
        state=order_state,
    )

    # -------------------------------------------
    # Step 5 — Validate the Coupon restriction error
    # -------------------------------------------
    assert response.status_code == 400, (
        "Expected HTTP 400 when applying a Coupon below its minimum spend, "
        f"got {response.status_code}. "
        f"Response: {response.text[:300]}"
    )

    error_response = response.json
    assert_order_error_response(error_response, expected_status=400)
    assert error_response["code"] == "woocommerce_rest_invalid_coupon", (
        "Expected WooCommerce's invalid-coupon error, "
        f"got {error_response['code']!r}."
    )
    assert "minimum spend" in error_response["message"].lower(), (
        "Expected the error message to identify the minimum-spend restriction, "
        f"got {error_response['message']!r}."
    )

    logger.info(
        "Coupon %s correctly rejected for Order ID=%r below minimum %s.",
        coupon_code,
        order_id,
        minimum_amount,
    )
