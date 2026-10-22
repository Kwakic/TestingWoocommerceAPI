"""
Order state provisioner.

This module applies already-prepared state data to an existing WooCommerce
Order through the existing OrdersHelper.

Architecture
------------
Existing Order
      |
      v
OrderStateBuilder
      |
      v
partial state mapping
      |
      v
OrderStateProvisioner
      |
      v
OrdersHelper
      |
      v
WooCommerce

The state provisioner is separate from ``OrderProvisioner``:

``OrderProvisioner`` creates a new Order from creation data.
``OrderStateProvisioner`` changes selected fields on an existing Order.

The provisioner deliberately does NOT:
- generate or customize Order state data;
- add defaults or modify the prepared state;
- validate HTTP status codes or response schemas;
- perform assertions or register cleanup resources;
- use pytest fixtures or access the database directly.

It validates the existing Order ID and prepared state mapping, delegates the
update to OrdersHelper, and returns the helper's response to the caller.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol

from EcommerceAPI.src.core.http_response import HttpResponse


class OrderStateHelper(Protocol):
    """Describe the order-helper operation used to update an existing Order.

    The provisioner depends only on this update operation. The Protocol
    documents that dependency without constructing or managing an
    ``OrdersHelper`` instance; helper lifetime and configuration remain the
    responsibility of the calling fixture or application layer.
    """

    def call_update_an_order(
        self,
        order_id: int,
        payload: dict[str, Any],
    ) -> HttpResponse:
        """Update an Order and return the underlying HTTP response."""
        ...


class OrderStateProvisioner:
    """Apply prepared state data to an existing WooCommerce Order.

    This class is the boundary between an in-memory state definition and the
    existing Order resource. It receives an Order ID and a mapping prepared
    by ``OrderStateBuilder``, then delegates the update operation to
    ``OrdersHelper``.

    Example:

        state = OrderStateBuilder().with_status("completed").build()
        provisioner = OrderStateProvisioner(order_helper)
        response = provisioner.provision(order_id=123, state=state)

    The provisioner returns the original ``HttpResponse``. The caller,
    normally a pytest fixture, remains responsible for validating the
    response and handling any resource lifecycle or cleanup requirements.
    """

    def __init__(self, order_helper: OrderStateHelper) -> None:
        """Initialize the provisioner with an Orders helper dependency.

        Args:
            order_helper: Existing helper responsible for Order API updates.

        The helper is injected rather than created here so this class remains
        independent of pytest fixtures and helper configuration.
        """
        self.order_helper = order_helper

    def provision(
        self,
        order_id: int,
        state: Mapping[str, Any],
    ) -> HttpResponse:
        """Apply prepared state data to an existing Order.

        Args:
            order_id:
                Positive WooCommerce Order ID of the resource to update.
            state:
                Non-empty mapping of the Order fields to change. The mapping
                is prepared by ``OrderStateBuilder`` or another valid state
                source; this method does not generate or enrich it.

        Returns:
            HttpResponse: The response returned by the Order update request.

        Raises:
            TypeError:
                If ``order_id`` is not an integer or ``state`` is not a
                mapping.
            ValueError:
                If ``order_id`` is not positive or ``state`` is empty.

        Notes:
            The provisioner intentionally does not validate the HTTP status
            or response body. Those checks belong to the caller/fixture.
        """
        # Reject bool explicitly because bool is a subclass of int in Python.
        if not isinstance(order_id, int) or isinstance(order_id, bool):
            raise TypeError("order_id must be an integer.")

        if order_id <= 0:
            raise ValueError("order_id must be greater than zero.")

        if not isinstance(state, Mapping):
            raise TypeError(
                "state must be a mapping containing the prepared order "
                "state to apply."
            )

        if not state:
            raise ValueError(
                "state cannot be empty. Prepare the order state before "
                "calling OrderStateProvisioner."
            )

        # Use the OrdersHelper compatibility method and return its response
        # unchanged for the caller to validate.
        return self.order_helper.call_update_an_order(
            order_id=order_id,
            payload=dict(state),
        )
