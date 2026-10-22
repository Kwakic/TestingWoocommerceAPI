"""Pytest fixtures for the WooCommerce Orders API.

This module provides Order-specific setup fixtures. ``create_valid_order``
builds prepared creation data, provisions the Order, validates the successful
response, and registers the created resource with the shared cleanup lifecycle.

Fixtures
--------
- ``create_valid_order`` returns a callable for creating a validated Order.
  It uses ``OrderBuilder`` and ``OrderFactory`` to prepare the payload and
  ``OrderProvisioner`` to cross the system boundary.
- ``order_api_raw`` returns the configured ``APIClient`` for tests that need
  direct control over Order API calls.

An Order requires an existing Product. Supply ``product_id`` for the default
line item or provide complete ``line_items``. The fixture does not create a
Product implicitly.

Architecture
------------
    OrderBuilder
        ↓
    OrderFactory
        ↓
    OrderProvisioner
        ↓
    OrdersHelper / OrdersApi
        ↓
    WooCommerce
        ↓
    Fixture validation
        ↓
    Ownership registration
        ↓
    shared_api_resources teardown cleanup
"""

from __future__ import annotations

import logging
from typing import Callable

import pytest

from EcommerceAPI.src.entities.orders.validators.order_validators import (
    assert_valid_order_response,
)

from EcommerceAPI.src.test_data.builders.orders.order_builder import OrderBuilder
from EcommerceAPI.src.test_data.provisioning.orders.order_provisioner import (
    OrderProvisioner,
)

log = logging.getLogger(__name__)


@pytest.fixture(scope="function")
def create_valid_order(shared_api_resources) -> Callable[..., dict]:
    """Create a valid Order through the test-data and provisioning layers.

    This fixture is the test-facing gatekeeper for Order setup. It prepares
    scenario data through ``OrderBuilder``/``OrderFactory``, provisions via
    ``OrderProvisioner``, enforces the HTTP creation contract, validates the
    response structure, and registers the created Order for teardown cleanup.

    Supply an existing ``product_id`` for the default line item, or pass a
    complete ``line_items`` list. Additional creation fields supported by
    ``OrderFactory`` may be passed as keyword arguments.

    Return contract:
        - Returns the validated Order response as a dictionary.
        - Does not expose ``HttpResponse`` to the test.
        - Registers ownership unless ``skip_cleanup=True``.

    Usage::

        order = create_valid_order(product_id=existing_product["id"])
        assert order["line_items"]

    Args:
        shared_api_resources: Shared resources containing the OrdersHelper and
            resource registration function.

    Returns:
        Callable[..., dict]: A function that creates a valid Order from
        scenario-specific creation fields.

    Raises:
        TypeError: If required product/line-item data is missing or an
            unsupported field is passed to ``OrderFactory``.
        AssertionError: If the create status is not 201 or the response
            structure does not match the Order model.
    """
    order_helper = shared_api_resources["orders_helper"]
    register = shared_api_resources["register_resource"]
    order_provisioner = OrderProvisioner(order_helper)

    def _create_order(skip_cleanup: bool = False, **kwargs) -> dict:
        """Create a valid Order for a positive test (happy path only).

        Flow:
            1. Build scenario-specific creation data.
            2. Provision the Order through ``OrderProvisioner``.
            3. Assert the creation status is HTTP 201.
            4. Validate the response structure.
            5. Register the Order for teardown cleanup.

        Args:
            skip_cleanup: If true, do not register the Order for cleanup.
            **kwargs: Scenario-specific creation fields supported by
                ``OrderFactory``. Supply ``product_id`` or ``line_items``.

        Returns:
            dict: The validated Order response body. The fixture uses the
                ``HttpResponse`` internally and returns only parsed JSON.

        Raises:
            AssertionError: If the creation status is not 201 or the response
                fails Order structure validation.
        """
        # -----------------------------------------
        # 1️⃣ Build Order creation data
        # -----------------------------------------
        # OrderBuilder collects scenario-specific fields. OrderFactory
        # assembles the line-item payload and enforces its supported fields.
        order_data = (
            OrderBuilder().with_fields(**kwargs).build()
        )  # Kwargs from the test flow directly
        # become Builder overrides

        # -----------------------------------------
        # 2️⃣ Provision Order
        # -----------------------------------------
        # OrderProvisioner delegates creation through OrdersHelper/OrdersApi
        # and returns the HttpResponse for fixture-level validation.
        response = order_provisioner.provision(order_data)

        # -----------------------------------------
        # 3️⃣ Transport validation (FAIL FAST)
        # -----------------------------------------
        # The setup operation must successfully create the Product.
        # response.text is deliberately included because it preserves the
        # server's actual error body when creation fails.
        assert response.status_code == 201, (
            "POST /orders creation failed. "
            f"Expected: 201, got {response.status_code}. "
            f"Response: {response.text}"
        )

        # -----------------------------------------
        # 4️⃣ Extract JSON to validate the response body
        # -----------------------------------------
        order = response.json

        # -----------------------------------------
        # 5️⃣ Structure + business validation
        # -----------------------------------------
        # Validate the Order returned by WooCommerce before exposing it to
        # the test.
        assert_valid_order_response(order)

        # -----------------------------------------
        # 6️⃣ Cleanup registration
        # -----------------------------------------
        # Only Orders explicitly created by this test are registered.
        if not skip_cleanup:
            register("orders", order["id"])
            log.debug("Registered Order ID %s for cleanup.", order["id"])
        else:
            log.debug("Skipped cleanup registration for Order ID %s.", order["id"])

        return order

    return _create_order


@pytest.fixture(scope="function")
def order_api_raw(api_client):
    """Provide direct access to APIClient for Order API calls.

    Use this fixture for negative cases or requests that intentionally bypass
    the valid-data fixture architecture.

    The fixture:
        - Skips ``OrderFactory`` and ``OrderBuilder``.
        - Skips ``OrderProvisioner`` and ``OrdersHelper``.
        - Performs no fixture-level response validation.
        - Returns the framework's ``HttpResponse`` abstraction.

    Intended use:
        - Negative tests with invalid or incomplete payloads.
        - Low-level API interaction and debugging.

    Args:
        api_client: Session-configured framework API client.

    Returns:
        APIClient: The configured client used for direct Order requests.
    """
    return api_client
