# import pytest
# from EcommerceAPI.src.helpers.products_helper import ProductsHelper
#
#
# @pytest.fixture(scope='module')
# def products_helper():
#     return ProductsHelper()
#
#
# @pytest.fixture
# def created_product(products_helper):
#     payload = {
#         "name": "Valid Product for Update Test",
#         "type": "simple",
#         "regular_price": "10.00"
#     }
#     product = products_helper.call_create_product(payload)
#     yield product
#     products_helper.call_delete_product(product['id'])
#
#
# @pytest.mark.parametrize("payload, expected_status_code, expect_error", [
#     ({"name": ""}, 201, False),  # empty name might be accepted
#     ({"type": "invalid_type"}, 400, True),
#     ({"regular_price": 123}, 400, True),
#     ({}, 201, False),  # empty payload might default
#     # The API currently accepts unknown fields and returns 201, so expect no error here
#     ({"name": "Extra Field", "invalid_field": "xyz"}, 201, False),
# ])
# def test_create_product_negative_variations(products_helper, payload, expected_status_code, expect_error):
#     response = products_helper.call_create_product(payload, expected_status_code=expected_status_code)
#
#     assert isinstance(response, dict), "Response should be a dict"
#     if expect_error:
#         assert "code" in response, "Expected error code in response"
#         assert response.get('code') in ['rest_invalid_param', 'woocommerce_rest_product_invalid_id'], \
#             f"Unexpected error code: {response.get('code')}"
#     else:
#         assert "id" in response, "Product creation should succeed"
#
#
# @pytest.mark.parametrize("product_id, expected_status_code, expected_error_code", [
#     (9999999999, 404, "woocommerce_rest_product_invalid_id"),
#     ("invalid-string", 404, "rest_no_route"),
#     (None, 404, "rest_no_route"),
# ])
# def test_get_product_negative_scenarios(products_helper, product_id, expected_status_code, expected_error_code):
#     response = products_helper.call_retrieve_product(product_id, expected_status_code=expected_status_code)
#
#     assert isinstance(response, dict), "Response should be a dict"
#     # If you have the status_code accessible from the response or helper, check here
#     # For example, if response is a requests.Response object: response.status_code == expected_status_code
#     # If not, rely on expected_status_code passed and exception handling in helper
#
#     assert "code" in response, "Response should contain an error code"
#     assert response["code"] == expected_error_code, f"Expected error code '{expected_error_code}'"
#
#
# @pytest.mark.parametrize("payload, expected_status_code", [
#     ({"name": ""}, 200),  # API accepts empty name and returns 200
#     ({}, 200),  # Empty payload returns 200 and unchanged product
#     ({"invalid_field": "abc"}, 200),  # Unknown field ignored, 200 OK returned
# ])
# def test_update_product_negative_variations(products_helper, created_product, payload, expected_status_code):
#     product_id = created_product["id"]
#     response = products_helper.call_update_product(payload, product_id, expected_status_code=expected_status_code)
#
#     assert isinstance(response, dict), "Response should be a dict"
#     if expected_status_code == 400:
#         assert "code" in response, "Expected error code in response"
#     else:
#         assert "id" in response, "Response should contain product id"
