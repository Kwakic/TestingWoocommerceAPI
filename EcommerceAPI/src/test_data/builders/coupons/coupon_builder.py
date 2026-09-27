"""Coupon test-data builder.

The builder prepares scenario-specific Coupon creation data.

The builder sits between a test and CouponFactory:

    Test
      |
      v
    CouponBuilder ---> CouponFactory
      |
      v
    creation data
      |
      v
    CouponProvisioner
      |
      v
    WooCommerce

The factory answers:
    "How do I generate a complete valid coupon?"

The builder answers:
    "What should be different for this particular scenario?"

This keeps tests concise. A test can customize only the fields relevant to
its scenario without rebuilding the complete Coupon creation payload.

The builder prepares creation data only. It does not create a Coupon in
WooCommerce.

The builder does NOT:
    - call WooCommerce;
    - access the database;
    - use pytest fixtures;
    - register cleanup resources;
    - perform assertions;
    - validate API responses;
    - perform provisioning.

The builder returns ``dict[str, Any]`` because it prepares data that exists
before the API call. The Coupon API model represents data returned by
WooCommerce and may contain server-generated fields such as ``id``.
"""

from __future__ import annotations

from typing import Any

from EcommerceAPI.src.test_data.factories.coupons.coupon_factory import (
    CouponFactory,
)


