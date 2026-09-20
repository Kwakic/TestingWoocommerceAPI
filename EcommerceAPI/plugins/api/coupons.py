"""
Plugin: coupon-specific API fixtures (domain layer).

This module provides fixtures for interacting with the Coupons API domain.
It builds on the shared API infrastructure and the CouponsHelper.

Fixtures
--------
- create_valid_coupon (function):
    Factory fixture for creating a valid coupon (happy-path only).

    Behavior:
    * Delegates coupon creation to CouponsHelper
    * Validates HTTP transport (status_code == 201)
    * Extracts and validates the JSON payload
    * Registers the created coupon for shared teardown

- coupon_api_raw (function):
    Provides direct access to the underlying APIClient.

    Intended for negative tests, low-level API interaction and debugging.

Design notes
------------
* This plugin is DOMAIN-SPECIFIC (coupons only).
* Resource cleanup is owned by the framework-level shared_api_resources fixture.
* The fixture uses entity_helper() rather than indexing shared_api_resources
  directly. This avoids coupling domain plugins to the dynamically-generated
  TypedDict keys in SharedAPIResources.
* Follows the "thin fixture, rich helper" principle.
"""

from __future__ import annotations

from typing import Any, Callable

import logging
import pytest

from EcommerceAPI.src.coupons.validators.coupon_validators import (
    assert_valid_coupon_response,
)

log = logging.getLogger(__name__)


# ---------------------------------------
# Fixture: create_valid_coupon
# ---------------------------------------
@pytest.fixture(scope="function")
def create_valid_coupon(
    entity_helper,
    shared_api_resources,
) -> Callable[..., dict]:
    """
    Factory fixture for creating a validated coupon.

    Contract
    --------
    - ALWAYS returns a validated coupon dict.
    - NEVER returns HttpResponse.
    - ALWAYS validates status_code == 201.
    - ALWAYS performs CouponModel/Pydantic validation.
    - Registers the created coupon for framework teardown unless
      skip_cleanup=True.

    Usage
    -----
        coupon = create_valid_coupon(
            code="test-coupon",
            discount_type="percent",
            amount="10.00",
        )
    """

    coupon_helper = shared_api_resources["coupons_helper"]
    register = shared_api_resources["register_resource"]

    def _create_coupon(
        skip_cleanup: bool = False,
        **kwargs: Any,
    ) -> dict:
        """
        Create a valid coupon using the domain helper.

        Args:
            skip_cleanup:
                If True, the coupon is not registered for shared teardown.
            **kwargs:
                Coupon creation fields passed to CouponsHelper.create_coupon().
        """

        # 1. Call Helper and keep the HttpResponse internally so the
        #    fixture can validate transport before consuming the body.
        response = coupon_helper.create_coupon(
            return_http_response=True,
            **kwargs,
        )

        # 2. Transport validation
        assert response.status_code == 201, (
            "POST /coupons creation failed. "
            f"Expected: 201, got {response.status_code}. "
            f"Response: {response.text}"
        )

        # 3. Extract JSON
        coupon = response.json

        # 4. Structure validation
        assert_valid_coupon_response(coupon)

        # 5. Register for framework-managed teardown
        if not skip_cleanup:
            register("coupons", str(coupon["id"]))
            log.debug(
                "Registered coupon with ID=%s for cleanup.",
                coupon["id"],
            )
        else:
            log.debug(
                "Skipped registering coupon ID=%s for cleanup.",
                coupon["id"],
            )

        return coupon

    return _create_coupon


# ---------------------------------------
# Fixture: coupon_api_raw
# ---------------------------------------
@pytest.fixture(scope="function")
def coupon_api_raw(api_client):
    """
    Provide direct access to the shared APIClient for coupon API calls.

    Intended for:
        * negative tests
        * invalid payloads
        * low-level API interaction
        * debugging

    Returns:
        APIClient
    """
    return api_client
