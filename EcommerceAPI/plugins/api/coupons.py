"""
Plugin: coupon-specific API fixtures (domain layer).

This module provides fixtures for interacting with the Coupons API domain.
It builds on top of shared infrastructure (api_client), domain helpers,
and the Coupon test-data/provisioning architecture.

Fixtures
--------
- create_valid_coupon (function):
    Factory fixture for creating a valid Coupon (happy-path only).

    Behavior:
    * Builds valid Coupon creation data through `CouponBuilder`
    * Uses `CouponFactory` for unspecified valid defaults
    * Provisions the Coupon through `CouponProvisioner`
    * Validates HTTP transport (status_code == 201)
    * Extracts and returns the JSON payload as a dict
    * Validates schema + domain rules via validators
    * Registers created resources for cleanup via shared_api_resources

    Contract:
    * ALWAYS returns a valid Coupon dict
    * NEVER returns HttpResponse
    * ALWAYS performs validation (transport + response structure)
    * Registers ownership unless `skip_cleanup=True`

    Intended usage:
    * Positive (happy-path) tests
    * Scenarios where a valid Coupon is required as a precondition
    * Tests that need scenario-specific Coupon creation data

- coupon_api_raw (function):
    Provides direct access to the underlying APIClient.

    Behavior:
    * Bypasses CouponFactory and CouponBuilder
    * Bypasses CouponProvisioner and CouponsHelper
    * Performs no fixture-level response validation
    * Provides direct API control to the test

    Intended usage:
    * Negative tests (invalid payloads, edge cases)
    * Low-level API interaction
    * Debugging scenarios

Design notes
------------
* This plugin is DOMAIN-SPECIFIC (coupons only).
* Relies on `shared_api_resources` provided by the entities plugin.
* Uses CouponFactory/CouponBuilder for test-data preparation.
* Uses CouponProvisioner to cross the system boundary.
* Uses CouponsHelper for domain/API orchestration.
* Uses validators for response structure and business-rule enforcement.
* Registers only explicitly test-created Coupons for cleanup.
* Keeps the pytest fixture as the lifecycle gatekeeper between the
  test-data/provisioning layers and the test.

Notes
-----
- This plugin should NOT contain shared logic used by other domains.
- Each entity (customers, products, orders, etc.) should have its own
  plugin module.
- Test-data generation belongs to the Coupon Factory/Builder layer.
- System provisioning belongs to the Coupon Provisioner layer.
- API/domain orchestration belongs to the Coupons Helper layer.
- Fixture-level validation and ownership registration belong here.
- Negative tests should use `coupon_api_raw` when direct API control
  is required.
- Follows the "thin fixture, explicit lifecycle gatekeeper" principle.

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
        ↓
    HttpResponse
        ↓
    Fixture validation
        ↓
    Ownership registration
        ↓
    validated Coupon dict
"""

from __future__ import annotations

from typing import Callable
import logging

import pytest

from EcommerceAPI.src.coupons.validators.coupon_validators import (
    assert_valid_coupon_response,
)

from EcommerceAPI.src.test_data.builders.coupons.coupon_builder import (
    CouponBuilder,
)

from EcommerceAPI.src.test_data.provisioning.coupons.coupon_provisioner import (
    CouponProvisioner,
)

log = logging.getLogger(__name__)


