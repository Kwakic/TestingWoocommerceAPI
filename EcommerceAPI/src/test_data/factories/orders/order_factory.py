"""Order test-data factory.

Generates the minimum/default valid Order creation data in memory.

An Order requires an existing Product to be referenced by its line items.
Therefore, the factory receives a Product ID rather than generating one.

The factory returns plain creation data, not an Order API model. The Order
will only exist in WooCommerce after the provisioning layer sends the
creation payload through the existing Orders API architecture.

Responsibilities
----------------
- Generate the minimum Order creation payload.
- Compose the supplied Product ID and quantity into the expected structure.
- Accept explicit overrides for supported Order creation fields.
- Reject unsupported fields so test-data mistakes fail early.
- Keep test-data generation independent of API calls and persistence.

Non-responsibilities
--------------------
- No WooCommerce/API calls.
- No database access.
- No pytest fixtures or assertions.
- No resource ownership or cleanup.
- No provisioning.
- No API-response validation.

Architecture
------------
    OrderBuilder
        ↓
    OrderFactory
        ↓
    OrderProvisioner
        ↓
    OrdersHelper
        ↓
    OrdersApi
        ↓
    WooCommerce

The factory prepares creation data in memory. It does not create or persist
an Order in WooCommerce.
"""

from __future__ import annotations

from typing import Any

from EcommerceAPI.src.test_data.factories.base import BaseFactory


class OrderFactory(BaseFactory[dict[str, Any]]):
    """
    Factory responsible for generating Order creation data.

    An Order must reference an existing Product through its ``line_items``.
    The caller supplies the Product ID because selecting or creating a Product
    is outside this factory's responsibility.

    By default, the factory returns a payload containing one line item with
    the supplied Product ID and a quantity of one.

    Example:
        order = OrderFactory().build(product_id=123)

    Result:

        {
            "line_items": [
                {
                    "product_id": 123,
                    "quantity": 1,
                }
            ]
        }

    A scenario can provide a different quantity or additional supported Order
    creation fields:

        order = OrderFactory().build(
            product_id=123,
            quantity=2,
            status="processing",
            payment_method="bacs",
            payment_method_title="Direct Bank Transfer",
            set_paid=True,
        )

    IMPORTANT ARCHITECTURAL RULE
    ----------------------------
    This factory generates *creation data*. It does not represent the Order
    object returned by WooCommerce.

    The Order API model belongs to the Order domain and describes API
    responses, which may contain server-generated fields such as ``id``.

    The factory therefore returns ``dict[str, Any]`` rather than an Order
    API model. Response validation belongs to the appropriate model and
    validation layer after the API call.

    RESPONSIBILITIES
    ----------------
    - Prepare the minimum Order creation payload.
    - Use an existing Product ID supplied by the caller.
    - Default the line-item quantity to one.
    - Accept explicit overrides for supported Order creation fields.
    - Reject unsupported fields at the test-data generation boundary.

    NON-RESPONSIBILITIES
    --------------------
    The factory must NOT:
        - generate or provision Products;
        - call the WooCommerce API;
        - access the database;
        - use pytest fixtures;
        - register resources for cleanup;
        - perform provisioning;
        - validate API responses;
        - contain test assertions.

    Keeping these responsibilities separate makes the factory reusable from
    API, GraphQL, and UI test-data workflows without coupling it to pytest
    or to a particular execution layer.
    """

    # These fields represent the Order creation data supported by this
    # factory's current contract.
    #
    # ``product_id`` and ``quantity`` are factory inputs used to construct
    # the line_items structure. They are not top-level WooCommerce Order
    # fields in the payload returned by build().
    #
    # The remaining fields are optional Order creation fields. They are
    # included only when explicitly supplied by the caller.
    SUPPORTED_FIELDS = {
        "product_id",
        "quantity",
        "customer_id",
        "status",
        "payment_method",
        "payment_method_title",
        "set_paid",
        "billing",
        "shipping",
        "line_items",
        "shipping_lines",
        "coupon_lines",
        "fee_lines",
        "meta_data",
    }

    def build(self, **overrides: Any) -> dict[str, Any]:
        """
        Build the minimum Order creation payload.

        The factory requires the ID of an existing Product and creates one
        line item with a default quantity of one.

        Additional supported Order creation fields can be supplied explicitly.
        They are not added automatically because customer details, payment
        configuration, addresses, shipping, and other Order state depend on
        the scenario being tested.

        Explicit keyword arguments replace the corresponding defaults.

        Example:
            order = OrderFactory().build(product_id=123)

        Or, when a scenario requires two units and a specific payment method:

            order = OrderFactory().build(
                product_id=123,
                quantity=2,
                payment_method="bacs",
                payment_method_title="Direct Bank Transfer",
                set_paid=True,
            )

        Supported creation fields:

            ``product_id``
            ``quantity``
            ``customer_id``
            ``status``
            ``payment_method``
            ``payment_method_title``
            ``set_paid``
            ``billing``
            ``shipping``
            ``line_items``
            ``shipping_lines``
            ``coupon_lines``
            ``fee_lines``
            ``meta_data``

        Args:
            **overrides:
                Order creation values. ``product_id`` is required unless
                ``line_items`` is explicitly supplied. ``quantity`` defaults
                to one when constructing the default line item. Other
                supported fields are included only when explicitly supplied.

        Returns:
            dict[str, Any]:
                Order creation data ready for the OrderBuilder/
                OrderProvisioner workflow.

        Raises:
            TypeError:
                If an unsupported field is supplied, or if neither
                ``product_id`` nor ``line_items`` is provided.

        Notes:
            The returned mapping represents data prepared before the API call.
            No Order has been created in WooCommerce at this point.
        """
        values = dict(overrides)

        # Fail early if a caller supplies a typo or a field that is not part
        # of this factory's explicit creation-data contract.
        unknown_fields = set(values) - self.SUPPORTED_FIELDS
        if unknown_fields:
            field_names = ", ".join(sorted(unknown_fields))
            raise TypeError(f"Unsupported OrderFactory fields: {field_names}")

        # Allow a caller to supply complete line-item data when a scenario
        # needs more than the default Product ID and quantity structure.
        #
        # Otherwise, construct the minimum line item from the required
        # existing Product ID and the requested quantity.
        line_items = values.pop("line_items", None)

        if line_items is None:
            if "product_id" not in values:
                raise TypeError(
                    "OrderFactory.build() requires 'product_id' unless "
                    "'line_items' is supplied."
                )

            product_id = values.pop("product_id")
            quantity = values.pop("quantity", 1)

            line_items = [
                {
                    "product_id": product_id,
                    "quantity": quantity,
                }
            ]
        else:
            # ``product_id`` and ``quantity`` are inputs for the default
            # line item. They must not be silently ignored when the caller
            # supplies a complete ``line_items`` structure.
            if "product_id" in values or "quantity" in values:
                raise TypeError(
                    "Supply either 'line_items' or 'product_id'/'quantity', "
                    "not both."
                )

        # Start with the line items required for the minimum Order payload.
        # Additional fields are included only when explicitly requested by
        # the scenario.
        order_data: dict[str, Any] = {
            "line_items": line_items,
        }

        order_data.update(values)

        return order_data


# The factory prepares Order creation data only. Scenario-specific Order
# details are composed by the Builder, and persistence is handled by the
# provisioning and domain/API layers.
