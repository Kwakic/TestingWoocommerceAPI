"""JSON-driven integration tests for Coupon behavior on WooCommerce Orders.

Scenario data lives in tests/orders/data/coupon_scenarios.json. Valid Coupons
and Products are created through their fixtures. Successful Order creation
uses create_valid_order; below-minimum cases apply a Coupon to an existing,
fixture-owned Order so cleanup remains registered if WooCommerce rejects it.
"""

import logging
from decimal import Decimal

import pytest

from tests.orders.data.scenario_loader import load_coupon_scenarios

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

COUPON_SCENARIOS = load_coupon_scenarios()
ELIGIBLE_SCENARIOS = [
    scenario
    for scenario in COUPON_SCENARIOS
    if scenario["expected_outcome"] == "applied"
]
BELOW_MINIMUM_SCENARIOS = [
    scenario
    for scenario in COUPON_SCENARIOS
    if scenario["expected_outcome"] == "rejected_below_minimum"
]


# ---------------------------------------
# 🧪 Test: Apply Eligible JSON Scenarios
# ---------------------------------------
@pytest.mark.contract
@pytest.mark.regression
@pytest.mark.parametrize(
    "scenario",
    ELIGIBLE_SCENARIOS,
    ids=lambda scenario: scenario["name"],
)
def test_apply_coupon_scenario_from_json(
    scenario,
    create_valid_coupon,
    create_valid_product,
    create_valid_order,
    order_helper,
):
    """Apply each eligible JSON-defined Coupon and verify the Order totals.

    The test checks that the scenario's derived product price meets its
    minimum spend and that the JSON expected discount matches the configured
    discount rule before comparing those expectations with the API response.
    """

    # -------------------------------------------
    # Step 1 — Create the Coupon from scenario data
    # -------------------------------------------
    free_shipping = scenario.get("free_shipping", False)
    coupon = create_valid_coupon(
        discount_type=scenario["discount_type"],
        amount=scenario["amount"],
        minimum_amount=scenario["minimum_amount"],
        free_shipping=free_shipping,
    )
    coupon_id = coupon["id"]
    coupon_code = coupon["code"]

    # -------------------------------------------
    # Step 2 — Create a Product that meets minimum spend
    # -------------------------------------------
    minimum_amount = Decimal(scenario["minimum_amount"])
    product_price = (
        minimum_amount + Decimal(scenario["product_price_offset"])
    ).quantize(Decimal("0.01"))

    assert product_price >= minimum_amount, (
        f"Eligible scenario {scenario['name']!r} has product price "
        f"{product_price} below minimum {minimum_amount}."
    )

    product = create_valid_product(
        regular_price=f"{product_price:.2f}",
    )
    product_id = product["id"]

    # -------------------------------------------
    # Step 3 — Create the Order with Coupon and shipping
    # -------------------------------------------
    expected_shipping_total = Decimal(scenario["expected_shipping_total"])
    shipping_lines = [
        {
            "method_id": "flat_rate",
            "method_title": "Flat Rate",
            "total": f"{expected_shipping_total:.2f}",
        }
    ]
    order = create_valid_order(
        product_id=product_id,
        shipping_lines=shipping_lines,
        coupon_lines=[{"code": coupon_code}],
    )
    order_id = order["id"]

    # -------------------------------------------
    # Step 4 — Retrieve and validate the Order response
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
        f"Scenario {scenario['name']!r}: expected Coupon {coupon_code!r} "
        f"on Order ID={order_id}, found {len(applied_coupon_lines)}."
    )

    # -------------------------------------------
    # Step 5 — Verify JSON expectations and API totals
    # -------------------------------------------
    amount = Decimal(scenario["amount"])
    if scenario["discount_type"] == "percent":
        calculated_discount = product_price * amount / Decimal("100")
    else:
        calculated_discount = min(amount, product_price)

    calculated_discount = calculated_discount.quantize(Decimal("0.01"))
    expected_discount = Decimal(scenario["expected_discount"])

    assert calculated_discount == expected_discount, (
        f"Scenario {scenario['name']!r} has inconsistent expected_discount: "
        f"JSON says {expected_discount}, rule calculates {calculated_discount}."
    )

    coupon_line = applied_coupon_lines[0]
    assert (
        coupon_line.discount is not None
    ), f"Scenario {scenario['name']!r}: applied Coupon has no discount value."
    assert Decimal(coupon_line.discount) == expected_discount, (
        f"Scenario {scenario['name']!r}: expected coupon-line discount "
        f"{expected_discount}, got {coupon_line.discount}."
    )
    assert Decimal(api_order.discount_total or "0.00") == expected_discount, (
        f"Scenario {scenario['name']!r}: expected Order discount_total "
        f"{expected_discount}, got {api_order.discount_total}."
    )
    assert Decimal(api_order.shipping_total or "0.00") == expected_shipping_total, (
        f"Scenario {scenario['name']!r}: expected shipping total "
        f"{expected_shipping_total}, got {api_order.shipping_total}."
    )

    logger.info(
        "Scenario %r applied Coupon ID=%r to Order ID=%r "
        "(discount=%s, shipping=%s).",
        scenario["name"],
        coupon_id,
        order_id,
        expected_discount,
        expected_shipping_total,
    )


