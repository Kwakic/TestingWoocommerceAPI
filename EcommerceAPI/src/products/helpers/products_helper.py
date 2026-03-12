# """
# ProductsHelper — wrapper/helper for working with WooCommerce products using RequestUtility.
#
# Purpose / changes:
# - Require injection of the shared RequestUtility instance (best practice).
# - Use centralized exceptions module for consistent error handling.
# - Replace ad-hoc print() usage with structured logging.
# - Provide robust pagination and filter handling for listing products.
# - Use ProductsDao for any DB-backed checks (example placeholder included).
#
# Usage:
#     helper = ProductsHelper(request_utility=request_utility)
#     helper.call_create_product(payload)
#     helper.call_list_products(status="publish", limit=50)
# """
# from __future__ import annotations
#
# import copy
# import logging
# import random
# from typing import Any, Dict, List, Optional, Tuple
#
# from EcommerceAPI.src.clients.api_client import APIClient
# from EcommerceAPI.src.utils.exceptions import APIRequestException
# from EcommerceAPI.src.products.dao.products_dao import ProductsDAO
#
# logger = logging.getLogger(__name__)
#
#
# class ProductsHelper:
#     """
#     Helper for product-related API interactions.
#
#     The helper requires an injected RequestUtility instance to ensure all helpers and tests
#     use the same configured HTTP client (the session-scoped `request_utility` fixture).
#     """
#
#     ENDPOINT = "products"
#
#     def __init__(self, request_utility: APIClient):
#         """
#         Require an injected RequestUtility for consistent configuration and testability.
#
#         Raises:
#             ValueError: if request_utility is None
#             TypeError: if request_utility is not an instance of RequestUtility
#         """
#         if request_utility is None:
#             raise ValueError(
#                 "ProductsHelper requires a RequestUtility instance. "
#                 "Pass `request_utility` from your conftest (session-scoped fixture)."
#             )
#         if not isinstance(request_utility, APIClient):
#             raise TypeError("request_utility must be an instance of RequestUtility")
#
#         self.request_utility = request_utility
#         # Optional DAO for DB-backed validations (instantiate as needed)
#         self.dao = ProductsDAO()
#
#     # ------------------------
#     # CRUD wrappers
#     # ------------------------
#     def call_retrieve_product(self, product_id: int, expected_status_code: int = 200) -> Dict[str, Any]:
#         logger.debug("🟢 Calling 'Get Product' for id=%s", product_id)
#         return self.request_utility.get(f"{self.ENDPOINT}/{product_id}", expected_status_code=expected_status_code)
#
#     def call_delete_product(self, product_id: int, params: Optional[Dict[str, Any]] = None,
#                             expected_status_code: int = 200) -> Dict[str, Any]:
#         logger.debug("🟢 Calling 'Delete Product' for id=%s", product_id)
#         return self.request_utility.delete(f"{self.ENDPOINT}/{product_id}", params=params or {"force": True},
#                                            expected_status_code=expected_status_code)
#
#     def call_create_product(self, payload: Dict[str, Any], expected_status_code: int = 201) -> Dict[str, Any]:
#         logger.debug("🟢 Calling 'Create Product' with payload keys: %s", list(payload.keys()))
#         try:
#             resp = self.request_utility.post(self.ENDPOINT, payload=payload, expected_status_code=expected_status_code)
#             logger.info("✅ Product created successfully")
#             return resp
#         except APIRequestException as e:
#             logger.warning("⚠️ Product creation failed: %s", e)
#             resp = getattr(e, "response", None)
#             if resp is not None:
#                 try:
#                     return resp.json()
#                 except Exception as parse_err:
#                     logger.error("🚫 Failed to parse error response JSON from product creation: %s", parse_err)
#                     raise
#             raise
#
#     def call_update_product(self, payload: Dict[str, Any], product_id: int, expected_status_code: int = 200) -> Dict[str, Any]:
#         logger.debug("🟢 Calling 'Update Product' for id=%s", product_id)
#         return self.request_utility.put(f"{self.ENDPOINT}/{product_id}", payload=payload,
#                                         expected_status_code=expected_status_code)
#
#     # ------------------------
#     # Utilities
#     # ------------------------
#     @staticmethod
#     def generate_sale_price(regular_price: float, min_discount: float = 5.0, max_discount: float = 50.0) -> Tuple[str, float]:
#         """
#         Generates a valid sale price that is less than the regular price.
#
#         Returns:
#             Tuple[sale_price_str, discount_percentage]
#         """
#         discount_percentage = random.uniform(min_discount, max_discount)
#         discount_amount = regular_price * (discount_percentage / 100.0)
#         sale_price_value = regular_price - discount_amount
#         return str(round(sale_price_value, 2)), discount_percentage
#
#     # ------------------------
#     # Listing / Pagination
#     # ------------------------
#     def call_list_products(
#         self,
#         params: Optional[Dict[str, Any]] = None,
#         max_pages: int = 1000,
#         created_before: Optional[str] = None,
#         created_after: Optional[str] = None,
#         status: Optional[str] = None,
#         sku: Optional[str] = None,
#         category: Optional[Any] = None,
#         limit: Optional[int] = None,
#     ) -> List[Dict[str, Any]]:
#         """
#         Fetch products with optional filters and pagination. Returns a flat list.
#
#         Notes:
#         - Uses the injected RequestUtility client and requests with expected_status_code=200.
#         - If `limit` is provided, short-circuits once that many items are collected.
#         """
#         VALID_STATUSES = {'draft', 'pending', 'private', 'publish', 'future', 'trash', 'any'}
#         all_products: List[Dict[str, Any]] = []
#
#         params = copy.deepcopy(params) if params else {}
#         params.setdefault('per_page', 100)
#
#         if status:
#             if status not in VALID_STATUSES:
#                 raise ValueError(f"❌ Invalid status '{status}'. Must be one of: {', '.join(sorted(VALID_STATUSES))}")
#             params['status'] = status
#
#         if sku:
#             params['sku'] = sku
#
#         if category:
#             params['category'] = category
#
#         if created_after:
#             params['after'] = created_after
#
#         if created_before:
#             params['before'] = created_before
#
#         for page in range(1, max_pages + 1):
#             logger.debug("📦 Fetching products page: %d", page)
#             params['page'] = page
#             try:
#                 response = self.request_utility.get(self.ENDPOINT, params=params, expected_status_code=200)
#             except Exception as e:
#                 logger.warning("⚠️ Error fetching page %d: %s", page, e)
#                 break
#
#             if not response:
#                 break
#
#             if not isinstance(response, list):
#                 logger.error("Unexpected products list response type: %s", type(response))
#                 raise AssertionError("Products list endpoint did not return a list")
#
#             all_products.extend(response)
#
#             if sku and all_products:
#                 # If filtering by SKU and found, stop early
#                 break
#
#             if limit and len(all_products) >= limit:
#                 logger.debug("🔚 Reached product limit (%s).", limit)
#                 return all_products[:limit]
#         else:
#             raise Exception(f"❌ Reached {max_pages} pages without exhausting results. Potential infinite dataset?")
#
#         return all_products
#
#     # ------------------------
#     # Example DB-backed helper
#     # ------------------------
#     def verify_product_exists_in_db(self, sku: str) -> None:
#         """
#         Example: verify a product exists in the DB by SKU via ProductsDao.
#         """
#         try:
#             row = self.dao.get_product_by_sku(sku)
#         except Exception as e:
#             logger.error("🚨 Failed to query DB for product SKU=%s: %s", sku, e)
#             raise
#
#         if not row:
#             raise AssertionError(f"❌ No DB record found for product SKU={sku}")
#
