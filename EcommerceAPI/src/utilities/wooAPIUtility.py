# import os
# import time
# import json
# import logging
# from logging.handlers import RotatingFileHandler
# from woocommerce import API
# from jsonschema import validate, ValidationError
# from EcommerceAPI.configs.hosts_config import WOO_API_HOSTS
# from EcommerceAPI.src.utilities.credentialsUtility import get_db_credentials, get_wc_api_keys
#
# log = logging.getLogger("wooLogger")
# log.setLevel(logging.DEBUG)
# # logger.propagate = False # Already configured in "custom_logger.py" utility" It keeps your file-specific logger
# # independent, so messages don’t also go to the root logger
#
# # if not log.hasHandlers():
# #     formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
# #     fh = RotatingFileHandler("test_debug.log", maxBytes=5_000_000, backupCount=3)
# #     fh.setLevel(logging.DEBUG)
# #     fh.setFormatter(formatter)
# #     ch = logging.StreamHandler()
# #     ch.setLevel(logging.INFO)
# #     ch.setFormatter(formatter)
# #     log.addHandler(fh)
# #     log.addHandler(ch)
#
# # BaseAPIUtility
# # ├── RequestUtility: (uses requests.Session + OAuth1). The RequestUtility is actually the foundation your helpers
# # and DAO-level tests rely on for all CRUD operations (customers, products, etc.).
# # └── WooAPIUtility: uses WooCommerce API lib. Is used for WooCommerce endpoints directly via woocommerce Python client
#
#
# class WooAPIUtility(object):
#     """
#     Utility for interacting with the WooCommerce API using the official SDK.
#     - Supports GET, POST, PUT, DELETE.
#     - Handles retry with exponential backoff for transient errors.
#     - Validates response status code and optional JSON schema.
#     - Detailed logging for request/response, especially on errors.
#     - Optionally returns the raw response object for advanced/negative test use.
#
#     Methods match the interface of RequestUtility to allow interchangeable use in helpers/test clients.
#     """
#
#     def __init__(self):
#         wc_creds = get_wc_api_keys()
#         self.env = os.environ.get('ENV', 'test')
#         self.base_url = WOO_API_HOSTS[self.env]
#         self.wcapi = API(
#             url=self.base_url,
#             consumer_key=wc_creds['wc_key'],
#             consumer_secret=wc_creds['wc_secret'],
#             version="wc/v3",
#             timeout=20
#         )
#         self.status_code = None
#         self.expected_status_code = None
#         self.endpoint = None
#         self.rs_json = None
#
#     def _request_with_backoff(self, method, endpoint, params=None):
#         """
#         Handles retries with exponential backoff for transient errors.
#         Retries 3 times on failure, waiting: 1s, 2s, 4s.
#         """
#         retries = 3
#         delay = 1
#         for attempt in range(retries):
#             try:
#                 if method == 'get':
#                     return self.wcapi.get(endpoint, params=params)
#                 elif method == 'post':
#                     return self.wcapi.post(endpoint, data=params)
#                 elif method == 'put':
#                     return self.wcapi.put(endpoint, data=params)
#                 elif method == 'delete_it.py':
#                     return self.wcapi.delete_it.py(endpoint, params=params)
#             except Exception as e:
#                 log.warning(f"Attempt {attempt + 1} failed for {method.upper()} {endpoint}: {e}")
#                 time.sleep(delay)
#                 delay *= 2
#         raise RuntimeError(f"❌ {method.upper()} {endpoint} failed after {retries} retries")
#
#     def _handle_response(self, response, endpoint, expected_status_code, schema=None, return_raw=False):
#         """
#         Parse, validate, and log the HTTP response.
#         If return_raw is True, return the raw response object.
#         """
#         self.status_code = response.status_code
#         self.expected_status_code = expected_status_code
#         self.endpoint = endpoint
#
#         try:
#             self.rs_json = response.json()
#         except ValueError:
#             self.rs_json = response.text
#
#         # Log response on error
#         if self.status_code >= 400:
#             if isinstance(self.rs_json, (dict, list)):
#                 log.debug(json.dumps(self.rs_json, indent=2))
#             else:
#                 log.debug(str(self.rs_json))
#
#         # Always log HTTP info
#         log.debug(f"📡 {response.request.method} {self.endpoint} → {self.status_code}")
#
#         # Assert status code, or raise
#         if self.status_code != self.expected_status_code:
#             log.error(f"Bad Status Code. Expected {self.expected_status_code}, Actual: {self.status_code}, "
#                       f"URL: {self.endpoint}, Response: {self.rs_json}")
#             raise AssertionError(
#                 f"Bad Status Code. Expected {self.expected_status_code}, "
#                 f"Actual: {self.status_code}, URL: {self.endpoint}, Response: {self.rs_json}"
#             )
#
#         # Optional: Validate JSON schema
#         if schema:
#             if not isinstance(schema, dict):
#                 raise TypeError(f"Schema must be a dictionary, got {type(schema)}")
#             try:
#                 validate(instance=self.rs_json, schema=schema)
#             except ValidationError as e:
#                 raise AssertionError(f"Response schema validation failed: {e.message}")
#
#         # If advanced debugging: return the raw response object
#         if return_raw:
#             return response
#
#         # Return parsed JSON or text
#         return self.rs_json
#
#     def _request(self, method, endpoint, expected_status_code=200, params=None, payload=None, schema=None,
#                  return_raw=False):
#         """
#         Internal helper to orchestrate request and response handling.
#         Arguments:
#             method (str): 'get', 'post', 'put', 'delete_it.py'
#             endpoint (str): API endpoint path
#             expected_status_code (int): Expected HTTP response code
#             params (dict): Query parameters for GET/DELETE; body data for POST/PUT
#             payload (dict): Alias for params (for compatibility)
#             schema (dict): Optional JSON schema for validation
#             return_raw (bool): If True, return requests.Response
#         Returns:
#             dict/str/requests.Response
#         """
#         # Support both 'params' and 'payload' for compatibility with RequestUtility interface
#         actual_params = payload if payload is not None else params
#         start = time.perf_counter()
#         response = self._request_with_backoff(method, endpoint, actual_params)
#         duration = time.perf_counter() - start
#         result = self._handle_response(response, endpoint, expected_status_code, schema, return_raw=return_raw)
#         log.debug(f"✅ {method.upper()} {endpoint} → Status {self.status_code} ({duration:.2f}s)")
#         return result
#
#     # Public API: method signatures match RequestUtility for drop-in compatibility
#     def get(self, endpoint, params=None, expected_status_code=200, schema=None, return_raw=False):
#         """
#         GET request. Returns parsed response or raw response if return_raw=True.
#         """
#         return self._request("get", endpoint, expected_status_code, params=params, schema=schema,
#                              return_raw=return_raw)
#
#     def post(self, endpoint, payload=None, expected_status_code=201, schema=None, return_raw=False):
#         """
#         POST request. Returns parsed response or raw response if return_raw=True.
#         """
#         return self._request("post", endpoint, expected_status_code, payload=payload, schema=schema,
#                              return_raw=return_raw)
#
#     def put(self, endpoint, payload=None, expected_status_code=200, schema=None, return_raw=False):
#         """
#         PUT request. Returns parsed response or raw response if return_raw=True.
#         """
#         return self._request("put", endpoint, expected_status_code, payload=payload, schema=schema,
#                              return_raw=return_raw)
#
#     def delete_it.py(self, endpoint, params=None, expected_status_code=200, schema=None, return_raw=False):
#         """
#         DELETE request. Returns parsed response or raw response if return_raw=True.
#         """
#         if params is None:
#             params = {"force": True}
#         return self._request("delete_it.py", endpoint, expected_status_code, params=params, schema=schema,
#                              return_raw=return_raw)
#
#
# # 🔍 Manual test run
# if __name__ == '__main__':
#     api = WooAPIUtility()
#     response = api.get("products", schema={"type": "array"})
#     print(json.dumps(response, indent=2))
#
