"""
Coupon state provisioner.

This module is responsible for taking already-prepared coupon state data
and applying that state to an existing coupon in the real WooCommerce
environment through the existing CouponsHelper.

Architecture
------------
Existing coupon
    ↓
CouponStateProvisioner
    ↓
CouponsHelper
    ↓
CouponsApi
    ↓
WooCommerce

The state provisioner deliberately does NOT:
- generate test data;
- customize scenario data;
- validate HTTP status codes;
- validate response schemas;
- register cleanup;
- use pytest fixtures;
- access the database directly.

The provisioner is intentionally separate from CouponProvisioner.

CouponProvisioner creates a new coupon from creation data.
CouponStateProvisioner changes the state of an already-existing coupon.

This separation keeps resource creation and resource state mutation as
distinct lifecycle operations.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from EcommerceAPI.src.core.http_response import HttpResponse
from EcommerceAPI.src.coupons.helpers.coupons_helper import CouponsHelper


class CouponStateProvisioner:
    """
    Apply prepared state data to an existing WooCommerce coupon.

    The state provisioner is the bridge between a test-data state definition
    and the real coupon resource.

    It receives:
        - an existing coupon ID;
        - already-prepared state data.

    It delegates the actual update operation to CouponsHelper and returns
    the framework ``HttpResponse`` so the caller (normally a pytest fixture)
    can apply the appropriate setup contract.

    Example:
        state = {
            "amount": "25.00",
            "discount_type": "fixed_cart",
        }

        provisioner = CouponStateProvisioner(coupon_helper)
        response = provisioner.provision(coupon_id, state)

    The caller remains responsible for:

        HttpResponse
            ↓
        expected status validation
            ↓
        response-body/domain validation
    """

    def __init__(self, coupon_helper: CouponsHelper) -> None:
        """
        Initialize the coupon state provisioner.

        Args:
            coupon_helper:
                Existing domain helper responsible for coupon API
                orchestration.
        """
        self.coupon_helper = coupon_helper

    def provision(
        self,
        coupon_id: int,
        state: Mapping[str, Any],
    ) -> HttpResponse:
        """
        Apply prepared state data to an existing coupon.

        Args:
            coupon_id:
                WooCommerce coupon ID of the resource being modified.

            state:
                Prepared coupon state data. The mapping is passed to the
                existing CouponsHelper without generating or modifying
                its contents.

        Returns:
            HttpResponse:
                Response from the coupon update request.

        Raises:
            TypeError:
                If ``coupon_id`` is not an integer or ``state`` is not a
                mapping.

            ValueError:
                If ``coupon_id`` is not positive or ``state`` is empty.

        Notes:
            The provisioner intentionally does not validate the HTTP status.
            A setup caller may expect 200 for a successful WooCommerce update,
            but that transport assertion belongs to the caller/fixture.
        """
        # Validate the resource identifier before crossing the system
        # boundary. bool is explicitly rejected because bool is a subclass
        # of int in Python.
        if not isinstance(coupon_id, int) or isinstance(coupon_id, bool):
            raise TypeError("coupon_id must be an integer.")

        if coupon_id <= 0:
            raise ValueError("coupon_id must be greater than zero.")

        # State must already be prepared by the caller. The provisioner does
        # not generate defaults, interpret scenarios, or construct payloads.
        if not isinstance(state, Mapping):
            raise TypeError(
                "state must be a mapping containing the prepared coupon "
                "state to apply."
            )

        if not state:
            raise ValueError(
                "state cannot be empty. Prepare the coupon state before "
                "calling CouponStateProvisioner."
            )

        # Convert the mapping to a plain dict at the system boundary so the
        # helper receives an independent request payload.
        return self.coupon_helper.update_coupon(
            coupon_id=coupon_id,
            payload=dict(state),
            return_http_response=True,
        )
