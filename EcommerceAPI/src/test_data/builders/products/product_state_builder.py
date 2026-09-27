"""Product state builder.

Builds partial Product state for an already-existing WooCommerce Product.

The builder is intentionally separate from ``ProductBuilder``.

``ProductBuilder`` prepares complete creation data for a new Product.

``ProductStateBuilder`` prepares only the fields that an existing Product
should change.

The builder does NOT:
- create a complete Product payload;
- generate default values;
- call the WooCommerce API;
- access the database;
- use pytest fixtures;
- register cleanup resources;
- validate API responses;
- own any Product resources.

Architecture
------------
Creation:

    ProductBuilder
        ↓
    ProductFactory
        ↓
    ProductProvisioner
        ↓
    WooCommerce

State change:

    ProductStateBuilder
        ↓
    ProductStateProvisioner
        ↓
    ProductsHelper
        ↓
    ProductsApi
        ↓
    WooCommerce

IMPORTANT
---------
The state builder has no ProductFactory dependency.

This is intentional.

A state update should modify only the fields explicitly requested by the
scenario. It must not fill unspecified fields with creation defaults because
doing so could unintentionally overwrite existing Product state.
"""

from __future__ import annotations

from typing import Any


class ProductStateBuilder:
    """
    Build partial state for an existing Product (builds a change).

    Unlike ProductBuilder, this class does not create a complete Product
    payload. It returns only the fields that should be changed.

    The builder stores the requested state in memory and does not perform the
    update itself.

    Example:
        state = (
            ProductStateBuilder()
            .with_regular_price("29.99")
            .with_sale_price("24.99")
            .build()
        )

    The resulting mapping can then be passed to ProductStateProvisioner.

    The builder deliberately has no Factory dependency because state changes
    must not receive generated defaults.

    For example, if a scenario changes only ``regular_price``, the resulting
    state contains only ``regular_price``. Existing Product fields remain
    untouched by the prepared state.
    """

    _SUPPORTED_FIELDS = {
        "name",
        "type",
        "status",
        "description",
        "short_description",
        "sku",
        "regular_price",
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
    }

    def __init__(self) -> None:
        """
        Initialize an empty Product state.

        The builder starts with no requested changes. At least one supported
        field must be configured before ``build()`` can return the state.
        """
        self._state: dict[str, Any] = {}

    def with_regular_price(self, price: str) -> ProductStateBuilder:
        """
        Set the Product's regular price.

        This adds only the requested regular-price change to the partial
        state. It does not create or modify the Product itself.
        """
        self._state["regular_price"] = price
        return self

    def with_sale_price(self, price: str | None) -> ProductStateBuilder:
        """
        Set or clear the Product's sale price.

        ``None`` can be used when the scenario needs to explicitly clear the
        existing sale price.
        """
        self._state["sale_price"] = price
        return self

    def with_name(self, name: str) -> ProductStateBuilder:
        """
        Set the Product name.

        The value becomes part of the partial update state and is not
        generated or otherwise transformed by the builder.
        """
        self._state["name"] = name
        return self

    def with_sku(self, sku: str) -> ProductStateBuilder:
        """
        Set the Product SKU.

        The builder does not determine whether the SKU is unique or accepted
        by WooCommerce. Those concerns belong to the API/domain validation
        and the relevant test scenario.
        """
        self._state["sku"] = sku
        return self

    def with_status(self, status: str) -> ProductStateBuilder:
        """
        Set the Product status.

        The builder records the requested state only. Whether the supplied
        status is valid is determined by the Product/API domain.
        """
        self._state["status"] = status
        return self

    def with_fields(self, **fields: Any) -> ProductStateBuilder:
        """
        Add supported Product state fields.

        This method is useful when a scenario needs to change multiple
        Product fields that do not all have dedicated fluent methods.

        Raises:
            TypeError:
                If one or more supplied fields are not supported by the
                ProductStateBuilder.

        Notes:
            The builder validates field names, but does not validate whether
            the supplied values are accepted by WooCommerce.
        """
        unsupported = set(fields) - self._SUPPORTED_FIELDS

        if unsupported:
            raise TypeError(
                "Unsupported product state field(s): " + ", ".join(sorted(unsupported))
            )

        self._state.update(fields)
        return self

    def build(self) -> dict[str, Any]:
        """
        Return the prepared partial Product state.

        The returned mapping contains only the Product fields explicitly
        configured by the scenario.

        Unlike ProductFactory/ProductBuilder, this method does not add
        defaults for unspecified fields.

        Returns:
            dict[str, Any]:
                Partial Product state ready for ProductStateProvisioner.

        Raises:
            ValueError:
                If no Product state fields have been configured.

        Example:
            state = (
                ProductStateBuilder()
                .with_regular_price("39.99")
                .build()
            )

            # Result:
            # {"regular_price": "39.99"}

        This design prevents an update scenario from unintentionally
        overwriting existing Product state with generated creation defaults.
        """
        if not self._state:
            raise ValueError(
                "Product state cannot be empty. Configure at least one field."
            )

        return dict(self._state)
