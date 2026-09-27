"""Product test-data provisioner.

This module is responsible for taking already-prepared Product creation data
and provisioning it into the real WooCommerce environment through the
existing ProductsHelper.

Architecture
------------
ProductFactory
    ↓
ProductBuilder
    ↓
ProductProvisioner
    ↓
ProductsHelper
    ↓
ProductsApi
    ↓
WooCommerce

The provisioner is the bridge between the in-memory test-data layer and the
real system under test.

The provisioner deliberately does NOT:
- generate test data;
- customize scenario data;
- validate HTTP status codes;
- validate response schemas;
- register cleanup;
- use pytest fixtures;
- access the database directly.

Those responsibilities belong to the appropriate layers above or below the
provisioner.

The provisioner receives already-prepared Product data and delegates the
actual creation operation to ProductsHelper.

It intentionally returns the framework's ``HttpResponse`` so the caller,
normally the pytest fixture, can apply the existing setup contract:

    HttpResponse
        ↓
    expected status validation
        ↓
    response-body/domain validation
        ↓
    ownership registration
        ↓
    clean Product dict returned to the test

Keeping those concerns separate preserves the framework rule that the
fixture is the gatekeeper for valid setup data.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from EcommerceAPI.src.core.http_response import HttpResponse
from EcommerceAPI.src.products.helpers.products_helper import ProductsHelper


class ProductProvisioner:
    """
    Provision prepared Product data into WooCommerce.

    The provisioner is the bridge between the in-memory Product test-data
    layer and the real system under test.

    It receives data produced by ProductFactory/ProductBuilder and delegates
    the actual creation operation to ProductsHelper.

    IMPORTANT
    ---------
    The provisioner does not decide what Product data should be created.

    ProductFactory/ProductBuilder are responsible for preparing the creation
    payload. ProductProvisioner is responsible only for taking that prepared
    payload across the system boundary.

    The provisioner intentionally returns ``HttpResponse`` rather than a
    parsed Product dictionary. This allows the caller, normally the pytest
    fixture, to apply the setup contract:

        HttpResponse
            ↓
        expected status validation
            ↓
        response-body/domain validation
            ↓
        ownership registration
            ↓
        validated Product dict returned to the test

    This keeps test lifecycle responsibilities in the fixture rather than
    moving assertions, validation, or cleanup into the provisioning layer.
    """

    def __init__(self, product_helper: ProductsHelper) -> None:
        """
        Initialize the ProductProvisioner.

        Args:
            product_helper:
                Existing ProductsHelper responsible for Product API
                orchestration.

        Notes:
            Dependency injection keeps the provisioner independent of how
            ProductsHelper is constructed and makes the provisioning layer
            easy to use from pytest fixtures or other test-data workflows.
        """
        self.product_helper = product_helper

    def provision(self, product_data: Mapping[str, Any]) -> HttpResponse:
        """
        Create a Product from already-prepared test data.

        Args:
            product_data:
                Creation payload produced by ``ProductFactory`` or
                ``ProductBuilder``.

        Returns:
            HttpResponse:
                The response returned by the Product creation request.

                The response is intentionally returned unchanged so the
                caller can inspect transport details and apply its own
                validation contract.

        Raises:
            TypeError:
                If ``product_data`` is not a mapping.

            ValueError:
                If no Product data was supplied.

        Notes:
            The provisioner does not generate missing Product data.

            This is intentional. Test-data generation belongs to the
            ProductFactory/ProductBuilder layer, so the provisioner must
            pass the prepared payload to ProductsHelper rather than allowing
            another layer to silently generate a second payload.

        Flow:
            ProductFactory/ProductBuilder
                ↓
            prepared Product data
                ↓
            ProductProvisioner
                ↓
            ProductsHelper
                ↓
            ProductsApi
                ↓
            WooCommerce
                ↓
            HttpResponse
        """
        # -----------------------------------------
        # 1️⃣ Validate the provisioning input
        # -----------------------------------------
        # The provisioner accepts prepared test data only. Rejecting invalid
        # input here prevents malformed provisioning calls from reaching the
        # domain/API layer.
        if not isinstance(product_data, Mapping):
            raise TypeError(
                "product_data must be a mapping containing the Product "
                "creation payload."
            )

        if not product_data:
            raise ValueError(
                "product_data cannot be empty. "
                "Build the product data with ProductFactory/ProductBuilder first."
            )

        # -----------------------------------------
        # 2️⃣ Provision Product through domain layer
        # -----------------------------------------
        # ProductsHelper owns Product API orchestration. The provisioner passes
        # the already-prepared payload unchanged and explicitly requests the
        # HttpResponse because the fixture needs it for setup validation.
        return self.product_helper.create_product(
            payload=dict(product_data),
            return_http_response=True,
        )
