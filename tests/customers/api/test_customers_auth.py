# import os
# import pytest
# import logging
# from requests_oauthlib import OAuth1
#
# from tests.shared.schemas.customer import error_schema
# from EcommerceAPI.src.utilities.credentialsUtility import get_wc_api_keys
#
# logger = logging.getLogger(__name__)
#
# # 🔖 Apply markers at module level for test discovery/grouping
# pytestmark = [pytest.mark.customers, pytest.mark.negative, pytest.mark.security]
#
# # 🧮 Test Matrix — Defines test dimensions: method, endpoint, etc.
# TEST_MATRIX = [
#     # method, endpoint, resource_type, needs_id, needs_payload
#     ("get", "customers", "customer", False, False),
#     ("post", "customers", "customer", False, True),
#     ("put", "customers", "customer", True, True),
#     ("delete_it.py", "customers", "customer", True, False),
# ]
#
#
# # NOT WORKING DUE TO removal expected status code and not updated
# def get_invalid_auth_test_data():
#     """
#     🚫 Returns invalid OAuth credentials for negative testing.
#     Each tuple: (consumer_key, consumer_secret, expected_error_message)
#     """
#     creds = get_wc_api_keys()
#     return [
#         ("ck_invalid_key_123", "cs_fake_secret_xyz", "Consumer key is invalid."),
#         ("ck_invalid_key_123", creds["wc_secret"], "Consumer key is invalid."),
#         (creds["wc_key"], "cs_invalid_secret_456", "Invalid signature - provided signature does not match."),
#     ]
#
#
# # ⚙️ Parametrize the test matrix
# @pytest.mark.parametrize(
#     "invalid_key, invalid_secret, expected_message",
#     get_invalid_auth_test_data(),
#     ids=["invalid_key+secret", "invalid_key_valid_secret", "valid_key_invalid_secret"]
# )
# @pytest.mark.parametrize(
#     "http_method, endpoint, resource_type, needs_id, needs_payload",
#     TEST_MATRIX,
#     ids=["GET customers", "POST customers", "PUT customers/{id}", "DELETE customers/{id}"]
# )
# @pytest.mark.negative_test
# @pytest.mark.tcid20
# def test_negative_auth_customers_only(
#         all_resources,
#         shared_api_resources,
#         http_method,
#         endpoint,
#         resource_type,
#         needs_id,
#         needs_payload,
#         invalid_key,
#         invalid_secret,
#         expected_message
# ):
#     """
#     🔐 Negative Authentication Matrix Test
#
#     Verifies all customer-related endpoints properly reject invalid credentials (401 Unauthorized).
#
#     - Does NOT create any real resources.
#     - Uses fake customer ID when needed (e.g., PUT/DELETE).
#     - Ensures invalid keys/secrets prevent access regardless of input.
#     """
#     # ⚠️ Skip risky methods if running in production. (NOT REAL it needs to be implemented)
#     if os.getenv("ENV") == "prod" and http_method in ["post", "put", "delete_it.py"]:
#         pytest.skip("Skipping potentially destructive test in production")
#
#     # 🔐 Set up the test client with invalid OAuth credentials
#     request_util = all_resources.request
#     request_util.auth = OAuth1(invalid_key, invalid_secret)
#
#     # 🧪 If endpoint requires ID, inject a fake ID instead of creating a real customer
#     if needs_id:
#         fake_id = 999999  # Arbitrary ID that doesn't exist — we’re testing auth, not existence
#         endpoint = f"{endpoint}/{fake_id}"
#         logger.debug(f"Injected fake ID into endpoint: {endpoint}")
#
#     # ⚙️ Prepare request arguments
#     kwargs = {
#         "endpoint": endpoint,
#         "expected_status_code": 401,
#         "schema": error_schema
#     }
#
#     # Add empty payload if needed (e.g., for POST/PUT)
#     if needs_payload:
#         kwargs["payload"] = {}
#         logger.debug(f"Added empty payload for {http_method.upper()} request.")
#
#     # Add empty query params for GET/DELETE
#     if http_method in ["get", "delete_it.py"]:
#         kwargs["params"] = {}
#         logger.debug(f"Added empty query params for {http_method.upper()} request.")
#
#     # 🚀 Execute the request dynamically based on method (e.g., get/post/put/delete_it.py)
#     method_func = getattr(request_util, http_method)
#     response = method_func(**kwargs)
#
#     # 📋 Log test scenario
#     logger.info(f"{http_method.upper()} {endpoint} → with invalid key: {invalid_key}")
#
#     # ✅ Assert response matches expected auth error structure
#     assert isinstance(response, dict), "Expected response to be a dictionary"
#     assert response.get("code") == "woocommerce_rest_authentication_error", f"Unexpected error code: {response}"
#     assert response.get("message") == expected_message, f"Unexpected error message: {response}"
#     assert response.get("data", {}).get("status") == 401, f"Expected status 401, got: {response}"
#
#     logger.info(f"✅ Properly rejected request to {http_method.upper()} {endpoint} with invalid credentials.")
#
# # 📊 Negative Auth Test Coverage Matrix:
# # | Method | Endpoint       | Resource | Needs ID | Needs Payload | Auth Variants |
# # |--------|----------------|----------|----------|----------------|----------------|
# # | GET    | customers      | customer | ❌        | ❌              | 3              |
# # | POST   | customers      | customer | ❌        | ✅              | 3              |
# # | PUT    | customers/{id} | customer | ✅        | ✅              | 3              |
# # | DELETE | customers/{id} | customer | ✅        | ❌              | 3              |
#
#
# # ✅ Summary:
# #    - Total combinations: 16
# #    - Invalid auth variants per combo: 3
# #    - Total test cases run: 4 × 3 = 12
