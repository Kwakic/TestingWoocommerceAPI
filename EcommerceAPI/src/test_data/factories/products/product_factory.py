"""Product test-data factory.

Factory responsible for generating valid Product creation data.

A factory belongs to the test-data generation layer. Its job is to create a
complete, valid set of Product data in memory so tests do not have to
manually assemble repetitive creation payloads.

IMPORTANT ARCHITECTURAL RULE
----------------------------
This factory generates *creation data*. It does not represent the Product
object returned by WooCommerce.

The canonical Product API model lives in the Product domain:

    EcommerceAPI/src/products/models/product_model.py

That model describes API responses and contains server-generated fields such
as ``id``. It should therefore not be used as this factory's return type.

Instead, this factory returns ``dict[str, Any]`` containing the fields needed
to create a Product. ProductProvisioner will later pass this data to the
existing ProductsHelper/API architecture.

RESPONSIBILITIES
----------------
- Generate realistic Product test values.
- Generate collision-resistant values where uniqueness is required.
- Provide sensible defaults for a complete valid Product.
- Compose generic utility values into the Product structure.
- Accept explicit overrides for scenario-specific data.
- Reject unsupported fields so test-data mistakes fail early.

NON-RESPONSIBILITIES
--------------------
The factory must NOT:
- call the WooCommerce API;
- access the database;
- use pytest fixtures;
- register resources for cleanup;
- perform provisioning;
- validate API responses;
- contain test assertions.

Keeping these responsibilities separate makes the factory reusable from API,
GraphQL, and UI test-data workflows without coupling it to pytest or to a
particular execution layer.

ARCHITECTURE
------------
    ProductBuilder
        ↓
    ProductFactory
        ↓
    ProductProvisioner
        ↓
    ProductsHelper
        ↓
    ProductsApi
        ↓
    WooCommerce

The Builder describes what a scenario wants to customize.

The Factory determines how to produce a complete valid Product creation
payload.

The Provisioner is responsible for crossing the system boundary.
"""

from __future__ import annotations

import random
from typing import Any
from uuid import uuid4

from EcommerceAPI.src.test_data.factories.base import BaseFactory
from EcommerceAPI.src.utils.generic_utilities import safe_product_name


