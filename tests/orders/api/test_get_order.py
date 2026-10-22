"""GET /orders integration tests.

These tests create valid Orders through the shared fixture, then exercise the
Orders GET endpoint independently of Order creation and update scenarios.
The fixture validates and registers setup resources for automatic cleanup.

Coverage:
    - Retrieve an Order by ID and verify its identity and line items.
    - Compare a retrieved Order with the database records.
    - Validate the not-found response for an unknown Order ID.
"""

import logging

import pytest

from EcommerceAPI.src.entities.orders.validators.order_db_validators import (
    assert_order_matches_db,
)
from EcommerceAPI.src.entities.orders.validators.order_validators import (
    assert_order_identity,
    assert_order_line_items,
    assert_order_not_found_error,
    assert_valid_order_response,
)


logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.orders, pytest.mark.integration]


# -------------------------------------------
# 🧪 Test: GET Order By ID
# -------------------------------------------
@pytest.mark.sanity
@pytest.mark.smoke
@pytest.mark.contract
def test_get_order_by_id(
    order_helper,
    create_valid_product,
    create_valid_order,
):
    """Retrieve a valid Order by ID and verify its identity and line items.

    Fixture responsibilities:
        - Create a Product for the Order line item.
        - Create and validate a valid Order.
        - Register both resources for automatic cleanup.

    Test flow:
        1. Create a Product and an Order through their fixtures.
        2. Retrieve the Order through GET /orders/{id}.
        3. Assert the GET transport status.
        4. Validate the Order response structure.
        5. Verify the Order ID and Product line item.
    """

    # -------------------------------------------
    # Step 1 — Create a Product and Order
    # -------------------------------------------
    logger.info("Creating a Product for the Order line item.")
    product = create_valid_product()
    product_id = product["id"]

    order = create_valid_order(product_id=product_id)
    order_id = order["id"]

    # -------------------------------------------
    # Step 2 — Retrieve the Order by ID
    # -------------------------------------------
    logger.info("Fetching Order ID=%r.", order_id)
    response = order_helper.get_order_by_id(
        order_id=order_id,
        return_http_response=True,
    )

    # -------------------------------------------
    # Step 3 — Transport validation
    # -------------------------------------------
    # The test owns the status assertion because GET is the operation under test.
    assert response.status_code == 200, (
        f"Expected HTTP 200, got {response.status_code}. " f"Response: {response.text}"
    )

    # -------------------------------------------
    # Step 4 — Response structure validation
    # -------------------------------------------
    order_model = assert_valid_order_response(response.json)

    # -------------------------------------------
    # Step 5 — Order identity and line-item validation
    # -------------------------------------------
    assert_order_identity(order_model, expected_id=order_id)
    assert_order_line_items(
        order_model,
        expected_line_items=[{"product_id": product_id, "quantity": 1}],
    )

    logger.info("Retrieved Order ID=%r with Product ID=%r.", order_id, product_id)


# -------------------------------------------
# 🗄 Test: GET Order By ID — API/DB Consistency
# -------------------------------------------
@pytest.mark.contract
def test_get_order_by_id_matches_db(
    order_helper,
    orders_dao,
    create_valid_product,
    create_valid_order,
):
    """Verify that a retrieved Order matches its WooCommerce database records.

    Test flow:
        1. Create a Product and an Order through their fixtures.
        2. Retrieve the Order through GET /orders/{id}.
        3. Validate the GET response structure.
        4. Retrieve the Order, metadata, and line-item records through OrdersDAO.
        5. Compare the API response with the database records.
    """

    # -------------------------------------------
    # Step 1 — Create a Product and Order
    # -------------------------------------------
    product = create_valid_product()
    product_id = product["id"]
    order = create_valid_order(product_id=product_id)
    order_id = order["id"]

    # -------------------------------------------
    # Step 2 — Retrieve and validate the Order
    # -------------------------------------------
    response = order_helper.get_order_by_id(
        order_id=order_id,
        return_http_response=True,
    )

    # The test owns the status assertion for the GET operation.
    assert response.status_code == 200, (
        f"Expected HTTP 200, got {response.status_code}. " f"Response: {response.text}"
    )

    order_model = assert_valid_order_response(response.json)
    assert_order_identity(order_model, expected_id=order_id)

    # -------------------------------------------
    # Step 3 — Retrieve the corresponding database records
    # -------------------------------------------
    db_order = orders_dao.get_order_by_id(order_id)
    db_order_meta = orders_dao.get_order_metadata(order_id)
    db_order_lines = orders_dao.get_order_lines_by_order_id(order_id)
    db_order_item_meta = {
        item["order_item_id"]: orders_dao.get_order_items_details(item["order_item_id"])
        for item in db_order_lines
        if item["order_item_type"] == "line_item"
    }

    # -------------------------------------------
    # Step 4 — Compare API and database values
    # -------------------------------------------
    assert_order_matches_db(
        order_model,
        db_order,
        db_order_meta,
        db_order_lines,
        db_order_item_meta,
    )

    logger.info("GET Order ID=%r matches its database records.", order_id)


# -------------------------------------------
# ⚠️ Test: GET Non-Existent Order
# -------------------------------------------
@pytest.mark.negative
@pytest.mark.contract
@pytest.mark.regression
def test_get_nonexistent_order(order_helper):
    """Validate the not-found response when retrieving an unknown Order ID.

    No setup resource is required because the unknown ID is the scenario under
    test.

    Test flow:
        1. Request an Order ID that does not exist.
        2. Assert that the GET operation returns HTTP 404.
        3. Validate the WooCommerce not-found error contract.
    """

    non_existent_order_id = 999999999

    # -------------------------------------------
    # Step 1 — Request the unknown Order ID
    # -------------------------------------------
    logger.info("Requesting non-existent Order ID=%r.", non_existent_order_id)
    response = order_helper.get_order_by_id(
        order_id=non_existent_order_id,
        return_http_response=True,
    )

    # -------------------------------------------
    # Step 2 — Transport validation
    # -------------------------------------------
    assert response.status_code == 404, (
        f"Expected HTTP 404, got {response.status_code}. " f"Response: {response.text}"
    )

    # -------------------------------------------
    # Step 3 — Error response validation
    # -------------------------------------------
    assert_order_not_found_error(response.json)

    logger.info(
        "Order not-found response validated for ID=%r.",
        non_existent_order_id,
    )
