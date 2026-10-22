"""Order test-data builder.

Prepares scenario-specific Order creation data in memory. The builder offers
readable fluent methods while OrderFactory remains responsible for defaults
and its supported-field contract.

The builder does not call APIs, access the database, use pytest, register
cleanup, perform assertions, validate responses, or provision Orders.
It returns request data (``dict[str, Any]``), not an API response model.
"""

from __future__ import annotations

from typing import Any

from EcommerceAPI.src.test_data.factories.orders.order_factory import OrderFactory


class OrderBuilder:
    """
    Build Order creation payloads for individual test scenarios.

    The caller supplies an existing Product ID for the default line item.
    The factory assembles that item and defaults its quantity to one.

    The builder answers:
    "What should be different for this particular scenario?"

    Example:
        order_data = (
            OrderBuilder()
            .with_product(product_id=123, quantity=2)
            .with_status("processing")
            .with_payment(
                payment_method="bacs",
                payment_method_title="Direct Bank Transfer",
                set_paid=True,
            )
            .build()
        )

    ``build()`` only returns in-memory data. A later provisioning layer
    will send it to WooCommerce.
    """

    def __init__(self, factory: OrderFactory | None = None) -> None:
        """Initialize with an optional injected factory.

        Args:
            factory: Custom OrderFactory, or a default instance if omitted.
        """
        self._factory = factory or OrderFactory()

        # Store only scenario overrides. The factory owns payload assembly
        # and rejects fields outside its supported creation-data contract.
        self._overrides: dict[str, Any] = {}

    def with_product(self, product_id: int, quantity: int = 1) -> OrderBuilder:
        """Set the existing Product ID and quantity for the default line item.

        The builder does not create or look up the Product. Use
        ``with_line_items()`` instead for a complete custom list; do not
        combine that method with ``with_product()``.
        """
        self._overrides["product_id"] = product_id
        self._overrides["quantity"] = quantity
        return self

    def with_customer(self, customer_id: int) -> OrderBuilder:
        """Associate this Order with an existing Customer.

        For a guest Order, omit this method. The builder does not verify
        that the supplied Customer exists.
        """
        self._overrides["customer_id"] = customer_id
        return self

    def with_status(self, status: str) -> OrderBuilder:
        """Set the requested Order status, for example ``processing``."""
        self._overrides["status"] = status
        return self

    def with_payment(
        self,
        *,
        payment_method: str | None = None,
        payment_method_title: str | None = None,
        set_paid: bool | None = None,
    ) -> OrderBuilder:
        """Set one or more payment fields.

        Only ``None`` values are omitted; explicit values such as
        ``set_paid=False`` are preserved.
        """
        payment_fields = {
            "payment_method": payment_method,
            "payment_method_title": payment_method_title,
            "set_paid": set_paid,
        }
        self._overrides.update(
            {key: value for key, value in payment_fields.items() if value is not None}
        )
        return self

    def with_billing(self, billing: dict[str, Any]) -> OrderBuilder:
        """Set the billing address; address validity is not checked here."""
        self._overrides["billing"] = billing
        return self

    def with_shipping(self, shipping: dict[str, Any]) -> OrderBuilder:
        """Set the shipping address; address validity is not checked here."""
        self._overrides["shipping"] = shipping
        return self

    def with_line_items(self, line_items: list[dict[str, Any]]) -> OrderBuilder:
        """Supply complete custom line items, e.g. for multiple Products.

        Do not combine with ``with_product()``. OrderFactory rejects supplying
        both custom ``line_items`` and the ``product_id``/``quantity`` inputs.
        """
        self._overrides["line_items"] = line_items
        return self

    def with_shipping_lines(self, shipping_lines: list[dict[str, Any]]) -> OrderBuilder:
        """Set shipping methods/charges in the Order creation payload."""
        self._overrides["shipping_lines"] = shipping_lines
        return self

    def with_coupon_lines(self, coupon_lines: list[dict[str, Any]]) -> OrderBuilder:
        """Set coupon lines applied to the Order."""
        self._overrides["coupon_lines"] = coupon_lines
        return self

    def with_fee_lines(self, fee_lines: list[dict[str, Any]]) -> OrderBuilder:
        """Set fee lines included in the Order creation payload."""
        self._overrides["fee_lines"] = fee_lines
        return self

    def with_meta_data(self, meta_data: list[dict[str, Any]]) -> OrderBuilder:
        """Set custom metadata entries for the Order."""
        self._overrides["meta_data"] = meta_data
        return self

    def with_fields(self, **fields: Any) -> OrderBuilder:
        """Set arbitrary fields supported by OrderFactory.

        Prefer dedicated ``with_*`` methods for commonly used fields because
        they make test intent easier to read. The builder does not duplicate
        factory validation; unsupported fields are rejected during build().
        """
        self._overrides.update(fields)
        return self

    def build(self) -> dict[str, Any]:
        """Return the final request payload without creating an Order.

        Raises:
            TypeError: If required line-item inputs are missing, incompatible
                line-item inputs are supplied, or an unsupported field exists.
        """
        return self._factory.build(**self._overrides)
