"""Order creation integration tests.

These tests create Orders through the shared valid-data fixture. The fixture
uses OrderBuilder and OrderFactory to prepare the request, provisions through
OrderProvisioner, validates the HTTP 201 response and Order structure, and
registers each created Order for teardown cleanup.

An Order needs at least one existing Product. Tests create Products with
create_valid_product and pass their IDs to create_valid_order.
"""

import logging

import pytest

from EcommerceAPI.src.entities.orders.validators.order_db_validators import (
    assert_order_matches_db,
)
from EcommerceAPI.src.entities.orders.validators.order_validators import (
    assert_order_customer_id,
    assert_order_line_items,
    assert_valid_order_response,
)


logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.orders, pytest.mark.integration]


# ---------------------------
# 🧪 Test: Minimal Order Creation
# ---------------------------
@pytest.mark.sanity
@pytest.mark.smoke
@pytest.mark.contract
def test_create_single_order(
    order_helper,
    orders_dao,
    create_valid_product,
    create_valid_order,
):
    """Create a minimal Order and compare its API response with the database.

    Test flow:

        1. Create a Product for the Order line item.
        2. Create an Order with the standard fixture.
        3. Retrieve the Order through the API.
        4. Compare API data with the Order and line-item database records.
    """

    # -------------------------------------------
    # Step 1 — Create a Product for the Order
    # -------------------------------------------
    logger.info("🛠 Creating a Product for the Order line item.")
    product = create_valid_product()
    product_id = product["id"]

    # -------------------------------------------
    # Step 2 — Create an Order
    # -------------------------------------------
    # The fixture sends these scenario values through OrderBuilder and
    # OrderFactory, then provisions the prepared payload through the API.
    order = create_valid_order(product_id=product_id)
    order_id = order["id"]

    # -------------------------------------------
    # Step 3 — Retrieve the Order through the API
    # -------------------------------------------
    api_order_data = order_helper.get_order_by_id(order_id=order_id)
    api_order = assert_valid_order_response(api_order_data)

    # -------------------------------------------
    # Step 4 — Compare the API response with database records
    # -------------------------------------------
    db_order = orders_dao.get_order_by_id(order_id)
    db_order_meta = orders_dao.get_order_metadata(order_id)
    db_order_lines = orders_dao.get_order_lines_by_order_id(order_id)
    db_order_item_meta = {
        item["order_item_id"]: orders_dao.get_order_items_details(item["order_item_id"])
        for item in db_order_lines
        if item["order_item_type"] == "line_item"
    }

    assert_order_matches_db(
        api_order,
        db_order,
        db_order_meta,
        db_order_lines,
        db_order_item_meta,
    )

    # Confirm the Order references the Product created for this scenario.
    assert_order_line_items(
        api_order,
        expected_line_items=[{"product_id": product_id, "quantity": 1}],
    )

    logger.info("🎯 Full validation complete for Order ID: %r", order_id)


# ---------------------------
# 🧪 Test: Order Line-Item Quantity
# ---------------------------
@pytest.mark.regression
@pytest.mark.contract
def test_create_order_with_multiple_units(
    order_helper,
    create_valid_product,
    create_valid_order,
):
    """Create an Order line item with a quantity greater than the default."""

    # -------------------------------------------
    # Step 1 — Create a Product for the Order
    # -------------------------------------------
    product = create_valid_product()
    product_id = product["id"]

    # -------------------------------------------
    # Step 2 — Create an Order for two units
    # -------------------------------------------
    order = create_valid_order(product_id=product_id, quantity=2)
    order_id = order["id"]

    # -------------------------------------------
    # Step 3 — Verify the quantity returned by the API
    # -------------------------------------------
    api_order_data = order_helper.get_order_by_id(order_id=order_id)
    api_order = assert_valid_order_response(api_order_data)

    assert_order_line_items(
        api_order,
        expected_line_items=[{"product_id": product_id, "quantity": 2}],
    )


# ---------------------------
# 🧪 Test: Order with Multiple Products
# ---------------------------
@pytest.mark.regression
@pytest.mark.contract
def test_create_order_with_multiple_line_items(
    order_helper,
    create_valid_product,
    create_valid_order,
):
    """Create an Order with two Products and verify both line items."""

    # -------------------------------------------
    # Step 1 — Create the Products for the Order
    # -------------------------------------------
    first_product = create_valid_product()
    first_product_id = first_product["id"]

    second_product = create_valid_product()
    second_product_id = second_product["id"]

    # -------------------------------------------
    # Step 2 — Create an Order with both Products
    # -------------------------------------------
    line_items = [
        {"product_id": first_product_id, "quantity": 1},
        {"product_id": second_product_id, "quantity": 3},
    ]
    order = create_valid_order(line_items=line_items)
    order_id = order["id"]

    # -------------------------------------------
    # Step 3 — Verify both line items through the API
    # -------------------------------------------
    api_order_data = order_helper.get_order_by_id(order_id=order_id)
    api_order = assert_valid_order_response(api_order_data)

    assert_order_line_items(
        api_order,
        expected_line_items=line_items,
    )


# ---------------------------
# 🧪 Test: Order Associated with a Customer
# ---------------------------
@pytest.mark.regression
@pytest.mark.contract
def test_create_order_for_registered_customer(
    order_helper,
    create_valid_product,
    create_valid_customer,
    create_valid_order,
):
    """Create an Order for an existing Customer and verify its association."""

    # -------------------------------------------
    # Step 1 — Create the Product and Customer
    # -------------------------------------------
    product = create_valid_product()
    product_id = product["id"]

    customer = create_valid_customer()
    customer_id = customer["id"]

    # -------------------------------------------
    # Step 2 — Create an Order associated with the Customer
    # -------------------------------------------
    order = create_valid_order(
        product_id=product_id,
        customer_id=customer_id,
    )
    order_id = order["id"]

    # -------------------------------------------
    # Step 3 — Verify the Customer association and line item
    # -------------------------------------------
    api_order_data = order_helper.get_order_by_id(order_id=order_id)
    api_order = assert_valid_order_response(api_order_data)

    assert_order_customer_id(api_order, expected_customer_id=customer_id)
    assert_order_line_items(
        api_order,
        expected_line_items=[{"product_id": product_id, "quantity": 1}],
    )
