"""Product creation-data builder.

Builder for scenario-specific Product creation data (builds a new Product).

The builder sits between a test and the factory (depends on ProductFactory):

    Test
      |
      v
    Builder ---> Factory
      |
      v
    creation data
      |
      v
    Provisioner
      |
      v
    WooCommerce

The factory answers:
    "How do I generate a complete valid Product?"

The builder answers:
    "What should be different for this particular scenario?"

This keeps tests concise. A test can customize one or two fields without
rebuilding an entire Product payload.

Example:
    product = (
        ProductBuilder()
        .with_name("Known Product")
        .with_regular_price("49.99")
        .build()
    )

The builder does NOT:
    - call WooCommerce;
    - access the database;
    - use pytest fixtures;
    - register cleanup resources;
    - perform assertions;
    - validate API responses;
    - provision the Product into the system.

IMPORTANT
---------
The builder returns ``dict[str, Any]`` rather than ProductModel.

ProductModel describes a Product returned by the API, including
server-generated fields such as ``id`` and other response-only data.

ProductBuilder creates the data that exists BEFORE the API call.
The Product is only created in WooCommerce later by ProductProvisioner.
"""

from __future__ import annotations

from typing import Any

from EcommerceAPI.src.test_data.factories.products.product_factory import (
    ProductFactory,
)


class ProductBuilder:
    """
    Builder for scenario-specific Product creation data.

    The builder stores only scenario-specific overrides. ProductFactory
    remains responsible for generating all unspecified valid default values.

    This separation means a test can describe only what makes its scenario
    special while leaving the common Product data generation to the factory.

    Example:
        product = (
            ProductBuilder()
            .with_name("Known Product")
            .with_sku("KNOWN-SKU-001")
            .build()
        )

    The resulting mapping is complete Product creation data and can be passed
    to ProductProvisioner.

    The builder is intentionally unaware of:
        - WooCommerce;
        - HTTP requests;
        - pytest fixtures;
        - database state;
        - resource ownership;
        - cleanup;
        - API response validation.
    """

    def __init__(self, factory: ProductFactory | None = None) -> None:
        """
        Initialize the builder.

        Args:
            factory:
                Optional ProductFactory to use.

                Dependency injection is supported so callers can provide
                a configured or controlled factory when required.

                If omitted, a normal ProductFactory is created.
        """
        self._factory = factory or ProductFactory()

        # Store only scenario-specific overrides here.
        # ProductFactory remains responsible for generating all unspecified
        # default values.
        self._overrides: dict[str, Any] = {}

    def with_name(self, name: str) -> ProductBuilder:
        """
        Override the generated Product name.

        Useful for scenarios involving:
            - known Product names;
            - Product lookup;
            - duplicate-name scenarios;
            - name-specific validation;
            - readable test data.
        """
        self._overrides["name"] = name
        return self

    def with_sku(self, sku: str) -> ProductBuilder:
        """
        Override the generated Product SKU.

        Useful for scenarios involving:
            - known SKUs;
            - Product lookup by SKU;
            - duplicate-SKU behavior;
            - SKU-specific validation.
        """
        self._overrides["sku"] = sku
        return self

    def with_type(self, product_type: str) -> ProductBuilder:
        """
        Override the generated WooCommerce Product type.

        Useful for scenarios that need to create a specific Product type
        rather than relying on the factory default.
        """
        self._overrides["type"] = product_type
        return self

    def with_status(self, status: str) -> ProductBuilder:
        """
        Override the generated WooCommerce Product status.

        Useful for scenarios that explicitly require a particular Product
        lifecycle or publication status.
        """
        self._overrides["status"] = status
        return self

    def with_regular_price(self, price: str) -> ProductBuilder:
        """
        Override the generated Product regular price.

        Useful for scenarios involving:
            - specific Product prices;
            - price validation;
            - price boundary conditions;
            - update or comparison scenarios.
        """
        self._overrides["regular_price"] = price
        return self

    def with_sale_price(self, price: str) -> ProductBuilder:
        """
        Override the generated Product sale price.

        Useful for scenarios involving:
            - Products with a sale price;
            - regular-price/sale-price relationships;
            - sale-price validation;
            - pricing scenarios.
        """
        self._overrides["sale_price"] = price
        return self

    def with_description(self, description: str) -> ProductBuilder:
        """
        Override the generated full Product description.
        """
        self._overrides["description"] = description
        return self

    def with_short_description(self, description: str) -> ProductBuilder:
        """
        Override the generated Product short description.
        """
        self._overrides["short_description"] = description
        return self

    def with_fields(self, **fields: Any) -> ProductBuilder:
        """
        Override arbitrary Product creation fields.

        This is useful while the fixture API supports additional Product API
        fields that do not yet have a dedicated fluent builder method.

        Dedicated ``with_*`` methods remain preferable for commonly used
        scenario fields because they make tests self-documenting.

        Example:
            product = (
                ProductBuilder()
                .with_fields(
                    featured=True,
                    manage_stock=True,
                    stock_quantity=10,
                )
                .build()
            )

        Args:
            **fields:
                Product creation fields to override.

        Returns:
            ProductBuilder:
                The current builder instance, allowing method chaining.

        Notes:
            Validation of whether the resulting Product is accepted by
            WooCommerce remains outside the builder.
        """
        self._overrides.update(fields)
        return self

    def build(self) -> dict[str, Any]:
        """
        Produce the final Product creation payload.

        The builder does not generate all values itself. It passes the
        collected scenario overrides to ProductFactory, which generates
        sensible valid defaults for everything that was not overridden.

        Returns:
            dict[str, Any]:
                Complete Product creation data ready for the provisioning
                layer.

        Example:
            product = (
                ProductBuilder()
                .with_name("Test Product")
                .with_regular_price("29.99")
                .with_sku("TEST-PRODUCT-001")
                .build()
            )

        The returned mapping is still in-memory test data. No Product has
        been created in WooCommerce at this point.

        The next architectural step is ProductProvisioner, which is
        responsible for crossing the system boundary.
        """
        return self._factory.build(**self._overrides)
