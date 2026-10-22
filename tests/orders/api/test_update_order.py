"""Order update integration tests.

Each test creates its Order through create_valid_order so setup validation and
cleanup registration stay with the shared fixture. Partial update data is
prepared by OrderStateBuilder and applied by OrderStateProvisioner through the
existing OrdersHelper and Orders API layers.
"""

import logging

import pytest

from EcommerceAPI.src.entities.orders.validators.order_validators import (
    assert_order_error_response,
    assert_order_identity,
    assert_order_status,
    assert_order_updated_successfully,
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
# 🧪 Test: Update Order Status
# ---------------------------------------
@pytest.mark.smoke
@pytest.mark.contract
@pytest.mark.parametrize(
    "new_status",
    [
        pytest.param("cancelled", id="cancelled"),
        pytest.param("completed", id="completed"),
        pytest.param("on-hold", id="on-hold"),
    ],
)
def test_update_order_status(
    new_status,
    order_helper,
    create_valid_product,
    create_valid_order,
):
    """Update an Order to a supported status and verify it persists.

    Test flow:

        1. Create a Product and a valid Order through their fixtures.
        2. Build a partial state containing the requested status.
        3. Apply the state through OrderStateProvisioner.
        4. Validate the update response and retrieve the Order again.
    """

    # -------------------------------------------
    # Step 1 — Create a Product and Order
    # -------------------------------------------
    product = create_valid_product()
    product_id = product["id"]

    order = create_valid_order(product_id=product_id)
    order_id = order["id"]
    original_status = order["status"]

    assert original_status != new_status, (
        f"Order ID={order_id} already has status {new_status!r}; "
        "the update scenario requires a status change."
    )

    # -------------------------------------------
    # Step 2 — Build the partial Order state
    # -------------------------------------------
    order_state = OrderStateBuilder().with_status(new_status).build()

    # -------------------------------------------
    # Step 3 — Apply the state through the provisioner
    # -------------------------------------------
    order_state_provisioner = OrderStateProvisioner(order_helper)
    response = order_state_provisioner.provision(
        order_id=order_id,
        state=order_state,
    )

    updated_order = assert_order_updated_successfully(response)
    assert_order_identity(updated_order, expected_id=order_id)
    assert_order_status(updated_order, expected_status=new_status)

    # -------------------------------------------
    # Step 4 — Confirm the updated status through a fresh API read
    # -------------------------------------------
    retrieved_order_data = order_helper.get_order_by_id(order_id=order_id)
    retrieved_order = assert_valid_order_response(retrieved_order_data)

    assert_order_identity(retrieved_order, expected_id=order_id)
    assert_order_status(retrieved_order, expected_status=new_status)

    logger.info(
        "Order ID=%r status updated from %s to %s.",
        order_id,
        original_status,
        new_status,
    )


# ---------------------------------------
# 🧪 Test: Update Order Customer Note
# ---------------------------------------
@pytest.mark.contract
@pytest.mark.regression
def test_update_order_customer_note(
    order_helper,
    create_valid_product,
    create_valid_order,
):
    """Update an Order customer note and verify it persists through the API."""

    # -------------------------------------------
    # Step 1 — Create a Product and Order
    # -------------------------------------------
    product = create_valid_product()
    product_id = product["id"]

    order = create_valid_order(product_id=product_id)
    order_id = order["id"]

    # -------------------------------------------
    # Step 2 — Build and apply the partial note state
    # -------------------------------------------
    customer_note = "Updated by the Order API integration test."
    order_state = OrderStateBuilder().with_customer_note(customer_note).build()

    order_state_provisioner = OrderStateProvisioner(order_helper)
    response = order_state_provisioner.provision(
        order_id=order_id,
        state=order_state,
    )

    updated_order = assert_order_updated_successfully(response)
    assert_order_identity(updated_order, expected_id=order_id)
    assert updated_order.customer_note == customer_note, (
        f"Expected customer_note {customer_note!r}, "
        f"got {updated_order.customer_note!r}."
    )

    # -------------------------------------------
    # Step 3 — Confirm the note through a fresh API read
    # -------------------------------------------
    retrieved_order_data = order_helper.get_order_by_id(order_id=order_id)
    retrieved_order = assert_valid_order_response(retrieved_order_data)

    assert_order_identity(retrieved_order, expected_id=order_id)
    assert retrieved_order.customer_note == customer_note, (
        f"Customer note was not persisted. Expected {customer_note!r}, "
        f"got {retrieved_order.customer_note!r}."
    )

    logger.info(
        "Order ID=%r customer note updated and verified.",
        order_id,
    )


# ---------------------------------------
# ⚠️ Test: Reject an Invalid Order Status
# ---------------------------------------
@pytest.mark.negative
@pytest.mark.contract
@pytest.mark.regression
def test_update_order_status_to_invalid_value(
    order_helper,
    create_valid_product,
    create_valid_order,
):
    """Reject an unsupported status and verify the Order remains unchanged.

    The Order is created through the standard fixture and remains registered
    for cleanup. The invalid partial state is sent through the same update
    provisioner used by successful state changes.
    """

    # -------------------------------------------
    # Step 1 — Create a Product and baseline Order
    # -------------------------------------------
    product = create_valid_product()
    product_id = product["id"]

    order = create_valid_order(product_id=product_id)
    order_id = order["id"]
    original_status = order["status"]

    # -------------------------------------------
    # Step 2 — Build and submit an unsupported status
    # -------------------------------------------
    invalid_status = "not-a-valid-order-status"
    order_state = OrderStateBuilder().with_status(invalid_status).build()

    order_state_provisioner = OrderStateProvisioner(order_helper)
    response = order_state_provisioner.provision(
        order_id=order_id,
        state=order_state,
    )

    # -------------------------------------------
    # Step 3 — Validate the API error contract
    # -------------------------------------------
    assert response.status_code == 400, (
        "Expected HTTP 400 for an unsupported Order status, "
        f"got {response.status_code}. "
        f"Response: {response.text[:300]}"
    )

    error_response = response.json
    assert_order_error_response(error_response, expected_status=400)
    assert error_response["code"] == "rest_invalid_param", (
        "Expected the REST invalid-parameter error code, "
        f"got {error_response['code']!r}."
    )
    assert "status" in error_response["message"].lower(), (
        "Expected the error message to identify the invalid status field, "
        f"got {error_response['message']!r}."
    )

    # -------------------------------------------
    # Step 4 — Confirm the rejected update did not change the Order
    # -------------------------------------------
    current_order_data = order_helper.get_order_by_id(order_id=order_id)
    current_order = assert_valid_order_response(current_order_data)

    assert_order_identity(current_order, expected_id=order_id)
    assert_order_status(current_order, expected_status=original_status)

    logger.info(
        "Invalid status %r rejected; Order ID=%r remains %s.",
        invalid_status,
        order_id,
        original_status,
    )
