"""
ProductsHelper — Domain-level orchestration layer for Products (workflow).

Responsibilities
----------------
✔ Build request payloads
✔ Delegate HTTP calls to ProductsApi (no direct HTTP usage)
✔ Handle happy-path and expected negative flows
✔ Delegate validation to validator layer

Return Behavior
---------------
Helper methods support two return modes:

1. Default mode (return_http_response=False):
   → Returns parsed JSON (dict or list)
   → Used for most tests (clean, simple, business-focused)

2. Response mode (return_http_response=True):
   → Returns HttpResponse object
   → Used when access to transport data is required:
       - status_code
       - headers
       - elapsed time
       - request/response debugging

Design Principles
-----------------
✔ Helper abstracts transport layer for most tests
✔ Keeps tests readable and business-focused
✔ Allows opt-in access to full HTTP response when needed
✔ Supports both positive and negative scenarios

Non-Responsibilities
--------------------
✘ No raw HTTP calls (handled by APIClient)
✘ No schema validation logic (delegated to validators)
✘ No business validators
✘ No database access
✘ No pytest fixtures
"""

from __future__ import annotations

import logging
import random
from typing import Any, Dict, List, Optional, Tuple

from EcommerceAPI.src.utils.exceptions import (
    UnexpectedStatusCodeError,
    SchemaValidationError,
)
from EcommerceAPI.src.utils.pagination_utils import paginate_all_results
from EcommerceAPI.src.utils.date_timestamp_utils import safe_parse_utc_datetime
from EcommerceAPI.src.core.http_response import HttpResponse
from EcommerceAPI.src.products.api.products_api import ProductsApi
from EcommerceAPI.src.products.validators.product_validators import (
    assert_product_exists_and_matches_api,
)

logger = logging.getLogger(__name__)