class ProductFactory(BaseFactory[dict[str, Any]]):
    """
    Factory responsible for generating valid Product creation data.

    The factory provides complete default Product creation data while allowing
    tests to override only the fields relevant to their scenario.

    The factory intentionally returns creation data rather than a Product API
    model.

    A Product API model describes a Product returned by WooCommerce and may
    contain server-generated fields such as ``id``. The factory operates
    before the API call, so its output is a plain ``dict[str, Any]``.

    Example:
        product = factory.build()

    Or, when a known SKU and price are required:

        product = factory.build(
            sku="KNOWN-SKU-001",
            regular_price="49.99",
        )

    The factory does NOT:
        - call WooCommerce;
        - access the database;
        - use pytest fixtures;
        - register cleanup resources;
        - perform provisioning;
        - validate API responses;
        - perform assertions.

    All persistence and system interaction are handled by the provisioning
    and domain/API layers.
    """

    @staticmethod
    def generate_sale_price(
        regular_price: float,
        min_discount: float = 5.0,
        max_discount: float = 50.0,
    ) -> tuple[str, float]:
        """
        Generate a valid sale price that is less than the regular price.

        This utility belongs to ProductFactory because generating Product
        test-data values is a factory responsibility. It is useful for
        scenarios that need a realistic regular-price/sale-price relationship,
        particularly Product update/state scenarios.

        Args:
            regular_price (float): Base Product regular price.
            min_discount (float): Minimum discount percentage.
            max_discount (float): Maximum discount percentage.

        Returns:
            tuple[str, float]:
                Sale price as a string and the generated discount percentage.

        Raises:
            ValueError:
                If ``regular_price`` is not positive, ``min_discount`` is
                negative, ``max_discount`` is less than ``min_discount``, or
                ``max_discount`` is 100% or greater.

        Example:
            sale_price, discount = ProductFactory.generate_sale_price(100.00)

        Notes:
            The method generates only in-memory test data. It does not call
            WooCommerce, update a Product, or perform any provisioning.
        """
        # Validate the regular price before generating derived test data.
        if regular_price <= 0:
            raise ValueError("regular_price must be greater than zero.")

        # A negative discount would increase the sale price, which would not
        # represent a valid sale-price relationship.
        if min_discount < 0:
            raise ValueError("min_discount cannot be negative.")

        # Keep the configured discount range logically ordered.
        if max_discount < min_discount:
            raise ValueError(
                "max_discount must be greater than or equal to min_discount."
            )

        # A 100% discount would produce a zero sale price, while anything above
        # 100% would produce a negative value. Neither is a valid sale price.
        if max_discount >= 100:
            raise ValueError("max_discount must be less than 100.")

        # Generate a random discount within the requested range and derive the
        # sale price from the supplied regular price.
        discount_percentage = random.uniform(min_discount, max_discount)
        discount_amount = regular_price * (discount_percentage / 100.0)
        sale_price_value = regular_price - discount_amount

        return str(round(sale_price_value, 2)), discount_percentage

    def build(self, **overrides: Any) -> dict[str, Any]:
        """
        Build a complete Product creation payload.

        The factory provides sensible defaults for the fields required by the
        Product creation path. Explicit keyword arguments replace generated
        defaults, allowing a test to customize only the data relevant to its
        scenario.

        Generic random-data generation remains in the shared utility layer.
        ProductFactory composes those generic values into the structure
        required by the Product domain.

        Example:
            product = factory.build()

        Or, when a known Product name is required:

            product = factory.build(
                name="Known Product",
                sku="KNOWN-SKU-001",
            )

        Args:
            **overrides:
                Supported Product creation fields include:
                ``name``, ``type``, ``status``, ``regular_price``,
                ``sku``, ``description``, ``short_description``,
                ``sale_price``, ``featured``, ``catalog_visibility``,
                ``manage_stock``, ``stock_quantity``, ``stock_status``,
                ``weight``, ``dimensions``, ``categories``, ``tags``,
                ``images`` and ``meta_data``.

                Explicit values always take precedence over generated
                defaults.

        Returns:
            dict[str, Any]:
                Complete Product creation data ready for ProductBuilder/
                ProductProvisioner consumption.

        Raises:
            TypeError:
                If an unsupported Product field is supplied.

        Notes:
            The returned mapping represents data that exists before the API
            call. No Product has been created in WooCommerce at this point.
        """
        values = dict(overrides)

        # Product name is generated through the shared utility layer.
        # ProductFactory composes the generic generated value into the
        # Product-specific creation structure.
        name = values.pop("name", safe_product_name())

        # These are stable Product creation defaults.
        # A scenario can explicitly override any of them through the Builder
        # or directly through factory.build().
        product_type = values.pop("type", "simple")
        status = values.pop("status", "publish")
        regular_price = values.pop("regular_price", "19.99")

        # SKU must be collision-resistant because WooCommerce treats SKU as
        # a unique Product identifier in the normal creation flow.
        # uuid4() is used here only to provide uniqueness; generic random-data
        # primitives remain in the shared utility layer.
        sku = values.pop(
            "sku",
            f"TEST-SKU-{uuid4().hex[:12].upper()}",
        )

        # Description defaults are derived from the generated/overridden
        # Product name so the default payload remains internally coherent.
        description = values.pop(
            "description",
            f"Test product: {name}",
        )

        short_description = values.pop(
            "short_description",
            f"Test product: {name}",
        )

        payload: dict[str, Any] = {
            "name": name,
            "type": product_type,
            "status": status,
            "regular_price": regular_price,
            "sku": sku,
            "description": description,
            "short_description": short_description,
        }

        # Optional Product fields are included only when the scenario
        # explicitly provides them. The factory does not invent values for
        # fields that are not required by the default creation scenario.
        for field in (
            "sale_price",
            "featured",
            "catalog_visibility",
            "manage_stock",
            "stock_quantity",
            "stock_status",
            "weight",
            "dimensions",
            "categories",
            "tags",
            "images",
            "meta_data",
        ):
            if field in values:
                payload[field] = values.pop(field)

        # Fail fast on unsupported fields. This prevents a typo in test data
        # from silently becoming an unexpected Product payload.
        if values:
            unknown_fields = ", ".join(sorted(values))
            raise TypeError(f"Unsupported ProductFactory fields: {unknown_fields}")

        return payload