# ---------------------------------------
# ⚠️ Test: Reject Below-Minimum JSON Scenarios
# ---------------------------------------
@pytest.mark.negative
@pytest.mark.contract
@pytest.mark.regression
@pytest.mark.parametrize(
    "scenario",
    BELOW_MINIMUM_SCENARIOS,
    ids=lambda scenario: scenario["name"],
)
def test_reject_coupon_scenario_below_minimum_from_json(
    scenario,
    create_valid_coupon,
    create_valid_product,
    create_valid_order,
    order_helper,
):
    """Reject each JSON-defined Coupon application below its minimum spend.

    A valid Order is created before applying the Coupon. The expected failure
    therefore leaves an Order registered with the shared cleanup lifecycle.
    """

    # -------------------------------------------
    # Step 1 — Create the Coupon from scenario data
    # -------------------------------------------
    coupon = create_valid_coupon(
        discount_type=scenario["discount_type"],
        amount=scenario["amount"],
        minimum_amount=scenario["minimum_amount"],
    )
    coupon_code = coupon["code"]

    # -------------------------------------------
    # Step 2 — Create a Product below minimum spend
    # -------------------------------------------
    minimum_amount = Decimal(scenario["minimum_amount"])
    product_price = (
        minimum_amount + Decimal(scenario["product_price_offset"])
    ).quantize(Decimal("0.01"))

    assert product_price < minimum_amount, (
        f"Rejected scenario {scenario['name']!r} has product price "
        f"{product_price} that meets or exceeds minimum {minimum_amount}."
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
    # Step 4 — Attempt to apply the below-minimum Coupon
    # -------------------------------------------
    order_state = OrderStateBuilder().with_coupon_lines([{"code": coupon_code}]).build()
    order_state_provisioner = OrderStateProvisioner(order_helper)
    response = order_state_provisioner.provision(
        order_id=order_id,
        state=order_state,
    )

    # -------------------------------------------
    # Step 5 — Validate the expected WooCommerce error
    # -------------------------------------------
    assert response.status_code == 400, (
        f"Scenario {scenario['name']!r}: expected HTTP 400, "
        f"got {response.status_code}. "
        f"Response: {response.text[:300]}"
    )

    error_response = response.json
    assert_order_error_response(error_response, expected_status=400)
    assert error_response["code"] == scenario["expected_error_code"], (
        f"Scenario {scenario['name']!r}: expected error code "
        f"{scenario['expected_error_code']!r}, got {error_response['code']!r}."
    )
    expected_message = scenario["expected_error_message_contains"].lower()
    assert expected_message in error_response["message"].lower(), (
        f"Scenario {scenario['name']!r}: expected error message to contain "
        f"{expected_message!r}, got {error_response['message']!r}."
    )

    logger.info(
        "Scenario %r correctly rejected Coupon %s for Order ID=%r.",
        scenario["name"],
        coupon_code,
        order_id,
    )