class ProductsHelper(object):
    """
    Domain-level orchestration layer for Products.

    Provides clean, business-focused API for product operations
    while delegating transport and validation concerns to specialized layers.
    """

    ENDPOINT = "products"

    def __init__(self, products_api: ProductsApi):
        """
        Args:
            products_api: Domain API client (wraps APIClient)
        """
        self.products_api = products_api

    # -------- READ / GET HELPERS --------

    def get_product_by_id(
        self, product_id: int, return_http_response: bool = False
    ) -> Dict[str, Any] | HttpResponse:
        """
        Retrieve a product by its ID.

        Args:
            product_id (int): Product ID.
            return_http_response:  - False (default) → returns parsed JSON (dict)
                                   - True → returns HttpResponse (status_code, headers, elapsed, etc.)

        Returns:
            dict: Parsed product JSON response
            HttpResponse: if return_http_response=True

        Raises:
            UnexpectedStatusCodeError: If product not found or API error
        """
        logger.debug("🟢 Calling 'Get Product' for ID %s.", product_id)

        http_response = self.products_api.get_product(product_id)

        if return_http_response:
            return http_response

        return http_response.json

    def list_products_paginated(
        self,
        params: Optional[Dict[str, Any]] = None,
        max_pages: int = 1000,
        created_before: Optional[str] = None,
        created_after: Optional[str] = None,
        status: Optional[str] = None,
        sku: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch all products using the shared paginate_all_results utility and optionally filter by creation
        dates (timestamps), status, SKU, and search term.

        Args:
            params (Optional[dict]): Additional query parameters.
            max_pages (int): Max pages to fetch.
            created_before (Optional[str]): ISO 8601 timestamp to filter products created before.
            created_after (Optional[str]): ISO 8601 timestamp to filter products created after.
            status (Optional[str]): Product status filter (draft, pending, private, publish, etc.).
            sku (Optional[str]): SKU filter.
            search (Optional[str]): Search term filter.

        Returns:
            List[dict]: List of filtered products.

        Raises:
            ValueError: If status is invalid or date format is invalid
        """
        VALID_STATUSES = {
            "draft",
            "pending",
            "private",
            "publish",
            "future",
            "trash",
            "any",
        }

        logger.debug("⚙️ Calling 'List All Products' via pagination utility")

        # -------------------------------------------
        # 🔧 Prepare and sanitize query parameters
        # -------------------------------------------
        params = params.copy() if params else {}
        params.setdefault("per_page", 100)

        if status:
            if status not in VALID_STATUSES:
                raise ValueError(
                    f"❌ Invalid status '{status}'. Must be one of: {', '.join(sorted(VALID_STATUSES))}"
                )
            params["status"] = status

        if sku:
            params["sku"] = sku

        if search:
            params["search"] = search

        if created_after:
            params["after"] = created_after

        if created_before:
            params["before"] = created_before

        # -------------------------------------------
        # 🚀 Paginate through all pages using the utility
        # -------------------------------------------
        all_products = paginate_all_results(
            api_client=self.products_api.api_client,
            endpoint=self.products_api.ENDPOINT,
            params=params,
            max_pages=max_pages,
        )

        # -------------------------------------------
        # 🧹 Apply post-fetch filtering (date_created_gmt)
        # -------------------------------------------
        filtered_products = []

        parse_dt = safe_parse_utc_datetime

        cutoff_before = cutoff_after = None

        # 🧪 Parse created_before as UTC-aware datetime (if provided)
        if created_before:
            try:
                cutoff_before = parse_dt(created_before)
            except ValueError:
                logger.warning("⚠️ Invalid 'created_before' format. Use ISO 8601.")
                return []

        # 🧪 Parse created_after as UTC-aware datetime (if provided)
        if created_after:
            try:
                cutoff_after = parse_dt(created_after)
            except ValueError:
                logger.warning("⚠️ Invalid 'created_after' format. Use ISO 8601.")
                return []

        # 🔍 Iterate through all fetched products and apply time-based filters
        for product in all_products:
            created_gmt = product.get("date_created_gmt")
            try:
                # ✅ Parse product date as offset-aware datetime in UTC
                created_date = parse_dt(created_gmt) if created_gmt else None
                if created_date:
                    # ❌ Skip product if it was created *after* the allowed upper bound
                    if cutoff_before and created_date >= cutoff_before:
                        continue
                    # ❌ Skip product if it was created *before* the allowed lower bound
                    if cutoff_after and created_date <= cutoff_after:
                        continue
                # ✅ Keep product — passed all time filters
                filtered_products.append(product)
            except Exception as e:
                logger.warning(
                    "⚠️ Could not parse 'date_created_gmt' for product ID %s: %s",
                    product.get("id"),
                    e,
                )
                continue

        # ✅ Return all valid products that passed filter
        return filtered_products

    def list_products_for_test(
        self,
        test_run_id: str,
        per_page: int = 10,
        max_pages: int = 100,
        extra_params: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Test-focused helper for fetching products created within a test run.

        WHY:
        ----
        - Avoids global DB dependency
        - Guarantees deterministic dataset
        - Reusable across all list tests
        - Keeps tests clean (no manual params building)

        Args:
            test_run_id (str): Unique identifier used in test data

            per_page (int): Pagination size

            max_pages (int): Safety cap to avoid infinite loops

            extra_params (dict): Optional additional filters (future-proof)

        Returns:
            List[dict]: Filtered products belonging to this test run
        """
        logger.debug(
            "🧪 Fetching test products (run_id=%s, per_page=%s, max_pages=%s)",
            test_run_id,
            per_page,
            max_pages,
        )

        params = {
            "per_page": per_page,
            "search": test_run_id,
        }

        if extra_params:
            params.update(extra_params)

        return self.list_products_paginated(
            params=params,
            max_pages=max_pages,
        )

    # -------- CREATE / UPDATE HELPERS --------

    def create_product(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        price: Optional[float] = None,
        sku: Optional[str] = None,
        status: str = "publish",
        return_http_response: bool = False,
        **kwargs,
    ) -> Dict[str, Any] | HttpResponse:
        """
        Create a product via ProductsApi.

        Behavior:
        - Supports positive + negative testing
        - On success → return parsed JSON dict
        - On expected failure:
            - return parsed error JSON (if available)
            - otherwise re-raise original exception

        Args:
            name: Optional product name
            description: Optional description
            price: Optional price
            sku: Optional SKU
            status: Product status (default: "publish")
            return_http_response:  - False (default) → returns parsed JSON (dict)
                              - True → returns HttpResponse (status_code, headers, elapsed, etc.)
            **kwargs: Additional payload fields

        Returns:
            Dict[str, Any] | HttpResponse:
                - dict → default mode (parsed JSON)
                - HttpResponse → if return_http_response=True

        Raises:
            UnexpectedStatusCodeError, SchemaValidationError: Re-raised if no parsed error body is available.
        """
        payload: Dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        if price is not None:
            payload["price"] = price
        if sku is not None:
            payload["sku"] = sku

        payload["status"] = status
        payload.update(kwargs)

        logger.debug("⚙️ Creating product with payload keys: %r", list(payload.keys()))

        try:
            http_response = self.products_api.create_product(payload=payload)

            if return_http_response:
                return http_response

            return http_response.json
        except (UnexpectedStatusCodeError, SchemaValidationError) as e:
            logger.warning("⚠️ Product creation raised %s: %s", type(e).__name__, e)

            response_json = getattr(e, "response_json", None)

            if response_json is None:
                resp = getattr(e, "response", None)
                if resp is not None:
                    try:
                        response_json = resp.json()
                    except Exception as parse_err:
                        logger.exception(
                            "🚫 Failed to parse error response JSON from create_product: %s",
                            parse_err,
                        )
                        raise

            response = getattr(e, "response", None)

            if return_http_response and response is not None:
                return response

            if response_json is not None:
                return response_json

            raise

    def update_product(
        self,
        product_id: int,
        payload: Optional[Dict[str, Any]] = None,
        return_http_response: bool = False,
        **kwargs,
    ) -> Dict[str, Any] | HttpResponse:
        """
        Update product fields.

        Supports:
        - payload: for full/complex updates
        - return_http_response:  - False (default) → returns parsed JSON (dict)
                            - True → returns HttpResponse (status_code, headers, elapsed, etc.)
        - kwargs: for simple updates
        """
        final_payload: Dict[str, Any] = {}

        if payload:
            final_payload.update(payload)

        final_payload.update(kwargs)

        logger.debug(
            "🟢 Updating product %s with payload keys: %r",
            product_id,
            list(final_payload.keys()),
        )

        try:
            http_response = self.products_api.update_product(
                product_id=product_id, payload=final_payload
            )

            if return_http_response:
                return http_response

            return http_response.json

        except (UnexpectedStatusCodeError, SchemaValidationError) as e:
            logger.warning("⚠️ Product update raised %s: %s", type(e).__name__, e)

            response_json = getattr(e, "response_json", None)
            response = getattr(e, "response", None)

            if return_http_response and response is not None:
                return response

            if response_json is not None:
                return response_json

            raise

    def delete_product(
        self, product_id: int, return_http_response: bool = False
    ) -> Dict[str, Any] | HttpResponse:
        """
        Delete (hard delete) a product by ID using force=true.

        Args:
            product_id (int): Product ID.
            return_http_response:  - False (default) → returns parsed JSON (dict)
                              - True → returns HttpResponse (status_code, headers, elapsed, etc.)

        Returns:
            dict: Parsed JSON response from delete
        """
        logger.debug("🟢 Calling 'Delete Product' for ID %s.", product_id)

        http_response = self.products_api.delete_product(product_id, force=True)

        if return_http_response:
            return http_response

        return http_response.json

    # -------- UTILITY HELPERS --------

    @staticmethod
    def generate_sale_price(
        regular_price: float, min_discount: float = 5.0, max_discount: float = 50.0
    ) -> Tuple[str, float]:
        """
        Generates a valid sale price that is less than the regular price.

        Args:
            regular_price (float): Base price
            min_discount (float): Minimum discount percentage
            max_discount (float): Maximum discount percentage

        Returns:
            Tuple[sale_price_str, discount_percentage]: Sale price and discount %
        """
        discount_percentage = random.uniform(min_discount, max_discount)
        discount_amount = regular_price * (discount_percentage / 100.0)
        sale_price_value = regular_price - discount_amount
        return str(round(sale_price_value, 2)), discount_percentage

    # -------- VALIDATION HELPERS --------

    def assert_product_exists_and_matches_db(self, product_id: int, dao) -> None:
        """
        High-level helper that validates that a product exists
        in the API and matches the database record.

        Responsibilities:
            - Fetch product from API
            - Fetch product record from DB
            - Call validation layer

        This keeps tests clean and avoids repeated boilerplate.

        Args:
            product_id (int): Product ID
            dao: Product DAO instance.
        """
        logger.debug("🔎 Validating product integrity for ID=%s", product_id)

        # --------- API fetch (wrap in list to match validator signature) ---------
        product = self.get_product_by_id(product_id)
        products = [product] if product else []

        # --------- DB fetch ---------
        db_product = dao.get_product_by_id(product_id)

        # --------- Assertion layer ---------
        assert_product_exists_and_matches_api(
            products,
            product_id,
            db_product,
        )

        logger.info("✅ Product validated against API and DB (ID=%s)", product_id)
