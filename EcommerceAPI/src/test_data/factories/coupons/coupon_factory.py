"""Coupon test-data factory.

Generates complete, valid Coupon creation data in memory.

Responsibilities
----------------
- Generate valid default Coupon creation values.
- Generate a collision-resistant coupon code through the shared utility layer.
- Apply explicit scenario-specific overrides.
- Return plain creation data for the Coupon provisioning layer.

Non-responsibilities
--------------------
- No WooCommerce/API calls.
- No database access.
- No pytest fixtures or assertions.
- No resource ownership or cleanup.
- No API-response validation.

Architecture
------------
    CouponBuilder
        ↓
    CouponFactory
        ↓
    CouponProvisioner
        ↓
    CouponsHelper
        ↓
    CouponsApi
        ↓
    WooCommerce

The factory decides what valid default Coupon creation data looks like;
it does not persist the Coupon.

The factory intentionally returns ``dict[str, Any]`` rather than a Coupon
API model because the factory operates before the API call. Server-generated
fields such as ``id`` do not exist yet.
"""

from __future__ import annotations

from typing import Any

from EcommerceAPI.src.test_data.factories.base import BaseFactory
from EcommerceAPI.src.utils.generic_utilities import generate_random_coupon_code


class CouponFactory(BaseFactory[dict[str, Any]]):
    """
    Factory responsible for generating valid Coupon creation data.

    A factory belongs to the test-data generation layer. Its job is to create
    a complete, valid set of data in memory so tests do not have to manually
    assemble repetitive Coupon payloads.

    IMPORTANT ARCHITECTURAL RULE
    ----------------------------
    This factory generates *creation data*. It does not represent the Coupon
    object returned by WooCommerce.

    The factory therefore returns ``dict[str, Any]`` containing the fields
    needed to create a Coupon. The provisioner will later pass this data to
    the existing Coupon domain helper.

    RESPONSIBILITIES
    ----------------
    - Generate realistic valid test values.
    - Generate collision-resistant coupon codes.
    - Provide sensible defaults for a complete minimal Coupon.
    - Accept explicit overrides for supported Coupon creation fields.
    - Reject unsupported fields at the test-data generation boundary.

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

    Keeping these responsibilities separate makes the factory reusable from
    API, GraphQL, and UI-data workflows without coupling it to pytest or to a
    particular execution layer.
    """

    # These are the fields supported by CouponsHelper.create_coupon() and
    # therefore form the explicit Coupon creation-data contract.
    #
    # The factory does not populate every optional field by default. The
    # minimal Coupon payload is sufficient for a valid creation. Scenario-
    # specific optional fields are supplied through explicit overrides or,
    # later, through dedicated CouponBuilder methods.
    SUPPORTED_FIELDS = {
        "code",
        "amount",
        "discount_type",
        "individual_use",
        "product_ids",
        "excluded_product_ids",
        "usage_limit",
        "usage_limit_per_user",
        "limit_usage_to_x_items",
        "free_shipping",
        "product_categories",
        "excluded_product_categories",
        "exclude_sale_items",
        "minimum_amount",
        "maximum_amount",
        "email_restrictions",
        "description",
        "date_expires",
    }

    def build(self, **overrides: Any) -> dict[str, Any]:
        """
        Build a complete Coupon creation payload.

        The factory generates the generic valid defaults required for a
        minimal Coupon. Explicit keyword arguments replace those defaults,
        allowing a test to customize only the data relevant to its scenario.

        Optional Coupon creation fields are supported as explicit overrides.
        They are not generated automatically because the existing test suite
        treats them as scenario-specific data rather than requirements for
        every Coupon.

        Example:
            coupon = factory.build()

        Or, when a scenario requires restrictions:

            coupon = factory.build(
                discount_type="percent",
                amount="15",
                individual_use=True,
                free_shipping=True,
                minimum_amount="20",
                maximum_amount="100",
            )

        Supported creation fields:

            ``code``
            ``amount``
            ``discount_type``
            ``individual_use``
            ``product_ids``
            ``excluded_product_ids``
            ``usage_limit``
            ``usage_limit_per_user``
            ``limit_usage_to_x_items``
            ``free_shipping``
            ``product_categories``
            ``excluded_product_categories``
            ``exclude_sale_items``
            ``minimum_amount``
            ``maximum_amount``
            ``email_restrictions``
            ``description``
            ``date_expires``

        Args:
            **overrides:
                Explicit Coupon creation values. Supported fields are limited
                to the fields in ``SUPPORTED_FIELDS``.

        Returns:
            dict[str, Any]:
                Coupon creation data ready for the provisioning layer.

        Raises:
            TypeError:
                If an unsupported field is supplied.
        """
        values = dict(overrides)

        # Validate the creation-data contract before consuming any values.
        # Failing here is preferable to silently passing a typo or unsupported
        # field into the API.
        unknown_fields = set(values) - self.SUPPORTED_FIELDS
        if unknown_fields:
            field_names = ", ".join(sorted(unknown_fields))
            raise TypeError(f"Unsupported CouponFactory fields: {field_names}")

        # Coupon codes must normally be unique for independent test data.
        # Generation remains in the shared utility layer; this factory composes
        # that reusable primitive into the Coupon-specific payload.
        code = values.pop(
            "code",
            generate_random_coupon_code(
                length=10,
                prefix="test-",
            ),
        )

        # These are the three fields required by the Coupon creation flow used
        # by the current tests. The remaining creation fields are optional and
        # are added only when a scenario explicitly requests them.
        discount_type = values.pop("discount_type", "percent")
        amount = values.pop("amount", "10.00")

        # Start with the minimal valid Coupon creation payload, then add only
        # explicitly requested optional fields. This keeps ordinary tests
        # concise while allowing the same factory to support richer scenarios.
        coupon_data: dict[str, Any] = {
            "code": code,
            "discount_type": discount_type,
            "amount": amount,
        }

        coupon_data.update(values)

        return coupon_data
