"""Domain-level orchestration layer for WooCommerce Coupons."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from EcommerceAPI.src.core.http_response import HttpResponse
from EcommerceAPI.src.coupons.api.coupons_api import CouponsApi
from EcommerceAPI.src.coupons.validators.coupon_validators import (
    assert_coupon_exists_and_matches_api,
)
from EcommerceAPI.src.utils.exceptions import (
    UnexpectedStatusCodeError,
    SchemaValidationError,
)
from EcommerceAPI.src.utils.pagination_utils import paginate_all_results

logger = logging.getLogger(__name__)


class CouponsHelper:
    """
    Domain-level orchestration layer for Coupons.

    Responsibilities
    ----------------
    ✔ Build request payloads
    ✔ Delegate HTTP calls to CouponsApi
    ✔ Handle happy-path and expected negative flows
    ✔ Delegate validation to the validator layer

    Return Behavior
    ---------------
    Helper methods support two return modes:

    1. Default mode (return_http_response=False):
       → Returns parsed JSON (dict or list)

    2. Response mode (return_http_response=True):
       → Returns HttpResponse for access to status, headers and timing.

    Non-Responsibilities
    --------------------
    ✘ No raw HTTP calls
    ✘ No schema validation logic
    ✘ No database access except through the explicitly supplied DAO in
      assert_coupon_exists_and_matches_db()
    ✘ No pytest fixture logic
    """

    ENDPOINT = "coupons"

    def __init__(self, coupons_api: CouponsApi):
        """Initialize the helper with the injected CouponsApi."""
        self.coupons_api = coupons_api

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------

    def create_coupon(
        self,
        code: Optional[str] = None,
        amount: Optional[str] = None,
        discount_type: Optional[str] = None,
        individual_use: Optional[bool] = None,
        product_ids: Optional[List[int]] = None,
        excluded_product_ids: Optional[List[int]] = None,
        usage_limit: Optional[int] = None,
        usage_limit_per_user: Optional[int] = None,
        limit_usage_to_x_items: Optional[int] = None,
        free_shipping: Optional[bool] = None,
        product_categories: Optional[List[int]] = None,
        excluded_product_categories: Optional[List[int]] = None,
        exclude_sale_items: Optional[bool] = None,
        minimum_amount: Optional[str] = None,
        maximum_amount: Optional[str] = None,
        email_restrictions: Optional[List[str]] = None,
        description: Optional[str] = None,
        date_expires: Optional[str] = None,
        return_http_response: bool = False,
        **kwargs: Any,
    ) -> Dict[str, Any] | HttpResponse:
        """
        Create a coupon via CouponsApi.

        Only non-None arguments are included in the request payload.
        Additional fields can be supplied through **kwargs.

        Returns parsed JSON by default, or HttpResponse when
        return_http_response=True.
        """
        payload: Dict[str, Any] = {}

        fields = {
            "code": code,
            "amount": amount,
            "discount_type": discount_type,
            "individual_use": individual_use,
            "product_ids": product_ids,
            "excluded_product_ids": excluded_product_ids,
            "usage_limit": usage_limit,
            "usage_limit_per_user": usage_limit_per_user,
            "limit_usage_to_x_items": limit_usage_to_x_items,
            "free_shipping": free_shipping,
            "product_categories": product_categories,
            "excluded_product_categories": excluded_product_categories,
            "exclude_sale_items": exclude_sale_items,
            "minimum_amount": minimum_amount,
            "maximum_amount": maximum_amount,
            "email_restrictions": email_restrictions,
            "description": description,
            "date_expires": date_expires,
        }

        payload.update(
            {key: value for key, value in fields.items() if value is not None}
        )
        payload.update(kwargs)

        logger.debug(
            "⚙️ Creating coupon with payload keys: %r",
            list(payload.keys()),
        )

        try:
            http_response = self.coupons_api.create_coupon(payload=payload)

            if return_http_response:
                return http_response

            return http_response.json

        except (UnexpectedStatusCodeError, SchemaValidationError) as e:
            logger.warning(
                "⚠️ Coupon creation raised %s: %s",
                type(e).__name__,
                e,
            )

            response_json = getattr(e, "response_json", None)
            response = getattr(e, "response", None)

            if response_json is None and response is not None:
                try:
                    response_json = response.json()
                except Exception as parse_err:
                    logger.exception(
                        "🚫 Failed to parse coupon creation error response: %s",
                        parse_err,
                    )
                    raise

            if return_http_response and response is not None:
                return response

            if response_json is not None:
                return response_json

            raise

    # ------------------------------------------------------------------
    # READ
    # ------------------------------------------------------------------

    def get_coupon_by_id(
        self,
        coupon_id: int,
        return_http_response: bool = False,
    ) -> Dict[str, Any] | HttpResponse:
        """Retrieve a coupon by ID."""
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
        """
        Fetch coupons using the shared pagination utility.

        Additional API query parameters can be supplied through params.
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
        """
        Update coupon fields.

        Supports a payload for complex updates and kwargs for simple updates.
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
        """Hard-delete a coupon by ID using force=true."""
        logger.debug("🟢 Calling 'Delete Coupon' for ID %s.", coupon_id)

        http_response = self.coupons_api.delete_coupon(
            coupon_id,
            force=True,
        )

        if return_http_response:
            return http_response

        return http_response.json

    # ------------------------------------------------------------------
    # API + DATABASE VALIDATION
    # ------------------------------------------------------------------

    def assert_coupon_exists_and_matches_db(
        self,
        coupon_id: int,
        dao,
    ) -> None:
        """
        Validate that a coupon exists in the API and matches the database.

        The DAO is supplied by the caller, following the same pattern used
        by the Products and Customers helpers.
        """
        logger.debug(
            "🔎 Validating coupon integrity for ID=%s",
            coupon_id,
        )

        # API fetch
        coupon = self.get_coupon_by_id(coupon_id)
        coupons = [coupon] if coupon else []

        # DB fetch
        db_coupon = dao.get_coupon_by_id(coupon_id)
        db_coupon_meta = dao.get_coupon_metadata(coupon_id)

        # Validation
        assert_coupon_exists_and_matches_api(
            coupons,
            coupon_id,
            db_coupon,
            db_coupon_meta,
        )

        logger.info(
            "✅ Coupon validated against API and DB (ID=%s)",
            coupon_id,
        )
