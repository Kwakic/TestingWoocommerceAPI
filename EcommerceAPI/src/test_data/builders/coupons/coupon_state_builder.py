"""
Coupon state builder.

This module prepares partial Coupon state for an already-existing
WooCommerce Coupon.

The state builder is intentionally different from CouponBuilder:

    CouponBuilder
        -> prepares complete creation data
        -> works with CouponFactory

    CouponStateBuilder
        -> prepares only fields that should change on an existing Coupon
        -> has no Factory dependency

Architecture
------------
Existing Coupon
      |
      v
CouponStateBuilder
      |
      v
partial state
      |
      v
CouponStateProvisioner
      |
      v
CouponsHelper
      |
      v
WooCommerce

The state builder does NOT:
- generate test data;
- create a complete Coupon payload;
- call WooCommerce;
- access the database;
- use pytest fixtures;
- register cleanup resources;
- perform assertions;
- validate API responses;
- perform provisioning.

The builder returns ``dict[str, Any]`` containing only the requested state
changes. It does not need a Factory because an existing Coupon already
provides its current state.
"""

from __future__ import annotations

from typing import Any


class CouponStateBuilder:
    """
    Build partial state for an existing WooCommerce Coupon.

    Unlike CouponBuilder, this class does not create a complete Coupon
    payload and does not depend on CouponFactory. It represents a change
    that should be applied to an already-existing Coupon.

    Example:
        state = (
            CouponStateBuilder()
            .with_amount("25.00")
            .with_discount_type("fixed_cart")
            .build()
        )

    The resulting mapping can be passed to CouponStateProvisioner.
    """

    _SUPPORTED_FIELDS = {
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

    def __init__(self) -> None:
        """Initialize an empty Coupon state."""
        self._state: dict[str, Any] = {}

    def with_code(self, code: str) -> CouponStateBuilder:
        """
        Set the Coupon code state.

        Useful for update scenarios that intentionally change the existing
        Coupon code.
        """
        self._state["code"] = code
        return self

    def with_discount_type(self, discount_type: str) -> CouponStateBuilder:
        """
        Set the Coupon discount type state.

        Supported values exercised by the current Coupon tests include:
            - ``percent``
            - ``fixed_cart``
            - ``fixed_product``

        The builder stores the requested value without validating business
        rules. API/domain validation remains the responsibility of the
        update operation and its tests.
        """
        self._state["discount_type"] = discount_type
        return self

    def with_amount(self, amount: str) -> CouponStateBuilder:
        """Set the Coupon discount amount state."""
        self._state["amount"] = amount
        return self

    def with_restrictions(
        self,
        *,
        individual_use: bool | None = None,
        free_shipping: bool | None = None,
        exclude_sale_items: bool | None = None,
        minimum_amount: str | None = None,
        maximum_amount: str | None = None,
    ) -> CouponStateBuilder:
        """
        Configure common Coupon restriction state fields.

        Only explicitly provided values are added to the state mapping.
        ``None`` means that the corresponding field is not changed.
        """
        restrictions = {
            "individual_use": individual_use,
            "free_shipping": free_shipping,
            "exclude_sale_items": exclude_sale_items,
            "minimum_amount": minimum_amount,
            "maximum_amount": maximum_amount,
        }

        self._state.update(
            {key: value for key, value in restrictions.items() if value is not None}
        )
        return self

    def with_usage_limits(
        self,
        *,
        usage_limit: int | None = None,
        usage_limit_per_user: int | None = None,
        limit_usage_to_x_items: int | None = None,
    ) -> CouponStateBuilder:
        """
        Configure Coupon usage-limit state fields.

        Only explicitly provided values are added to the state mapping.
        """
        usage_limits = {
            "usage_limit": usage_limit,
            "usage_limit_per_user": usage_limit_per_user,
            "limit_usage_to_x_items": limit_usage_to_x_items,
        }

        self._state.update(
            {key: value for key, value in usage_limits.items() if value is not None}
        )
        return self

    def with_product_ids(
        self,
        product_ids: list[int],
    ) -> CouponStateBuilder:
        """Set the products included by the Coupon."""
        self._state["product_ids"] = list(product_ids)
        return self

    def with_excluded_product_ids(
        self,
        product_ids: list[int],
    ) -> CouponStateBuilder:
        """Set the products excluded by the Coupon."""
        self._state["excluded_product_ids"] = list(product_ids)
        return self

    def with_product_categories(
        self,
        product_categories: list[int],
    ) -> CouponStateBuilder:
        """Set the product categories included by the Coupon."""
        self._state["product_categories"] = list(product_categories)
        return self

    def with_excluded_product_categories(
        self,
        product_categories: list[int],
    ) -> CouponStateBuilder:
        """Set the product categories excluded by the Coupon."""
        self._state["excluded_product_categories"] = list(product_categories)
        return self

    def with_email_restrictions(
        self,
        email_restrictions: list[str],
    ) -> CouponStateBuilder:
        """
        Restrict Coupon usage to the supplied email addresses.
        """
        self._state["email_restrictions"] = list(email_restrictions)
        return self

    def with_expiration(
        self,
        date_expires: str,
    ) -> CouponStateBuilder:
        """
        Set the Coupon expiration date.

        The builder only stores the supplied value. Date-format and
        business-rule validation remain outside the builder.
        """
        self._state["date_expires"] = date_expires
        return self

    def with_description(
        self,
        description: str,
    ) -> CouponStateBuilder:
        """Set the Coupon description state."""
        self._state["description"] = description
        return self

    def with_fields(self, **fields: Any) -> CouponStateBuilder:
        """
        Add supported Coupon state fields.

        Dedicated ``with_*`` methods are preferred for commonly used
        scenarios because they make tests self-documenting.

        Raises:
            TypeError:
                If any supplied field is not supported by the state builder.
        """
        unsupported = set(fields) - self._SUPPORTED_FIELDS

        if unsupported:
            raise TypeError(
                "Unsupported coupon state field(s): " + ", ".join(sorted(unsupported))
            )

        self._state.update(fields)
        return self

    def build(self) -> dict[str, Any]:
        """
        Return the prepared partial Coupon state.

        Raises:
            ValueError:
                If no state fields have been configured.

        Returns:
            dict[str, Any]:
                Partial state ready for CouponStateProvisioner.
        """
        if not self._state:
            raise ValueError(
                "Coupon state cannot be empty. Configure at least one field."
            )

        return dict(self._state)
