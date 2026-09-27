"""ProductsHelper — domain-level orchestration layer for Products.

ProductsHelper sits between the Product test/domain layer and ProductsApi.
It provides business-focused operations while keeping transport details and
validation responsibilities in their dedicated layers.

Architecture
------------
Test / Fixture
    ↓
Factory / Builder / Provisioner
    ↓
ProductsHelper
    ↓
ProductsApi
    ↓
WooCommerce

Responsibilities
----------------
- Orchestrate Product operations through ProductsApi.
- Prepare and normalize request arguments required by the API operation.
- Support both successful and expected negative API flows.
- Expose parsed JSON by default or the framework HttpResponse when requested.
- Delegate schema/domain validation to the appropriate validator layer.
- Provide Product-specific query and pagination behavior.

Non-responsibilities
--------------------
- Generate test data.
- Decide scenario-specific Product values.
- Build Product creation defaults.
- Build partial Product state for updates.
- Register resource ownership or perform cleanup.
- Use pytest fixtures.
- Access the database directly.
- Perform schema validation inside the Helper.

Test-data generation belongs to ProductFactory and ProductBuilder. Scenario-
specific update state belongs to ProductStateBuilder. System-boundary
provisioning belongs to ProductProvisioner and ProductStateProvisioner.

Return behavior
---------------
Helper methods that expose ``return_http_response`` support two modes:

1. Default mode (``False``): return parsed JSON for clean, business-focused
   tests.
2. Response mode (``True``): return ``HttpResponse`` when transport-level
   information such as status code, headers, elapsed time, or debugging data
   is required.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from EcommerceAPI.src.utils.exceptions import (
    UnexpectedStatusCodeError,
    SchemaValidationError,
)
from EcommerceAPI.src.utils.pagination_utils import paginate_all_results
from EcommerceAPI.src.utils.date_timestamp_utils import safe_parse_utc_datetime
from EcommerceAPI.src.core.http_response import HttpResponse
from EcommerceAPI.src.products.api.products_api import ProductsApi

logger = logging.getLogger(__name__)


class ProductsHelper(object):
    """Domain-level orchestration layer for Product operations.

    ProductsHelper provides the business-facing operations used by tests and
    provisioning components while delegating HTTP transport to ProductsApi.

    The Helper intentionally does not generate Product test data. A Product
    payload should already have been prepared by ProductFactory/ProductBuilder
    when creating a resource, or by ProductStateBuilder when updating an
    existing resource.

    The Helper therefore remains reusable across fixtures, provisioning flows,
    and direct API-oriented tests without becoming responsible for test-data
    lifecycle or pytest concerns.
    """

    ENDPOINT = "products"

    def __init__(self, products_api: ProductsApi):
        """Initialize the helper with the Product API layer.

        Args:
            products_api:
                Product API client responsible for HTTP transport and endpoint
                interaction. The Helper does not create the API client itself.
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
        payload: Optional[Dict[str, Any]] = None,
        return_http_response: bool = False,
        **kwargs,
    ) -> Dict[str, Any] | HttpResponse:
        """Create a Product using already-prepared creation data.

        Product test-data generation deliberately happens outside the Helper.
        The payload normally comes from ProductFactory/ProductBuilder and is
        passed here by ProductProvisioner. ``kwargs`` remains supported as a
        convenience for direct API-oriented tests and backward-compatible
        callers.

        Behavior:
            - Success + default mode → parsed Product JSON.
            - Success + response mode → ``HttpResponse``.
            - Expected API failure → parsed error JSON when available, or the
              original framework exception when no response body is available.

        Args:
            payload:
                Prepared Product creation payload. It is not generated or
                enriched by this Helper.
            return_http_response:
                When ``False`` (default), return parsed JSON. When ``True``,
                return the framework ``HttpResponse``.
            **kwargs:
                Additional Product fields. These are merged into ``payload``
                and are primarily useful for direct/simple API operations.

        Returns:
            Dict[str, Any] | HttpResponse:
                Parsed Product JSON by default, or the HTTP response when
                ``return_http_response=True``.

        Raises:
            UnexpectedStatusCodeError:
                Re-raised when an expected error response cannot be returned
                as parsed JSON or an ``HttpResponse``.
            SchemaValidationError:
                Re-raised when no usable error response is available.

        Notes:
            This method does not register cleanup. Resource ownership belongs
            to the fixture/lifecycle layer.
        """
        final_payload: Dict[str, Any] = {}

        if payload:
            final_payload.update(payload)

        final_payload.update(kwargs)

        logger.debug(
            "⚙️ Creating product with payload keys: %r",
            list(final_payload.keys()),
        )

        try:
            http_response = self.products_api.create_product(payload=final_payload)

            if return_http_response:
                return http_response

            return http_response.json

        except (UnexpectedStatusCodeError, SchemaValidationError) as e:
            logger.warning(
                "⚠️ Product creation raised %s: %s",
                type(e).__name__,
                e,
            )

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
        """Update an existing Product with prepared partial state.

        The update payload is intentionally treated as state data: only fields
        supplied by the caller are sent to ProductsApi. ProductStateBuilder is
        responsible for defining scenario-specific state; this Helper only
        orchestrates the update operation.

        Args:
            product_id:
                WooCommerce Product ID of the resource to update.
            payload:
                Prepared partial Product state.
            return_http_response:
                When ``False`` (default), return parsed JSON. When ``True``,
                return ``HttpResponse``.
            **kwargs:
                Additional update fields for simple/direct API calls.

        Returns:
            Dict[str, Any] | HttpResponse:
                Updated Product JSON by default, or the HTTP response when
                ``return_http_response=True``.

        Raises:
            UnexpectedStatusCodeError, SchemaValidationError:
                Re-raised when no usable response body is available.

        Notes:
            Response validation and resource lifecycle remain outside the
            Helper. ProductStateProvisioner returns this response to its
            caller so the setup/fixture layer can apply its contract.
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
                product_id=product_id,
                payload=final_payload,
            )

            if return_http_response:
                return http_response

            return http_response.json

        except (UnexpectedStatusCodeError, SchemaValidationError) as e:
            logger.warning(
                "⚠️ Product update raised %s: %s",
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
