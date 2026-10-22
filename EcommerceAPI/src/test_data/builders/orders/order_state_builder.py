"""
Order state builder.

This module prepares partial state changes for an already-existing
WooCommerce Order. It is intentionally separate from ``OrderBuilder``:

    OrderBuilder
        -> prepares creation data for a new Order
        -> uses OrderFactory

    OrderStateBuilder
        -> prepares only the fields to change on an existing Order
        -> has no Factory dependency

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

The builder returns ``dict[str, Any]`` containing only explicitly requested
changes. It does not add creation defaults, so fields omitted from the state
remain outside this update request.

The state builder does NOT:
- create an Order or a complete Order payload;
- generate default values for unspecified Order fields;
- call WooCommerce or access the database;
- use pytest fixtures or register cleanup resources;
- validate API responses or perform assertions;
- provision or otherwise own an Order resource.
"""

from __future__ import annotations

from typing import Any


class OrderStateBuilder:
    """Build partial state for an existing WooCommerce Order.

    Unlike ``OrderBuilder``, this class does not build creation data or depend
    on ``OrderFactory``. It stores only the fields that a scenario explicitly
    wants to change; unspecified Order fields are not added to the payload.

    Example:

        state = (
            OrderStateBuilder()
            .with_status("completed")
            .with_customer_note("Ready for pickup")
            .build()
        )

        # Result:
        # {"status": "completed", "customer_note": "Ready for pickup"}

    The resulting mapping can be passed to ``OrderStateProvisioner``. This
    builder prepares data in memory; it does not update the Order itself.
    """

    _SUPPORTED_FIELDS = {
        "customer_id",
        "status",
        "customer_note",
        "payment_method",
        "payment_method_title",
        "set_paid",
        "transaction_id",
        "billing",
        "shipping",
        "line_items",
        "shipping_lines",
        "coupon_lines",
        "fee_lines",
        "meta_data",
    }

    def __init__(self) -> None:
        """Initialize an empty Order state.

        At least one supported field must be configured before ``build()``
        can return the partial state mapping.
        """
        self._state: dict[str, Any] = {}

    def with_customer(self, customer_id: int) -> OrderStateBuilder:
        """Set the customer ID included in the Order update state.

        The builder records the supplied value and does not check whether the
        referenced customer exists.
        """
        self._state["customer_id"] = customer_id
        return self

    def with_status(self, status: str) -> OrderStateBuilder:
        """Set the requested Order status, for example ``processing``.

        The builder stores the value without validating WooCommerce business
        rules. Validation belongs to the API/domain layer and the test scenario.
        """
        self._state["status"] = status
        return self

    def with_customer_note(self, customer_note: str) -> OrderStateBuilder:
        """Set the customer-facing note included in the Order update."""
        self._state["customer_note"] = customer_note
        return self

    def with_payment(
        self,
        *,
        payment_method: str | None = None,
        payment_method_title: str | None = None,
        set_paid: bool | None = None,
        transaction_id: str | None = None,
    ) -> OrderStateBuilder:
        """Configure one or more payment fields in the partial Order state.

        Only values other than ``None`` are added. This allows callers to
        omit payment fields they do not want to change while preserving
        explicit values such as ``set_paid=False``.
        """
        fields = {
            "payment_method": payment_method,
            "payment_method_title": payment_method_title,
            "set_paid": set_paid,
            "transaction_id": transaction_id,
        }
        self._state.update(
            {key: value for key, value in fields.items() if value is not None}
        )
        return self

    def with_billing(self, billing: dict[str, Any]) -> OrderStateBuilder:
        """Set the billing address included in the Order update state.

        A shallow copy is stored so replacing keys in the caller's mapping
        after this call does not replace keys in the builder's state.
        """
        self._state["billing"] = dict(billing)
        return self

    def with_shipping(self, shipping: dict[str, Any]) -> OrderStateBuilder:
        """Set the shipping address included in the Order update state.

        A shallow copy of the supplied mapping is stored by the builder.
        """
        self._state["shipping"] = dict(shipping)
        return self

    def with_line_items(self, line_items: list[dict[str, Any]]) -> OrderStateBuilder:
        """Set the line items included in the Order update state.

        Each item mapping is shallow-copied. The builder does not look up
        products or validate the line-item values.
        """
        self._state["line_items"] = [dict(item) for item in line_items]
        return self

    def with_shipping_lines(
        self, shipping_lines: list[dict[str, Any]]
    ) -> OrderStateBuilder:
        """Set the shipping lines included in the Order update state.

        Each line mapping is shallow-copied; shipping configuration and
        amount validation remain outside the builder.
        """
        self._state["shipping_lines"] = [dict(item) for item in shipping_lines]
        return self

    def with_coupon_lines(
        self, coupon_lines: list[dict[str, Any]]
    ) -> OrderStateBuilder:
        """Set the coupon lines included in the Order update state.

        Each line mapping is shallow-copied. The builder does not check
        whether a coupon exists or is valid for the Order.
        """
        self._state["coupon_lines"] = [dict(item) for item in coupon_lines]
        return self

    def with_fee_lines(self, fee_lines: list[dict[str, Any]]) -> OrderStateBuilder:
        """Set the fee lines included in the Order update state.

        Each line mapping is shallow-copied; WooCommerce remains responsible
        for validating the fee data.
        """
        self._state["fee_lines"] = [dict(item) for item in fee_lines]
        return self

    def with_meta_data(self, meta_data: list[dict[str, Any]]) -> OrderStateBuilder:
        """Set the metadata entries included in the Order update state.

        Each metadata mapping is shallow-copied. Metadata keys and values
        are not validated by the builder.
        """
        self._state["meta_data"] = [dict(item) for item in meta_data]
        return self

    def with_fields(self, **fields: Any) -> OrderStateBuilder:
        """Add supported Order state fields by name.

        Prefer the dedicated ``with_*`` methods for common fields because
        they make scenario intent easier to read. This method checks field
        names only; it does not validate field values or WooCommerce rules.

        Raises:
            TypeError: If any supplied field is not supported by this builder.
        """
        unsupported = set(fields) - self._SUPPORTED_FIELDS
        if unsupported:
            raise TypeError(
                "Unsupported order state field(s): " + ", ".join(sorted(unsupported))
            )

        self._state.update(fields)
        return self

    def build(self) -> dict[str, Any]:
        """Return the prepared partial Order state.

        The result contains only fields explicitly configured by the
        scenario. Unlike ``OrderBuilder`` and ``OrderFactory``, this method
        does not add defaults for fields that were not requested.

        Returns:
            dict[str, Any]: Partial state ready for ``OrderStateProvisioner``.

        Raises:
            ValueError: If no Order state fields have been configured.

        Example:

            state = OrderStateBuilder().with_status("processing").build()

            # Result:
            # {"status": "processing"}
        """
        if not self._state:
            raise ValueError(
                "Order state cannot be empty. Configure at least one field."
            )

        return dict(self._state)
