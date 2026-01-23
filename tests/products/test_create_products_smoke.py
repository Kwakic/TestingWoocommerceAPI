# import pytest
#
# from EcommerceAPI.src.utilities.genericUtilities import generate_random_string
# from EcommerceAPI.src.helpers.products_helper import ProductsHelper
# from EcommerceAPI.src.dao.products_dao import ProductsDAO
#
# pytestmark = [pytest.mark.products, pytest.mark.smoke]
#
#
# @pytest.mark.tcid26
# def test_create_1_simple_product(shared_api_resources):
#     # 1. Generate data to create a product (payload)
#     name = generate_random_string(10, prefix="Test") # # For the name, we don't want to hardcode the
#     # string because we will run the automation many times and we don't want to have products with the same name.
#     # We could do it in SETUP and tear-down and delete_it.py it instead, we auto generate the name.
#     payload = {
#         "name": name,
#         "type": "simple",
#         "regular_price": "10.95"
#     }
#
#     # 2. Make the call (we have to create within our 'products_helper' a function to create a product)
#     product_rs = ProductsHelper().call_create_product(payload)  # We don't need to create an object and assign it to a
#     # variable because we will need it only once. If we needed the object "ProductHelper()" multiple times then I would
#     # have to create it every time. If we have multiple test cases, that need this helper that you can create the object
#     # within the SETUP step and use it.
#     # import pdb; pdb.set_trace()
#     shared_api_resources['created_products'].append(product_rs['id'])
#
#     # 3. Verify the response is not empty
#     assert product_rs, f"Create product API response is empty. Payload: {payload}"
#     assert product_rs['name'] == payload['name'], (f"Create product API call response has unexpected name. Expected "
#                                                    f"is {payload['name']}, Actual: {product_rs['name']}.")
#     # Apart from that, we verified that status code is 201 (we specified it in the helper class)
#
#     # 4. Verify the product exists in DB (We need to get a product from DB and make sure it exists.)
#     # The information from the DB (calling our SQL) is a list of dictionary, so we NEED TO PROVIDE INDEXING, e.g.,
#     # from the first index [0]
#     # We create a variable of the ID  from the response. And we make an instance of the class to make the call to DB.
#     product_id = product_rs['id']
#     db_product = ProductsDAO().get_product_by_id(product_id)
#     # Now we verify that the information from the DB matches with the information from the API call.
#     assert payload['name'] == db_product[0]['post_title'], (f"Create product, title in DB does not match title in API. "
#                                                             f"DB: {db_product['post_title']}, API: {payload['name']}")
#
#
# #   What we did in our test the following:
# # •	we created a product
# # •	generated random a name for the product
# # •	we set the type and price
# # •	we made API call
# # •	we verified that status code is 201 (we specified it in the helper class)
# # •	we made sure the response is not empty (we checked that there are some data in the response)
# # •	we made sure that name in the response matches the name in the request
# # •	we got the ID from the response, went to DB, got the product and compared the name of the product with the DB
# # (called ‘post_title’) is the same as the one in the request.
#
#
# @pytest.mark.tcid27
# def test_create_product_with_invalid_type_returns_400():
#     payload = {
#         "name": "Invalid Type",
#         "type": "nonsense",  # 🚫 Invalid type. Valid are: simple, grouped, external, and variable. Default is simple.
#         "regular_price": "10.00"
#     }
#
#     products_helper = ProductsHelper()
#     # Expecting WooCommerce or backend to return HTTP 400 (Bad Request)
#     rs = products_helper.call_create_product(payload=payload, expected_status_code=400)
#
#     # Assert main-level error info
#     assert rs['code'] == 'rest_invalid_param', f"Unexpected error code: {rs.get('code')}"
#     assert 'type' in rs['message'].lower(), f"Expected 'type' in error message. Got: {rs.get('message')}"
#
#     # Assert specific field validation detail
#     assert 'type' in rs['data']['params'], "Expected 'type' to be in 'params'"
#     assert "not one of simple" in rs['data']['params']['type'], f"Unexpected param error message: {rs['data']['params']['type']}"
#
#     # Optional: check deep error structure if needed
#     details = rs['data'].get('details', {})
#     assert details.get('type', {}).get('code') == 'rest_not_in_enum', \
#         f"Expected 'rest_not_in_enum' for type field. Got: {details.get('type')}"
