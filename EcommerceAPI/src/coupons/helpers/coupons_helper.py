# """
# CouponsHelper — wrapper/helper for working with WooCommerce coupons using RequestUtility.
#
# Changes / Rationale:
# - Require injection of the shared RequestUtility instance (best-practice).
# - Import APIRequestException from centralized exceptions module.
# - Gracefully handle missing `error_schema` at import time so tests don't crash during collection.
# - Keep helper methods thin and rely on the injected client for all HTTP operations.
#
# """
# from __future__ import annotations
#
# import logging
# from typing import Optional, Dict, Any, List
# from jsonschema import validate
# from jsonschema.exceptions import ValidationError
#
# from EcommerceAPI.src.clients.api_client import APIClient
# from EcommerceAPI.src.utils.exceptions import APIRequestException
# from EcommerceAPI.src.coupons.dao.coupons_dao import CouponsDAO
# from tests.coupons.models.coupon import coupon_schema, error_schema
#
# logger = logging.getLogger(__name__)
#
#
# class CouponsHelper:
#     """
#     Helper for coupon-related API interactions.
#
#     Usage:
#         helper = CouponsHelper(request_utility=request_utility)
#         helper.create_coupon({...})
#         helper.list_coupons()
#         helper.validate_coupon_response_schema(coupon)
#     """
#
#     ENDPOINT = "coupons"
#
#     def __init__(self, request_utility: APIClient):
#         """
#         Require a RequestUtility instance for consistent configuration and testability.
#
#         Best-practice: do NOT instantiate RequestUtility() here. Always pass the session-scoped
#         `request_utility` fixture from conftest (discover_entities will inject it).
#
#         Raises:
#             ValueError: if request_utility is None
#             TypeError: if request_utility is not an instance of RequestUtility
#         """
#         if request_utility is None:
#             raise ValueError(
#                 "CouponsHelper requires a RequestUtility instance. "
#                 "Pass `request_utility` from your conftest (session-scoped fixture)."
#             )
#         if not isinstance(request_utility, APIClient):
#             raise TypeError("request_utility must be an instance of RequestUtility")
#
#         self.request_utility = request_utility
#         # Optional DAO instance; helpers can create DAO on demand or use it directly
#         self.dao = CouponsDAO()
#
#     # ------------------------
#     # CRUD operations
#     # ------------------------
#     def create_coupon(self, payload: Dict[str, Any], expected_status_code: int = 201) -> Dict[str, Any]:
#         """
#         Create a coupon via POST /coupons and return parsed JSON.
#         """
#         logger.debug("🟢 Creating coupon with payload keys: %s", list(payload.keys()))
#         try:
#             resp = self.request_utility.post(self.ENDPOINT, payload=payload, expected_status_code=expected_status_code)
#             logger.info("✅ Coupon created successfully.")
#             return resp
#         except APIRequestException as e:
#             # Attempt to return error body when API returned a non-2xx
#             logger.warning("⚠️ Coupon creation failed: %s", e)
#             resp = getattr(e, "response", None)
#             if resp is not None:
#                 try:
#                     return resp.json()
#                 except Exception as parse_err:
#                     logger.error("🚫 Failed to parse error response JSON from coupon creation: %s", parse_err)
#                     raise
#             raise
#
#     def get_coupon(self, coupon_id: int, expected_status_code: int = 200) -> Dict[str, Any]:
#         logger.debug("🟢 Retrieving coupon id=%s", coupon_id)
#         return self.request_utility.get(f"{self.ENDPOINT}/{coupon_id}", expected_status_code=expected_status_code)
#
#     def delete_coupon(self, coupon_id: int, expected_status_code: int = 200) -> Dict[str, Any]:
#         logger.debug("🟢 Deleting coupon id=%s", coupon_id)
#         return self.request_utility.delete(f"{self.ENDPOINT}/{coupon_id}", params={"force": True},
#                                            expected_status_code=expected_status_code)
#
#     def list_coupons(self, params: Optional[Dict[str, Any]] = None, per_page: int = 100,
#                      max_pages: int = 1000) -> List[Dict[str, Any]]:
#         """
#         Returns a (possibly paginated) list of coupons. By default this fetches pages until exhaustion or max_pages.
#         """
#         params = params.copy() if params else {}
#         params.setdefault("per_page", per_page)
#
#         all_items: List[Dict[str, Any]] = []
#         for page in range(1, max_pages + 1):
#             logger.debug("📦 Fetching coupons page=%d", page)
#             params["page"] = page
#             try:
#                 response = self.request_utility.get(self.ENDPOINT, params=params, expected_status_code=200)
#             except Exception as e:
#                 logger.warning("⚠️ Error fetching coupons page %d: %s", page, e)
#                 break
#
#             if not response:
#                 break
#
#             if not isinstance(response, list):
#                 logger.error("Unexpected coupons list response type: %s", type(response))
#                 raise AssertionError("Coupons list endpoint did not return a list")
#
#             all_items.extend(response)
#
#             # If fewer than per_page returned, we exhausted results
#             if len(response) < params.get("per_page", per_page):
#                 break
#         else:
#             raise Exception(f"❌ Reached max_pages ({max_pages}) without exhausting results. Potential infinite dataset?")
#
#         return all_items
#
#     # ------------------------
#     # Validation helpers
#     # ------------------------
#     @staticmethod
#     def validate_coupon_response_schema(coupon: Dict[str, Any]) -> None:
#         """
#         Validate a coupon object against coupon_schema. Raises jsonschema.ValidationError on mismatch.
#         """
#         if not isinstance(coupon, dict):
#             raise TypeError(f"Expected coupon to be a dict, got {type(coupon)}")
#         validate(instance=coupon, schema=coupon_schema)
#         logger.info("📦 Coupon response schema validated successfully")
#
#     @staticmethod
#     def validate_coupon_error_response_schema(response: Dict[str, Any]) -> None:
#         """
#         Validate an error response for coupons.
#
#         If an `error_schema` is available in EcommerceAPI.src.models.coupon it will be used for full JSON Schema
#         validation. Otherwise a minimal structural check (presence of 'code' and 'message') is performed.
#         """
#         if not isinstance(response, dict):
#             raise TypeError(f"Expected error response to be a dict, got {type(response)}")
#
#         # Minimal checks
#         if not response.get("code"):
#             raise AssertionError("Missing 'code' in error response")
#         if not response.get("message"):
#             raise AssertionError("Missing 'message' in error response")
#
#         # Optional full schema validation
#         if error_schema is not None:
#             try:
#                 validate(instance=response, schema=error_schema)
#             except ValidationError as ve:
#                 logger.warning("Coupon error schema validation failed: %s", ve)
#                 raise
#
#     # ------------------------
#     # DAO-backed helpers (example)
#     # ------------------------
#     def verify_coupon_exists_in_db(self, code: str) -> None:
#         """
#         Example helper that uses the DAO to assert the coupon exists in the DB.
#         """
#         try:
#             db_row = self.dao.get_coupon_by_code(code)
#         except Exception as e:
#             logger.error("🚨 Failed to query DB for coupon code=%s: %s", code, e)
#             raise
#         if not db_row:
#             raise AssertionError(f"❌ No DB record found for coupon code={code}")
#
