# from __future__ import annotations
#
# import os
# import json
# import copy
# import logging
# from datetime import datetime
# from typing import Any, Dict, List
#
# from EcommerceAPI.src.clients.api_client import APIClient  # Importing the RequestUtility class does not
# # instantiate anything — it only gives the helper the type, so it can optionally create one if none is supplied.
# from EcommerceAPI.src.utilities.exceptions import APIRequestException
# from EcommerceAPI.src.orders.dao.orders_dao import OrdersDao
#
# logger = logging.getLogger(__name__)
#
#
# # logger.setLevel(logging.DEBUG)  # Controlled globally via pytest.ini / logging config
#
# """
# OrdersHelper — wrapper/helper for working with WooCommerce orders using RequestUtility.
#
# Important notes for integration:
# - RequestUtility must be configured to target the WooCommerce host/path for "woo" calls.
#   Two common options:
#     1) Set woo_client.base_url to include the Woo prefix (e.g. "https://example.com/wp-json/wc/v3/")
#        and call endpoints like "orders".
#     2) Set woo_client.base_url to the site root and call endpoints with full path "wp-json/wc/v3/orders".
#   Decide which mapping WOO_API_HOSTS[ENV] in your config uses and configure the test fixture accordingly.
#
# """
#
#
# class OrdersHelper(object):
#     """
#     Helper class that encapsulates order-related API interactions and validations.
#
#     Usage:
#       helper = OrdersHelper(request_utility=some_request_util)
#       helper.create_order(additional_args={...})
#       helper.call_list_all_orders(...)
#       helper.verify_order_is_created(...)
#
#     Notes:
#     - The helper returns parsed JSON from RequestUtility on success.
#     - For negative tests that need the raw requests.Response object, call RequestUtility directly with return_raw=True.
#     """
#     ENDPOINT = "orders"
#
#     def __init__(self, request_utility: APIClient):
#         """
#         Require an injected RequestUtility for consistent configuration and testability.
#
#         Best-practice: do NOT instantiate RequestUtility() here. Always pass the session-scoped `request_utility`
#         fixture from conftest (discover_entities should inject it).
#
#         Info:
#             - from EcommerceAPI.src.utilities.requestsUtility import RequestUtility only brings the class
#             (type/constructor) into the module. It does NOT create a client instance.
#             - The session-scoped request_utility fixture in conftest actually creates the single shared RequestUtility
#             instance.
#             - discover_entities (or whatever code builds your helpers) receives that fixture instance and passes it
#             into OrdersHelper(request_utility=...) when it constructs the helper.
#             - Inside OrdersHelper you store that instance on self.request_utility and call it for API requests. So the
#             helper uses the fixture-created, shared client.
#         Why do both exist?
#             - Importing RequestUtility lets the helper use the type (and, if needed, construct a client as a fallback).
#             - Requiring an injected instance (best practice) ensures the helper uses the one, configured client
#             supplied by the fixture instead of creating its own (avoids duplicate config, different headers,
#             broken monkeypatching, etc.).
#         """
#
#         if request_utility is None:
#             raise ValueError(
#                 "OrdersHelper requires a RequestUtility instance. "
#                 "Pass `request_utility` from your conftest (session-scoped fixture)."
#             )
#         # optional: confirm type for clearer error messages during development
#         if not isinstance(request_utility, APIClient):
#             raise TypeError("request_utility must be an instance of RequestUtility")
#
#         self.cur_file_dir = os.path.dirname(os.path.realpath(__file__))
#         # Use the injected client for all requests
#         self.request_utility = request_utility
#
#     def create_order(self, additional_args: Dict[str, Any] = None,
#                      expected_status_code: int = 201) -> Dict[str, Any]:
#         """
#         Create an order using a JSON payload template stored under src/data/create_order_payload.json.
#         """
#         logger.debug("🟢 Calling 'Create Order' (OrdersHelper).")
#
#         payload_template_path = os.path.abspath(os.path.join(self.cur_file_dir, '..', 'data',
#                                                              'create_order_payload.json'))
#         if not os.path.isfile(payload_template_path):
#             raise FileNotFoundError(f"🚫 Payload file not found: {payload_template_path}")
#
#         try:
#             with open(payload_template_path, 'r', encoding='utf-8') as f:
#                 payload = json.load(f)
#             logger.debug("📦 Loaded payload template from: %s", payload_template_path)
#         except json.JSONDecodeError as e:
#             raise ValueError(f"❌ Invalid JSON in payload template: {e}")
#         except Exception as e:
#             raise RuntimeError(f"❌ Failed to load order payload template: {e}")
#
#         if additional_args:
#             if not isinstance(additional_args, dict):
#                 raise TypeError(f"❗ 'additional_args' must be a dict, got {type(additional_args)}")
#             logger.debug("🧩 Updating payload with additional args: %s", additional_args)
#             payload.update(additional_args)
#
#         try:
#             rs_api = self.request_utility.post(self.ENDPOINT, payload=payload,
#                                                expected_status_code=expected_status_code)
#             logger.info("✅ Order successfully created.")
#             return rs_api
#         except APIRequestException as e:
#             # We import APIRequestException from the centralized exceptions module.
#             logger.warning("⚠️ Order creation failed: %s. Attempting to extract response JSON...", e)
#             resp = getattr(e, "response", None)
#             if resp is not None:
#                 try:
#                     return resp.json()
#                 except Exception as parse_error:
#                     logger.error("🚫 Failed to parse error response JSON: %s", parse_error)
#                     raise
#             raise
#
#     def call_update_an_order(self, order_id: int, payload: Dict[str, Any],
#                              expected_status_code: int = 200) -> Dict[str, Any]:
#         logger.debug("🟢 Calling 'Update Order' for order_id=%s", order_id)
#         return self.request_utility.put(f"{self.ENDPOINT}/{order_id}", payload=payload,
#                                         expected_status_code=expected_status_code)
#
#     def call_retrieve_an_order(self, order_id: int, expected_status_code: int = 200) -> Dict[str, Any]:
#         logger.debug("🟢 Calling 'Retrieve Order' for order_id=%s", order_id)
#         return self.request_utility.get(f"{self.ENDPOINT}/{order_id}", expected_status_code=expected_status_code)
#
#     def call_delete_an_order(self, order_id: int, params: Dict[str, Any] = None,
#                              expected_status_code: int = 200) -> Dict[str, Any]:
#         logger.debug("🟢 Calling 'Delete Order' for order_id=%s", order_id)
#         return self.request_utility.delete(f"{self.ENDPOINT}/{order_id}", params=params or {"force": True},
#                                            expected_status_code=expected_status_code)
#
#     def call_list_all_orders(
#             self,
#             params: Dict[str, Any] = None,
#             max_pages: int = 1000,
#             created_before: str = None,
#             created_after: str = None,
#             status: str = None
#     ) -> List[Dict[str, Any]]:
#         VALID_STATUSES = {
#             'pending', 'processing', 'on-hold', 'completed',
#             'cancelled', 'refunded', 'failed', 'trash', 'any'
#         }
#
#         all_orders: List[Dict[str, Any]] = []
#         params = copy.deepcopy(params) if params else {}
#         params.setdefault("per_page", 100)
#
#         if status:
#             if status not in VALID_STATUSES:
#                 raise ValueError(f"❌ Invalid status '{status}'. Must be one of: {', '.join(VALID_STATUSES)}")
#             params['status'] = status
#
#         cutoff_before = None
#         cutoff_after = None
#         if created_before:
#             try:
#                 cutoff_before = datetime.fromisoformat(created_before)
#             except ValueError:
#                 logger.warning("⚠️ Invalid 'created_before' format: %s", created_before)
#         if created_after:
#             try:
#                 cutoff_after = datetime.fromisoformat(created_after)
#             except ValueError:
#                 logger.warning("⚠️ Invalid 'created_after' format: %s", created_after)
#
#         for page in range(1, max_pages + 1):
#             logger.debug("📦 Fetching orders page number: %d", page)
#             params['page'] = page
#             try:
#                 response = self.request_utility.get(self.ENDPOINT, params=params, expected_status_code=200)
#             except Exception as e:
#                 logger.warning("⚠️ Error fetching orders page %d: %s", page, e)
#                 break
#
#             if not response:
#                 break
#
#             for order in response:
#                 created_gmt = order.get('date_created_gmt')
#                 try:
#                     created_date = datetime.fromisoformat(created_gmt.replace('Z', '+00:00')) if created_gmt else None
#                     if created_date:
#                         if cutoff_before and created_date >= cutoff_before:
#                             continue
#                         if cutoff_after and created_date <= cutoff_after:
#                             continue
#                     all_orders.append(order)
#                 except Exception as e:
#                     logger.warning("⚠️ Could not parse 'date_created_gmt' for order %s: %s", order.get('id'), e)
#                     continue
#         else:
#             # If loop finishes naturally without break, we've hit max_pages without exhaustion
#             raise Exception(
#                 f"❌ Reached max_pages ({max_pages}) without exhausting results. Potential infinite dataset?")
#
#         return all_orders
#
#     @staticmethod
#     def verify_order_is_created(order_json: Dict[str, Any], expect_cust_id: int,
#                                 exp_products: List[Dict[str, Any]]) -> None:
#         """
#         Validate that the created order matches expectations and that related DB records exist.
#         """
#         orders_dao = OrdersDao()
#
#         assert order_json, "❌ Create order response is empty."
#         assert 'customer_id' in order_json, "❌ 'customer_id' missing from response."
#         assert order_json['customer_id'] == expect_cust_id, (f"❌ Expected customer_id {expect_cust_id}, "
#                                                              f"got {order_json['customer_id']}")
#         assert 'line_items' in order_json, "❌ 'line_items' missing from order response."
#         assert len(order_json['line_items']) == len(exp_products), (f"❌ Expected {len(exp_products)} line item(s), but "
#                                                                     f"got {len(order_json['line_items'])}.")
#         assert order_json.get('order_key'), "❌ 'order_key' is empty!"
#
#         order_id = order_json['id']
#
#         try:
#             line_info = orders_dao.get_order_lines_by_order_id(order_id)
#         except Exception as e:
#             logger.error("🚨 Failed to retrieve order lines from DB for Order ID: %s. Error: %s", order_id, e)
#             raise
#
#         assert line_info, f"❌ No line item found in DB for Order ID: {order_id}"
#         try:
#             assert line_info[0]['order_item_id'] == order_json['line_items'][0]['id'], ("❌ Order item ID mismatch "
#                                                                                         "between API and DB")
#         except (KeyError, IndexError) as e:
#             logger.error("🚨 Error comparing order item IDs: %s", e)
#             raise
#
#         api_product_ids = [i.get('product_id') for i in order_json['line_items']]
#         for expected in exp_products:
#             pid = expected.get('product_id')
#             assert pid in api_product_ids, f"❌ Product ID {pid} missing in API response."
#
#             matched_item = next((item for item in order_json['line_items'] if item.get('product_id') == pid), None)
#             assert matched_item, f"❌ No matching product found for ID {pid} in response."
#
#             for key, val in expected.items():
#                 if key in matched_item:
#                     assert matched_item[key] == val, (
#                         f"❌ Mismatch for product_id {expected['product_id']} - Expected {key}: {val}, "
#                         f"got: {matched_item[key]}"
#                     )
#                 else:
#                     logger.warning("⚠️ Key '%s' missing in API response for product_id %s. Skipping validation.",
#                                    key, pid)
#
