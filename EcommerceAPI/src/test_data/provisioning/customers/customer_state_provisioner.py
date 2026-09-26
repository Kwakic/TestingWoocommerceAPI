"""
Customer state provisioner.

This module is responsible for taking already-prepared customer state data
and applying that state to an existing customer in the real WooCommerce
environment through the existing CustomersHelper.

Architecture
------------
Existing customer
    ↓
CustomerStateProvisioner
    ↓
CustomersHelper
    ↓
CustomersApi
    ↓
WooCommerce

The state provisioner deliberately does NOT:
- generate test data;
- customize scenario data;
- validate HTTP status codes;
- validate response schemas;
- register cleanup;
- use pytest fixtures;
- access the database directly.

The provisioner is intentionally separate from CustomerProvisioner.

CustomerProvisioner creates a new customer from creation data.
CustomerStateProvisioner changes the state of an already-existing customer.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from EcommerceAPI.src.core.http_response import HttpResponse
from EcommerceAPI.src.customers.helpers.customers_helper import CustomersHelper


class CustomerStateProvisioner:
    """
    Apply prepared state data to an existing WooCommerce customer.

    The state provisioner is the bridge between a test-data state definition
    and the real customer resource.

    It receives:
        - an existing customer ID;
        - already-prepared state data.

    It delegates the actual update operation to CustomersHelper and returns
    the framework ``HttpResponse`` so the caller (normally a pytest fixture)
    can apply the appropriate setup contract.

    Example:

        state = {
            "billing": {...},
            "shipping": {...},
        }

        provisioner = CustomerStateProvisioner(customer_helper)
        response = provisioner.provision(customer_id, state)

    The caller remains responsible for:
        HttpResponse
            ↓
        expected status validation
            ↓
        response-body/domain validation
    """

    def __init__(self, customer_helper: CustomersHelper) -> None:
        """
        Initialize the customer state provisioner.

        Args:
            customer_helper:
                Existing domain helper responsible for customer API
                orchestration.
        """
        self.customer_helper = customer_helper

    def provision(
        self,
        customer_id: int,
        state: Mapping[str, Any],
    ) -> HttpResponse:
        """
        Apply prepared state data to an existing customer.

        Args:
            customer_id:
                WooCommerce customer ID of the resource being modified.

            state:
                Prepared customer state data. The mapping is passed to the
                existing CustomersHelper without generating or modifying
                its contents.

        Returns:
            HttpResponse:
                Response from the customer update request.

        Raises:
            TypeError:
                If ``customer_id`` is not an integer or ``state`` is not a
                mapping.

            ValueError:
                If ``customer_id`` is not positive or ``state`` is empty.

        Notes:
            The provisioner intentionally does not validate the HTTP status.
            A setup caller may expect 200 for a successful WooCommerce update,
            but that transport assertion belongs to the caller/fixture.
        """
        if not isinstance(customer_id, int) or isinstance(customer_id, bool):
            raise TypeError("customer_id must be an integer.")

        if customer_id <= 0:
            raise ValueError("customer_id must be greater than zero.")

        if not isinstance(state, Mapping):
            raise TypeError(
                "state must be a mapping containing the prepared customer "
                "state to apply."
            )

        if not state:
            raise ValueError(
                "state cannot be empty. Prepare the customer state before "
                "calling CustomerStateProvisioner."
            )

        return self.customer_helper.update_customer(
            customer_id=customer_id,
            payload=dict(state),
            return_http_response=True,
        )