class CouponBuilder:
    """
    Builder for scenario-specific Coupon creation data.

    The builder sits between a test and CouponFactory. It stores only the
    values that are intentionally different for the current test scenario
    and delegates all unspecified defaults to CouponFactory.

    The builder does NOT:
        - call WooCommerce;
        - access the database;
        - use pytest fixtures;
        - register cleanup resources;
        - perform assertions;
        - validate API responses;
        - perform provisioning.

    IMPORTANT
    ---------
    The builder returns ``dict[str, Any]`` rather than CouponModel.
    CouponModel describes a Coupon returned by the API, including
    server-generated fields such as ``id``. This builder creates data that
    exists before the API call.

    Example:
        coupon = (
            CouponBuilder()
            .with_discount_type("percent")
            .with_amount("10.00")
            .build()
        )
    """

    def __init__(self, factory: CouponFactory | None = None) -> None:
        """
        Initialize the CouponBuilder.

        Args:
            factory:
                Optional CouponFactory to use. Dependency injection is
                supported so callers can provide a configured factory.
                If omitted, a normal CouponFactory is created.
        """
        self._factory = factory or CouponFactory()

        # Store only scenario-specific overrides here. CouponFactory remains
        # responsible for generating all unspecified valid default values.
        self._overrides: dict[str, Any] = {}

    def with_code(self, code: str) -> CouponBuilder:
        """
        Override the generated Coupon code.

        Useful for scenarios involving known coupon codes, lookup operations,
        duplicate-code behavior, or code-specific validation.
        """
        self._overrides["code"] = code
        return self

    def with_discount_type(self, discount_type: str) -> CouponBuilder:
        """
        Override the generated Coupon discount type.

        Supported values exercised by the current test suite include:

            - ``percent``
            - ``fixed_cart``
            - ``fixed_product``

        The builder stores the requested value without validating business
        rules. Validation of whether a value is accepted belongs to the API
        and the relevant test.
        """
        self._overrides["discount_type"] = discount_type
        return self

    def with_amount(self, amount: str) -> CouponBuilder:
        """
        Override the generated Coupon discount amount.

        Useful when a scenario requires a known amount, such as testing
        integer, decimal, minimum, or larger discount values.
        """
        self._overrides["amount"] = amount
        return self

    def with_restrictions(
        self,
        *,
        individual_use: bool | None = None,
        free_shipping: bool | None = None,
        exclude_sale_items: bool | None = None,
        minimum_amount: str | None = None,
        maximum_amount: str | None = None,
    ) -> CouponBuilder:
        """
        Configure common Coupon restriction fields.

        This groups the restriction fields used by the current Coupon tests
        into one scenario-oriented builder method.

        Only values that are explicitly provided are added to the overrides.
        ``None`` means that the corresponding field should remain unspecified,
        allowing CouponFactory to leave it out of the creation payload.

        Args:
            individual_use:
                Whether the Coupon can be used individually.
            free_shipping:
                Whether the Coupon grants free shipping.
            exclude_sale_items:
                Whether sale items are excluded.
            minimum_amount:
                Minimum required order amount.
            maximum_amount:
                Maximum allowed order amount.

        Returns:
            CouponBuilder:
                The current builder instance for fluent chaining.
        """
        restrictions = {
            "individual_use": individual_use,
            "free_shipping": free_shipping,
            "exclude_sale_items": exclude_sale_items,
            "minimum_amount": minimum_amount,
            "maximum_amount": maximum_amount,
        }

        self._overrides.update(
            {key: value for key, value in restrictions.items() if value is not None}
        )
        return self

    def with_usage_limits(
        self,
        *,
        usage_limit: int | None = None,
        usage_limit_per_user: int | None = None,
        limit_usage_to_x_items: int | None = None,
    ) -> CouponBuilder:
        """
        Configure Coupon usage-limit fields.

        These fields are treated as one scenario concept because the current
        test suite exercises them together when verifying Coupon usage limits.

        Only explicitly provided values are added to the creation payload.
        """
        usage_limits = {
            "usage_limit": usage_limit,
            "usage_limit_per_user": usage_limit_per_user,
            "limit_usage_to_x_items": limit_usage_to_x_items,
        }

        self._overrides.update(
            {key: value for key, value in usage_limits.items() if value is not None}
        )
        return self

    def with_email_restrictions(
        self,
        email_restrictions: list[str],
    ) -> CouponBuilder:
        """
        Restrict Coupon usage to the supplied email addresses.

        Args:
            email_restrictions:
                Email addresses that should be accepted by the Coupon.

        Returns:
            CouponBuilder:
                The current builder instance for fluent chaining.
        """
        self._overrides["email_restrictions"] = email_restrictions
        return self

    def with_expiration(self, date_expires: str) -> CouponBuilder:
        """
        Set the Coupon expiration date.

        The builder only stores the supplied value. Date-format and
        future-date validity remain domain/API concerns.
        """
        self._overrides["date_expires"] = date_expires
        return self

    def with_fields(self, **fields: Any) -> CouponBuilder:
        """
        Override arbitrary Coupon creation fields.

        This is useful while the Coupon API supports additional creation
        fields that do not yet have a dedicated fluent builder method.

        Dedicated ``with_*`` methods remain preferable for commonly used
        scenario fields because they make tests self-documenting.

        Args:
            **fields:
                Coupon creation fields to override.

        Returns:
            CouponBuilder:
                The current builder instance for fluent chaining.

        Note:
            CouponFactory remains responsible for rejecting unsupported
            fields. The Builder intentionally does not duplicate the
            Factory's field-contract validation.
        """
        self._overrides.update(fields)
        return self

    def build(self) -> dict[str, Any]:
        """
        Produce the final Coupon creation payload.

        The builder does not generate all values itself. It passes the
        collected scenario overrides to CouponFactory, which generates
        sensible defaults for everything that was not overridden.

        Returns:
            dict[str, Any]:
                Coupon creation data ready for the provisioning layer.

        Example:
            coupon = (
                CouponBuilder()
                .with_discount_type("percent")
                .with_amount("25.50")
                .with_restrictions(
                    individual_use=True,
                    free_shipping=True,
                    exclude_sale_items=True,
                    minimum_amount="20",
                    maximum_amount="100",
                )
                .with_usage_limits(
                    usage_limit=10,
                    usage_limit_per_user=2,
                    limit_usage_to_x_items=3,
                )
                .with_email_restrictions(
                    ["customer1@example.com", "customer2@example.com"]
                )
                .with_expiration("2030-12-31T23:59:59")
                .build()
            )

        Notes:
            No Coupon is created in WooCommerce by this method. It only
            prepares the in-memory creation payload.
        """
        return self._factory.build(**self._overrides)
