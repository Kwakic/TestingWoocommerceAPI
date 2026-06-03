# from EcommerceAPI.src.dao.products_dao import ProductsDAO
# from EcommerceAPI.src.helpers.woo_orders_helper import OrdersHelper
# from EcommerceAPI.src.helpers.customers_helper import CustomersHelper
# import pytest
# import json
#
#
# # Get a product from DB (We have a helper ‘product.dao’ that will return a random product ID.)
# @pytest.fixture(scope='function')
# def my_orders_smoke_setup(shared_api_resources):  # Inject test_data for cleanup support
#     product_dao = ProductsDAO()
#     rand_product = product_dao.get_random_product_from_db(1)
#     product_id = rand_product[0]['ID']
#
#     order_helper = shared_api_resources['order_helper']
#     customer_helper = shared_api_resources['customer_helper']
#
#     info = {
#         'product_id': product_id,
#         'order_helper': order_helper,
#         'customer_helper': customer_helper,
#         'test_data': shared_api_resources
#     }
#
#     return info
#
#
# @pytest.mark.smoke
# @pytest.mark.orders
# @pytest.mark.tcid48
# def test_create_paid_order_guest_user(my_orders_smoke_setup, shared_api_resources):
#     # create helper objects
#     order_helper = my_orders_smoke_setup['order_helper']  # we created the object in the fixture above
#     # product_dao = ProductsDAO() # we use it in our setup instead
#     customer_id = 0
#     # 1. Get a product from DB (We have a helper ‘product.dao’ that will return a random product ID.)
#     # rand_product = product_dao.get_random_product_from_db(1) # we use it in our setup
#     # product_id = rand_product[0]['ID'] # we use it in our setup instead
#     product_id = my_orders_smoke_setup['product_id']  # we created the object in the fixture above
#     # 2. Make the call (also update payload for order creation)
#     # For the API call we will use woocommerce API, which we created "wooAPIUtility.py"
#     # The call is going to be a POST call, and for that we create order helper because it is repetitive.
#     # We want to use our own product, and we want to overwrite the default called "line_items" array in our template.
#     # We want our 'product_id' to be our 'product_id' variable that we get from our DB.
#     # The 'info' which is our partial payload is copied from our JSON template, and we just added curly brackets since
#     # it must be a dictionary format.
#     order_payload = {
#         "line_items": [
#             {"product_id": product_id, "quantity": 1}
#         ]
#     }
#
#     order_json = order_helper.create_order(additional_args=order_payload)  # Response from POST request (order created)
#     shared_api_resources["created_orders"].append(order_json["id"])  # Added cleanup list
#
#     # with open('order_json_created.json', 'w') as data:
#     #     json.dump(order_json, data)
#     # data.close()
#
#     # 3. Verify response (FYI, we already checked the status code is 201 in our 'wooNOTUSED_orders_helper.py'.)
#     expected_products = [{'product_id': product_id}]  # List of the products with product id. If you want to validate
#     # something else you must add key-value pairs into the list.
#     order_helper.verify_order_is_created(order_json, customer_id, expected_products)
#     # import pdb;pdb.set_trace()
#
#
# @pytest.mark.smoke
# @pytest.mark.orders
# @pytest.mark.tcid49
# # For this particular test, we will basically use the code created for the guest with different payload
# def test_create_paid_order_new_created_customer(my_orders_smoke_setup, shared_api_resources):
#     # create helper objects
#     order_helper = my_orders_smoke_setup['order_helper']
#     customer_helper = my_orders_smoke_setup['customer_helper']
#
#     # 1. Get a product from DB (We have a helper ‘product.dao’ that will return a random product ID.)
#     # rand_product = product_dao.get_random_product_from_db(1) # we use it in our setup instead
#     # product_id = rand_product[0]['ID'] # we use it in our setup instead
#     product_id = my_orders_smoke_setup['product_id']
#     # 2. Make the call - First we make a call to create a customers
#     cust_info = customer_helper.create_customer()
#     # import pdb;pdb.set_trace()  # It helps us to see the structure of 'cust_info' to extract the ID from dictionary
#     customer_id = cust_info['id']
#     shared_api_resources["created_customers"].append(customer_id)  # Cleanup for cleanup
#     # For the API call we will use woocommerce API which we created "wooAPIUtility.py"
#     # The call is going to be a POST call, and for that we create order helper because it is something repetitive.
#     # We want to use our own product, and we want to overwrite the default called "line_items" array in our template.
#     # We want our 'product_id' to be our 'product_id' variable that we get from our DB so will update payload for order
#     # creation and add new attribute 'customer_id'.  The 'info' which is our partial payload is copied from our JSON
#     # template, and we just added curly brackets since it must be a dictionary format.
#     order_payload = {
#         "line_items": [{"product_id": product_id, "quantity": 1}],
#         "customer_id": customer_id
#     }
#     order_json = order_helper.create_order(additional_args=order_payload)
#     shared_api_resources["created_orders"].append(order_json["id"])
#     with open("my_orders.json", "w") as file:
#         json.dump(order_json, file)
#
#     # 3. Verify response (FYI, we already checked the status code is 201 in our 'wooNOTUSED_orders_helper.py'.)
#     expected_products = [{"product_id": product_id, "quantity": 1, "variation_id": 0}]  # It has to be a list with
#     # product id. If you want to validate something else, you must add key-value pairs into the list. You can
#     # dynamically extract quantity and variation_id from rand_product from get_random_product_from_db.
#     order_helper.verify_order_is_created(order_json, customer_id, expected_products)
#
#
