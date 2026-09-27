"""CouponsHelper — domain-level orchestration layer for Coupons.

CouponsHelper sits between the Coupon test/domain layer and CouponsApi.
It provides business-focused operations while keeping transport details,
test-data generation, state construction, validation, and lifecycle concerns
in their dedicated layers.

Architecture
------------
Test / Fixture
    ↓
Factory / Builder / Provisioner
    ↓
CouponsHelper
    ↓
CouponsApi
    ↓
WooCommerce

Responsibilities
----------------
- Orchestrate Coupon operations through CouponsApi.
- Prepare and normalize request arguments required by the API operation.
- Support both successful and expected negative API flows.
- Expose parsed JSON by default or the framework HttpResponse when requested.
- Delegate schema/domain validation to the appropriate validator layer.
- Provide Coupon-specific query and pagination behavior.

Non-responsibilities
--------------------
- Generate test data.
- Decide scenario-specific Coupon creation values.
- Build Coupon creation defaults.
- Build partial Coupon state for updates.
- Register resource ownership or perform cleanup.
- Use pytest fixtures.
- Access the database directly.
- Perform schema validation inside the Helper.

Test-data generation belongs to CouponFactory and CouponBuilder.
Scenario-specific update state belongs to CouponStateBuilder.
System-boundary provisioning belongs to CouponProvisioner and
CouponStateProvisioner.

Return behavior
---------------
Helper methods that expose ``return_http_response`` support two modes:

1. Default mode (``False``):
   Return parsed JSON for clean, business-focused tests.

2. Response mode (``True``):
   Return ``HttpResponse`` when transport-level information such as status
   code, headers, elapsed time, or debugging data is required.

The Helper does not own response validation or resource lifecycle.
Those responsibilities remain with the caller, normally the fixture or
provisioning/lifecycle layer.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from EcommerceAPI.src.core.http_response import HttpResponse
from EcommerceAPI.src.coupons.api.coupons_api import CouponsApi
from EcommerceAPI.src.utils.exceptions import (
    UnexpectedStatusCodeError,
    SchemaValidationError,
)
from EcommerceAPI.src.utils.pagination_utils import paginate_all_results

logger = logging.getLogger(__name__)


class CouponsHelper:
    """Domain-level orchestration layer for Coupon operations.

    CouponsHelper provides the business-facing operations used by tests and
    provisioning components while delegating HTTP transport to CouponsApi.

    The Helper intentionally does not generate Coupon test data. A Coupon
    creation payload should already have been prepared by
    CouponFactory/CouponBuilder, while partial state for an existing Coupon
    should be prepared by CouponStateBuilder.

    The Helper therefore remains reusable across fixtures, provisioning flows,
    and direct API-oriented tests without becoming responsible for test-data
    lifecycle or pytest concerns.
    """

    ENDPOINT = "coupons"

    def __init__(self, coupons_api: CouponsApi):
        """Initialize the helper with the Coupon API layer.

        Args:
            coupons_api:
                Coupon API client responsible for HTTP transport and endpoint
                interaction. The Helper does not create the API client itself.
        """
        self.coupons_api = coupons_api

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------

    def create_coupon(
        self,
        payload: Optional[Dict[str, Any]] = None,
        return_http_response: bool = False,
        **kwargs: Any,
    ) -> Dict[str, Any] | HttpResponse:
        """Create a Coupon using already-prepared creation data.

        Coupon test-data generation deliberately happens outside the Helper.
        The payload normally comes from CouponFactory/CouponBuilder and is
        passed here by CouponProvisioner.

        ``kwargs`` remains supported for direct/simple API operations and
        backward-compatible callers.

        Behavior:
            - Success + default mode → parsed Coupon JSON.
            - Success + response mode → ``HttpResponse``.
            - Expected API failure → parsed error JSON when available, or the
              original framework exception when no response body is available.

        Args:
            payload:
                Prepared Coupon creation payload. It is not generated or
                enriched by this Helper.

            return_http_response:
                When ``False`` (default), return parsed JSON.
                When ``True``, return the framework ``HttpResponse``.

            **kwargs:
                Additional Coupon creation fields. These are merged into
                ``payload`` and override matching keys.

        Returns:
            Dict[str, Any] | HttpResponse:
                Parsed Coupon JSON by default, or the HTTP response when
                ``return_http_response=True``.

        Raises:
            UnexpectedStatusCodeError:
                Re-raised when no usable error response is available.

            SchemaValidationError:
                Re-raised when no usable error response is available.

        Notes:
            - Test-data generation belongs to CouponFactory.
            - Scenario customization belongs to CouponBuilder.
            - System-boundary provisioning belongs to CouponProvisioner.
            - This method only prepares the final API payload and delegates
              the operation to CouponsApi.
            - Response validation belongs to the caller/validator layer.
            - Resource ownership and cleanup belong to the fixture/lifecycle
              layer.
        """
        final_payload: Dict[str, Any] = {}

        # Accept either a complete prepared payload or individual fields.
        if payload:
            final_payload.update(payload)

        # Explicit keyword arguments take precedence over payload values.
        final_payload.update(kwargs)

        logger.debug(
            "⚙️ Creating coupon with payload keys: %r",
            list(final_payload.keys()),
        )

        try:
            http_response = self.coupons_api.create_coupon(payload=final_payload)

            if return_http_response:
                return http_response

            return http_response.json

        except (UnexpectedStatusCodeError, SchemaValidationError) as e:
            logger.warning(
                "⚠️ Coupon creation raised %s: %s",
                type(e).__name__,
                e,
            )

            # Preferred: APIClient attaches parsed JSON to the exception.
            response_json = getattr(e, "response_json", None)

            # Fallback: parse the raw response if structured JSON was not
            # already attached to the exception.
            if response_json is None:
                response = getattr(e, "response", None)

                if response is not None:
                    try:
                        response_json = response.json()
                    except Exception as parse_err:
                        logger.exception(
                            "🚫 Failed to parse coupon creation error response: %s",
                            parse_err,
                        )
                        raise

            response = getattr(e, "response", None)

            # Response mode preserves the framework HttpResponse so callers
            # can inspect status, headers, timing, and raw response details.
            if return_http_response and response is not None:
                return response

            # Default mode exposes a structured WooCommerce error body when
            # one is available.
            if response_json is not None:
                return response_json

            # Nothing usable was attached to the exception, so preserve the
            # original framework failure.
            raise

    # ------------------------------------------------------------------
    # READ
    # ------------------------------------------------------------------

    def get_coupon_by_id(
        self,
        coupon_id: int,
        return_http_response: bool = False,
    ) -> Dict[str, Any] | HttpResponse:
        """Retrieve a Coupon by its ID.

        Args:
            coupon_id:
                WooCommerce Coupon ID.

            return_http_response:
                When ``False`` (default), return parsed JSON.
                When ``True``, return the framework ``HttpResponse``.

        Returns:
            Dict[str, Any] | HttpResponse:
                Parsed Coupon JSON by default, or ``HttpResponse`` when
                response mode is requested.

        Raises:
            UnexpectedStatusCodeError:
                If the Coupon cannot be retrieved or the API reports an
                unexpected status.
        """
        logger.debug("🟢 Calling 'Get Coupon' for ID %s.", coupon_id)

        http_response = self.coupons_api.get_coupon(coupon_id)

        if return_http_response:
            return http_response

        return http_response.json

    def list_coupons_paginated(
        self,
        params: Optional[Dict[str, Any]] = None,
        max_pages: int = 1000,
    ) -> List[Dict[str, Any]]:
        """Fetch Coupons using the shared pagination utility.

        Args:
            params:
                Optional API query parameters. The dictionary is copied before
                the Helper adds its default pagination size.

            max_pages:
                Maximum number of pages to fetch as a safety limit.

        Returns:
            List[Dict[str, Any]]:
                Aggregated Coupon records returned by the pagination utility.

        Notes:
            Pagination is delegated to ``paginate_all_results``. The Helper
            prepares the query parameters and supplies the Coupon API endpoint,
            but does not implement the page loop itself.
        """
        logger.debug("⚙️ Calling 'List All Coupons' via pagination utility")

        params = params.copy() if params else {}
        params.setdefault("per_page", 100)

        return paginate_all_results(
            api_client=self.coupons_api.api_client,
            endpoint=self.coupons_api.ENDPOINT,
            params=params,
            max_pages=max_pages,
        )

    # ------------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------------

    def update_coupon(
        self,
        coupon_id: int,
        payload: Optional[Dict[str, Any]] = None,
        return_http_response: bool = False,
        **kwargs: Any,
    ) -> Dict[str, Any] | HttpResponse:
        """Update an existing Coupon with prepared partial state.

        The update payload is intentionally treated as state data: only fields
        supplied by the caller are sent to CouponsApi.

        CouponStateBuilder is responsible for defining scenario-specific
        update state. CouponStateProvisioner is responsible for crossing the
        system boundary. This Helper only orchestrates the update operation.

        Args:
            coupon_id:
                WooCommerce Coupon ID of the resource to update.

            payload:
                Prepared partial Coupon state.

            return_http_response:
                When ``False`` (default), return parsed JSON.
                When ``True``, return ``HttpResponse``.

            **kwargs:
                Additional update fields for simple/direct API calls.

        Returns:
            Dict[str, Any] | HttpResponse:
                Updated Coupon JSON by default, or the HTTP response when
                ``return_http_response=True``.

        Raises:
            UnexpectedStatusCodeError:
                Re-raised when no usable response body is available.

            SchemaValidationError:
                Re-raised when no usable response body is available.

        Notes:
            Response validation and resource lifecycle remain outside the
            Helper. CouponStateProvisioner returns the response to its caller
            so the setup/fixture layer can apply its own contract.
        """
        final_payload: Dict[str, Any] = {}

        if payload:
            final_payload.update(payload)

        final_payload.update(kwargs)

        logger.debug(
            "🟢 Updating coupon %s with payload keys: %r",
            coupon_id,
            list(final_payload.keys()),
        )

        try:
            http_response = self.coupons_api.update_coupon(
                coupon_id=coupon_id,
                payload=final_payload,
            )

            if return_http_response:
                return http_response

            return http_response.json

        except (UnexpectedStatusCodeError, SchemaValidationError) as e:
            logger.warning(
                "⚠️ Coupon update raised %s: %s",
                type(e).__name__,
                e,
            )

            response_json = getattr(e, "response_json", None)
            response = getattr(e, "response", None)

            # Preserve structured error JSON when available.
            if response_json is None and response is not None:
                try:
                    response_json = response.json()
                except Exception as parse_err:
                    logger.exception(
                        "🚫 Failed to parse coupon update error response: %s",
                        parse_err,
                    )
                    raise

            if return_http_response and response is not None:
                return response

            if response_json is not None:
                return response_json

            raise

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------

    def delete_coupon(
        self,
        coupon_id: int,
        return_http_response: bool = False,
    ) -> Dict[str, Any] | HttpResponse:
        """Delete (hard delete) a Coupon by ID using ``force=true``.

        Args:
            coupon_id:
                WooCommerce Coupon ID.

            return_http_response:
                When ``False`` (default), return parsed JSON.
                When ``True``, return the framework ``HttpResponse``.

        Returns:
            Dict[str, Any] | HttpResponse:
                Parsed delete response by default, or ``HttpResponse`` when
                response mode is requested.

        Notes:
            Resource ownership and cleanup decisions do not belong here.
            The Helper only orchestrates the delete operation.
        """
        logger.debug("🟢 Calling 'Delete Coupon' for ID %s.", coupon_id)

        http_response = self.coupons_api.delete_coupon(
            coupon_id,
            force=True,
        )

        if return_http_response:
            return http_response

        return http_response.json
