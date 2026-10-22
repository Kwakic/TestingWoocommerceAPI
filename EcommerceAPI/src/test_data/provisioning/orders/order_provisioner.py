"""Order test-data provisioner.

This module takes an already-prepared Order creation payload and delegates
creation to the Orders domain helper.

Architecture
------------
OrderFactory -> OrderBuilder -> OrderProvisioner -> OrdersHelper
             -> OrdersApi -> WooCommerce

The provisioner deliberately does not generate data, validate the response,
register cleanup, use pytest, access the database, or make test assertions.
Those responsibilities belong to the factory/builder, fixture, tests, or
appropriate lower-level data-access components.

The provisioner returns HttpResponse unchanged so the calling fixture can
validate the response, register ownership for cleanup, and return a validated
Order dictionary to the test.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol

from EcommerceAPI.src.core.http_response import HttpResponse


class OrderCreationHelper(Protocol):
    """Interface required from the Orders domain helper.

    The concrete OrdersHelper should implement this method contract. Using a
    Protocol documents the dependency and lets type checkers validate the
    provisioner's call without requiring the concrete helper module to exist
    before the Orders layer has been implemented.
    """

    def create_order(
        self,
        *,
        return_http_response: bool = False,
        **order_data: Any,
    ) -> HttpResponse:
        """Create an Order from prepared fields and optionally return HttpResponse."""
        ...


class OrderProvisioner:
    """Provision prepared Order data into WooCommerce.

    The factory/builder prepares the payload. This class only passes the
    prepared fields to the domain helper and returns its HttpResponse.

    Response validation and cleanup remain in the pytest fixture, keeping
    the provisioner reusable outside pytest.
    """

    def __init__(self, order_helper: OrderCreationHelper) -> None:
        """Initialize with the Orders helper responsible for API orchestration."""
        self.order_helper = order_helper

    def provision(self, order_data: Mapping[str, Any]) -> HttpResponse:
        """Create an Order from a non-empty, already-prepared payload.

        Args:
            order_data: Mapping produced by OrderFactory or OrderBuilder.

        Returns:
            The original HttpResponse from the Order creation request.

        Raises:
            TypeError: If ``order_data`` is not a mapping.
            ValueError: If ``order_data`` is empty.
        """
        if not isinstance(order_data, Mapping):
            raise TypeError(
                "order_data must be a mapping containing the Order creation payload."
            )

        if not order_data:
            raise ValueError(
                "order_data cannot be empty. "
                "Build the Order data with OrderFactory/OrderBuilder first."
            )

        # Match the Customer/Coupon provisioners: pass prepared fields as
        # keyword arguments and explicitly request the raw HttpResponse.
        return self.order_helper.create_order(
            return_http_response=True,
            **dict(order_data),
        )
