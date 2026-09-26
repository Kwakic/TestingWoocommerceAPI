"""
Customer test-data provisioner.

This module is responsible for taking already-prepared customer creation data
and provisioning it into the real WooCommerce environment through the existing
CustomersHelper.

Architecture
------------
CustomerFactory
    ↓
CustomerBuilder
    ↓
CustomerProvisioner
    ↓
CustomersHelper
    ↓
CustomersApi
    ↓
WooCommerce

The provisioner deliberately does NOT:
- generate test data;
- customize scenario data;
- validate HTTP status codes;
- validate response schemas;
- register cleanup;
- use pytest fixtures;
- access the database directly.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from EcommerceAPI.src.core.http_response import HttpResponse
from EcommerceAPI.src.customers.helpers.customers_helper import CustomersHelper


class CustomerProvisioner:
    """
    Provision prepared customer data into WooCommerce.

    The provisioner is the bridge between the in-memory test-data layer and
    the real system under test.

    It receives data produced by a CustomerFactory/CustomerBuilder and delegates
    the actual creation operation to CustomersHelper. It intentionally returns
    the framework's ``HttpResponse`` so the caller (normally the pytest
    fixture) can apply the existing setup contract:

        HttpResponse
            ↓
        expected status validation
            ↓
        response-body/domain validation
            ↓
        ownership registration
            ↓
        clean dict returned to the test

    Keeping those concerns separate preserves the existing framework rule that
    the fixture is the gatekeeper for valid setup data.
    """

    def __init__(self, customer_helper: CustomersHelper) -> None:
        """
        Args:
            customer_helper: Existing domain helper responsible for customer
                API orchestration.
        """
        self.customer_helper = customer_helper

    def provision(self, customer_data: Mapping[str, Any]) -> HttpResponse:
        """
        Create a customer from already-prepared test data.

        Args:
            customer_data:
                Creation payload produced by ``CustomerFactory`` or
                ``CustomerBuilder``.

        Returns:
            HttpResponse:
                The response from the customer creation request.

        Raises:
            TypeError:
                If ``customer_data`` is not a mapping.
            ValueError:
                If no customer data was supplied.

        Notes:
            ``auto_generate=False`` is intentional. Test-data generation
            belongs to the Factory layer, so the provisioner must not allow
            the Helper to silently generate a second set of credentials.
        """
        if not isinstance(customer_data, Mapping):
            raise TypeError(
                "customer_data must be a mapping containing the customer "
                "creation payload."
            )

        if not customer_data:
            raise ValueError(
                "customer_data cannot be empty. "
                "Build the customer data with CustomerFactory/CustomerBuilder first."
            )

        return self.customer_helper.create_customer(
            auto_generate=False,
            return_http_response=True,
            **dict(customer_data),
        )
