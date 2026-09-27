"""Coupon test-data provisioner.

This module is responsible for taking already-prepared Coupon creation data
and provisioning it into the real WooCommerce environment through the
existing CouponsHelper.

Architecture
------------
CouponFactory
    ↓
CouponBuilder
    ↓
CouponProvisioner
    ↓
CouponsHelper
    ↓
CouponsApi
    ↓
WooCommerce

The provisioner is the bridge between the in-memory test-data layer and the
real system under test.

The provisioner deliberately does NOT:
- generate test data;
- customize scenario data;
- validate HTTP status codes;
- validate response schemas;
- register cleanup;
- use pytest fixtures;
- access the database directly.

Those responsibilities belong to the appropriate layers above or below the
provisioner.

The provisioner receives already-prepared Coupon data and delegates the
actual creation operation to CouponsHelper.

It intentionally returns the framework's ``HttpResponse`` so the caller,
normally the pytest fixture, can apply the existing setup contract:

    HttpResponse
        ↓
    expected status validation
        ↓
    response-body/domain validation
        ↓
    ownership registration
        ↓
    clean Coupon dict returned to the test

Keeping those concerns separate preserves the existing framework rule that
the fixture is the gatekeeper for valid setup data.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from EcommerceAPI.src.core.http_response import HttpResponse
from EcommerceAPI.src.coupons.helpers.coupons_helper import CouponsHelper


class CouponProvisioner:
    """
    Provision prepared Coupon data into WooCommerce.

    The provisioner is the bridge between the in-memory Coupon test-data
    layer and the real system under test.

    It receives data produced by CouponFactory/CouponBuilder and delegates
    the actual creation operation to CouponsHelper.

    IMPORTANT
    ---------
    The provisioner does not decide what Coupon data should be created.

    CouponFactory/CouponBuilder are responsible for preparing the creation
    payload. CouponProvisioner is responsible only for taking that prepared
    payload across the system boundary.

    The provisioner intentionally returns ``HttpResponse`` rather than a
    parsed Coupon dictionary. This allows the caller, normally the pytest
    fixture, to apply the setup contract:

        HttpResponse
            ↓
        expected status validation
            ↓
        response-body/domain validation
            ↓
        ownership registration
            ↓
        validated Coupon dict returned to the test

    This keeps test lifecycle responsibilities in the fixture rather than
    moving assertions, validation, or cleanup into the provisioning layer.
    """

    def __init__(self, coupon_helper: CouponsHelper) -> None:
        """
        Initialize the CouponProvisioner.

        Args:
            coupon_helper:
                Existing CouponsHelper responsible for Coupon API
                orchestration.

        Notes:
            Dependency injection keeps the provisioner independent of how
            CouponsHelper is constructed and makes the provisioning layer
            easy to use from pytest fixtures or other test-data workflows.
        """
        self.coupon_helper = coupon_helper

    def provision(self, coupon_data: Mapping[str, Any]) -> HttpResponse:
        """
        Create a Coupon from already-prepared test data.

        Args:
            coupon_data:
                Creation payload produced by ``CouponFactory`` or
                ``CouponBuilder``.

        Returns:
            HttpResponse:
                The response returned by the Coupon creation request.

                The response is intentionally returned unchanged so the
                caller can inspect transport details and apply its own
                validation contract.

        Raises:
            TypeError:
                If ``coupon_data`` is not a mapping.

            ValueError:
                If no Coupon data was supplied.

        Notes:
            The provisioner does not generate missing Coupon data.

            This is intentional. Test-data generation belongs to the
            CouponFactory/CouponBuilder layer, so the provisioner must pass
            the prepared payload to CouponsHelper rather than allowing
            another layer to silently generate a second payload.

        Flow:
            CouponFactory/CouponBuilder
                ↓
            prepared Coupon data
                ↓
            CouponProvisioner
                ↓
            CouponsHelper
                ↓
            CouponsApi
                ↓
            WooCommerce
                ↓
            HttpResponse
        """
        # -----------------------------------------
        # 1️⃣ Validate the provisioning input
        # -----------------------------------------
        # The provisioner accepts prepared test data only. Rejecting invalid
        # input here prevents malformed provisioning calls from reaching the
        # domain/API layer.
        if not isinstance(coupon_data, Mapping):
            raise TypeError(
                "coupon_data must be a mapping containing the Coupon "
                "creation payload."
            )

        if not coupon_data:
            raise ValueError(
                "coupon_data cannot be empty. "
                "Build the Coupon data with CouponFactory/CouponBuilder first."
            )

        # -----------------------------------------
        # 2️⃣ Provision Coupon through domain layer
        # -----------------------------------------
        # CouponsHelper owns Coupon API orchestration. The provisioner passes
        # the already-prepared payload unchanged and explicitly requests the
        # HttpResponse because the fixture needs it for setup validation.
        return self.coupon_helper.create_coupon(
            return_http_response=True,
            **dict(coupon_data),
        )