# ---------------------------------------
# Fixture: create_valid_coupon
# ---------------------------------------
@pytest.fixture(scope="function")
def create_valid_coupon(shared_api_resources) -> Callable[..., dict]:
    """
    This fixture acts as the test-facing "Gatekeeper" between the
    test-data/provisioning layers and tests.

    It:
        ✔ Builds valid Coupon creation data through CouponBuilder
        ✔ Uses CouponFactory for unspecified valid defaults
        ✔ Provisions the Coupon through CouponProvisioner
        ✔ Receives the HttpResponse from the provisioning flow
        ✔ Validates the setup transport status (201)
        ✔ Extracts and validates the response body
        ✔ Registers the created resource for cleanup
        ✔ Returns a clean dict to the test

    IMPORTANT:
    ----------
    The Coupon test-data architecture prepares the creation payload before
    it reaches the CouponsHelper.

        CouponBuilder
            ↓
        CouponFactory
            ↓
        CouponProvisioner
            ↓
        CouponsHelper / API
            ↓
        HttpResponse

    The fixture receives that HttpResponse so it can enforce the setup
    contract before exposing the Coupon to the test.

    RETURN CONTRACT:
    ----------------
    - ALWAYS returns dict
    - NEVER returns HttpResponse
    - NEVER returns invalid data
    - Registers ownership unless skip_cleanup=True

    WHEN TO USE:
    ------------
    ✅ Positive tests (happy path)
    ✅ Tests requiring a valid Coupon as a precondition

    ❌ Negative tests → use coupon_api_raw

    EXAMPLE:
    --------
    coupon = create_valid_coupon(
        discount_type="percent",
        amount="10.00",
    )
    assert coupon["code"]

    Args:
        shared_api_resources (dict):
            Injected shared resources containing the CouponsHelper and
            ownership registry.

    Returns:
        Callable[..., dict]:
            A function that creates a Coupon with optional
            scenario-specific fields.

    How it works:
        CouponBuilder
            ↓
        CouponFactory
            ↓
        CouponProvisioner
            ↓
        CouponsHelper / API
            ↓
        HttpResponse
            ↓
        Fixture validation + ownership registration
            ↓
        validated Coupon dict
    """
    coupon_helper = shared_api_resources["coupons_helper"]
    register = shared_api_resources["register_resource"]

    coupon_provisioner = CouponProvisioner(coupon_helper)

    def _create_coupon(skip_cleanup: bool = False, **kwargs) -> dict:
        """
        Create a valid Coupon (happy-path ONLY).

        🔥 CONTRACT (IMPORTANT):
        -------------------------
        - ALWAYS returns a valid Coupon dict
        - ALWAYS validates status_code == 201
        - ALWAYS validates the Coupon response
        - NEVER returns HttpResponse
        - NEVER returns invalid data
        - Registers the Coupon for cleanup unless skip_cleanup=True

        FLOW:
        -----
        1. Build scenario-specific creation data
        2. Apply CouponFactory defaults
        3. Provision through CouponProvisioner
        4. Validate setup status_code == 201
        5. Extract JSON
        6. Validate response structure + domain rules
        7. Register cleanup
        8. Return validated Coupon dict

            CouponBuilder
                ↓
            CouponFactory
                ↓
            CouponProvisioner
                ↓
            CouponsHelper / API
                ↓
            HttpResponse
                ↓
            status validation
                ↓
            response.json
                ↓
            Coupon validation
                ↓
            cleanup registration
                ↓
            return dict to test

        Args:
            skip_cleanup (bool):
                If True → Coupon is NOT registered for cleanup.

            **kwargs:
                Scenario-specific Coupon creation fields, such as:
                code, discount_type, amount, restrictions, usage limits,
                email restrictions, or expiration.

                Any field not supplied here is generated/provided by
                CouponFactory through CouponBuilder.

        Returns:
            dict:
                Validated Coupon object.

                The fixture uses the HttpResponse internally to validate
                the setup contract but never exposes it to the test.

        Raises:
            AssertionError:
                If status_code != 201.

            SchemaValidationError:
                If the Coupon response fails the configured response
                validation.
        """

        # -----------------------------------------
        # 1️⃣ Build Coupon creation data
        # -----------------------------------------
        # CouponBuilder collects scenario-specific overrides.
        # CouponFactory supplies all unspecified valid defaults.
        coupon_data = CouponBuilder().with_fields(**kwargs).build()

        # -----------------------------------------
        # 2️⃣ Provision Coupon
        # -----------------------------------------
        # CouponProvisioner crosses the system boundary through the
        # existing CouponsHelper/API architecture and returns the
        # HttpResponse required by this fixture's setup contract.
        response = coupon_provisioner.provision(coupon_data)

        # -----------------------------------------
        # 3️⃣ Transport validation (FAIL FAST)
        # -----------------------------------------
        # The setup operation must successfully create the Coupon.
        # response.text is deliberately included because it preserves the
        # server's actual error body when creation fails.
        assert response.status_code == 201, (
            "POST /coupons creation failed. "
            f"Expected: 201, got {response.status_code}. "
            f"Response: {response.text}"
        )

        # -----------------------------------------
        # 4️⃣ Extract JSON to validate body
        # -----------------------------------------
        coupon = response.json

        # -----------------------------------------
        # 5️⃣ Structure + business validation
        # -----------------------------------------
        # Validate the Coupon returned by WooCommerce before exposing it
        # to the test.
        assert_valid_coupon_response(coupon)

        # -----------------------------------------
        # 6️⃣ Cleanup registration
        # -----------------------------------------
        # Only explicitly test-created Coupons are registered.
        # Seeded/shared resources are not registered by this fixture.
        if not skip_cleanup:
            register("coupons", coupon["id"])
            log.debug(
                "ℹ️ Registered coupon with ID: %s for cleanup.",
                coupon["id"],
            )
        else:
            log.debug(
                "ℹ️ Skipped registering coupon %s for cleanup.",
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
    Provides direct access to APIClient for Coupons API calls without
    Coupon test-data/provisioning or fixture validation.

    When to use:
        - Testing invalid payloads, malformed fields, or bad requests
        - Testing edge cases that deliberately bypass valid-data setup
        - Low-level API interaction
        - Debugging API behavior

    This fixture:
        - Returns the API client's HttpResponse
        - Skips CouponFactory
        - Skips CouponBuilder
        - Skips CouponProvisioner
        - Skips CouponsHelper
        - Performs no fixture-level response validation

    IMPORTANT:
        The fixture is intentionally outside the normal positive-test
        architecture. Negative tests often need complete control over the
        payload and therefore must not be forced through valid test-data
        generation.

    Returns:
        HttpResponse:
            The response produced by the underlying APIClient.

    Notes:
        - ⚠️ "Raw" means raw from the Coupon fixture architecture;
          it still uses the project's APIClient/HttpResponse abstraction.
        - This fixture should not be used when a valid Coupon precondition
          is required. Use create_valid_coupon instead.
    """
    return api_client
