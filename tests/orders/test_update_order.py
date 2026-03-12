# import json
# from EcommerceAPI.src.helpers.woo_orders_helper import OrdersHelper
# from EcommerceAPI.src.utils.genericUtilities import generate_random_string
# from EcommerceAPI.src.utils.wooAPIUtility import WooAPIUtility
# import pytest
#
# pytestmark = [pytest.mark.orders, pytest.mark.regression]
#
#
# @pytest.mark.parametrize("new_status",
#                          [
#                              pytest.param('cancelled', marks=[pytest.mark.tcid55, pytest.mark.smoke]),
#                              pytest.param('completed', marks=pytest.mark.tcid56),
#                              pytest.param('on-hold', marks=pytest.mark.tcid57)
#                          ])
# def test_update_order_status(new_status):
#     # 1. Create new order (for that we will use our OrdersHelper)
#     order_helper = OrdersHelper()
#     order_json = order_helper.create_order()
#
#     # with open('order_status_before_update.json', 'w') as file:
#     #     json.dump(order_json, file)
#     # file.close()
#
#     # 2. Get the current status of order
#     cur_status = order_json['status']
#     assert cur_status != new_status, f'Current status of order is already {new_status}. Unable to run test.'  # First,
#     # we verify the status of the order to make sure it doesn’t have the same status that you want to update with.
#
#     # 3. Update status (making the call to update the status)
#     # First, we need to define method PUT in our 'wooAPIUtility.py' (we create new function 'def put():')
#     # Next, we will create a new function 'def call_update_an_order():' in "wooNOTUSED_orders_helper.py" which requires function
#     # PUT that we created in 'wooAPIUtility.py'.
#     order_id = order_json['id']
#     payload = {"status": new_status}
#     rs_updated = order_helper.call_update_an_order(order_id, payload)
#     # with open('order_status_updated.json', 'w') as file:
#     #     json.dump(rs_updated, file)
#     # file.close()
#     # pdb.set_trace()
#
#     # 4. Get order information
#     # We could go to a database and get an order, but instead we make GET API call to get the data. To make GET API
#     # call, we need to create a function in 'wooNOTUSED_orders_helper.py' ('def call_retrieve_an_order()')
#     # NOTE!!!!! Make sure it is not cached because when you say GET Order, and if this update doesn't bust/refresh the
#     # cache, then when you call the API GET Order it will give you outdated information. So ask developers if is cached
#     # or not! In our case is not cached.
#     # We use GET method to make sure that is retrieved from a database. That way, we don't need to make an additional
#     # test for DB. We could have used the response that returns the call to update the status but who knows if it comes
#     # from the memory or from DB. We better make call GET to ensure 100% that comes from DB.
#
#     new_order_info = order_helper.call_retrieve_an_order(order_id)  # This will retrieve the info from the DB.
#
#     # 5. Verify the new order status is what was updated
#     assert new_order_info['status'] == new_status, (f"Updated order status to '{new_status}' but order is still "
#                                                     f"'{new_order_info['status']}'")
#
#
# @pytest.mark.tcid58
# def test_update_order_status_to_random_string():  # negative test with invalid input
#     # 1. Create new order (for that we will use our OrdersHelper)
#     order_helper = OrdersHelper()
#     order_json = order_helper.create_order()
#     order_id = order_json['id']
#
#     # 2. Generate random string for the status
#     random_string = generate_random_string(15)
#     new_status = random_string
#     # import pdb; pdb.set_trace()
#
#     # 3. Update status (making the call to update the status)
#     # First, we need to define method PUT in our 'wooAPIUtility.py' (we create new function 'def put():')
#     # Next, we will create a new function 'def call_update_an_order():' in "wooNOTUSED_orders_helper.py" which requires function
#     # PUT that we created in 'wooAPIUtility.py'.
#     # Since we set status code 200 in 'wooAPIUtility.py' for method PUT, we could modify the status code either in
#     # 'def call_update_an_order():' or call it from here which we did.
#     payload = {"status": new_status}
#     rs_api = WooAPIUtility().put(f'orders/{order_id}', params=payload, expected_status_code=400)
#
#     # 4. Validate error message
#     assert rs_api['code'] == 'rest_invalid_param', (f"Update order status to random string did not have correct code "
#                                                     f"in response. Expected: 'rest_invalid_param' , Actual:{rs_api[
#                                                         'code']}")
#     assert rs_api['message'] == 'Invalid parameter(s): status', (f"Update order status to random string did not have "
#                                                                  f"correct code in response. Expected: 'Invalid "
#                                                                  f"parameter(s): status' , Actual:{rs_api['message']}")
#     # I create the following tests just for practice purposes
#     error_message = rs_api['data']['details']['status']['message']
#     assert error_message == ('status is not one of auto-draft, pending, processing, on-hold, completed, cancelled, '
#                              'refunded, failed and checkout-draft.')
#     assert 'status' in rs_api['data']['details']
#     assert 'status is not one of' in rs_api['data']['details']['status']['message']
#
#     # import pdb;pdb.set_trace()
#
#
# @pytest.mark.tcid59
# def test_update_order_customer_note():
#     # 1. Create new order (for that we will use our OrdersHelper)
#     order_helper = OrdersHelper()
#     order_json = order_helper.create_order()
#     order_id = order_json['id']
#
#     # 2. Update the order (making the call to update the status)
#     # For the note; we want to generate some random string
#     rand_string = generate_random_string(40)
#     payload = {"customer_note": rand_string}
#     order_helper.call_update_an_order(order_id, payload)
#
#     # 3. Get order information
#     new_order_info = order_helper.call_retrieve_an_order(order_id)  # This will retrieve the info from the DB.
#     assert new_order_info['customer_note'] == rand_string, (f"Update order's 'customer_note' field failed. Expected: "
#                                                             f"{rand_string}, Actual:{new_order_info['customer_note']}")
