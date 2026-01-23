# from EcommerceAPI.src.helpers.woo_coupons_helper import CouponsHelper
# from EcommerceAPI.src.utilities.genericUtilities import generate_random_string, generate_random_coupon_code
# # from EcommerceAPI.src.utilities.wooAPIUtility import WooAPIUtility
# import json
# import logging as logger
# import pytest
# import random
#
# pytestmark = [pytest.mark.coupons, pytest.mark.regresion]
#
#
# # @pytest.fixture(scope='module')
# # def test_data():
# #     info = {'coupon_helper': CouponsHelper(), 'created_coupons': []}
# #
# #     yield info  # Let the test run
# #
# #     # Teardown: delete_it.py all created coupons
# #     for coupon_id in info['created_coupons']:
# #         try:
# #             info['coupon_helper'].call_delete_coupon(coupon_id)
# #             logger.info(f"Deleted test coupon with ID: {coupon_id}")
# #         except Exception as e:
# #             error_message = str(e).lower()
# #             if "does not exist" in error_message or "not found" in error_message:
# #                 logger.warning(f"Coupon with ID {coupon_id} was already deleted or not found.")
# #             else:
# #                 logger.error(f"Failed to delete_it.py coupon with ID {coupon_id}: {e}")
# #     # Each test adds the coupon ID to test_data['created_coupons'].
# #     # After all tests, the yield finishes and the teardown runs — deleting each coupon.
# #     # If a test fails partway and deletes the coupon manually (or the coupon expires or is auto-deleted), this teardown
# #     # won't crash or falsely flag it.
# #     # It keeps your logs clean and accurate.
# #     # You're not treating expected exceptions (like 404s) as test failures.
# #     # NOTE: By default it's limited to up to 100 objects to be created, updated or deleted.
#
#
# @pytest.mark.parametrize("discount_type",
#                          [
#                              pytest.param(None, marks=[pytest.mark.tcid36, pytest.mark.smoke]),
#                              pytest.param('percent', marks=[pytest.mark.tcid37, pytest.mark.smoke]),
#                              pytest.param('fixed_product', marks=pytest.mark.tcid38),
#                              pytest.param('fixed_cart', marks=pytest.mark.tcid39),
#                          ])
# # Determines the type of discount that will be applied. Options: percent, fixed_cart and fixed_product. Default is
# # "fixed_cart".
# def test_create_coupon_with_various_discount_types(shared_api_resources, discount_type):
#     """
#     Creates a coupon with given 'discount type' verify the coupon is created.
#     """
#     logger.info("Testing create coupon API with discount type: %s", discount_type)
#     #  logger.info("Testing create coupon API with discount type: %s", % discount_type) # This would be invalid Python
#     #  syntax in LOGGING to add % for formatting.
#
#     # One of the tests is about not sending discount type and verify the default is used, if None is given check for
#     # default
#     expected_discount_type = discount_type if discount_type else 'fixed_cart'
#     #  if discount_type: this checks if "discount_type" is True. In Python, None, False, 0, "", and empty containers
#     # are considered False
#     #  "expected_discount_type = discount_type if discount_type else 'fixed_cart'": this means:
#     #     - If discount_type is not None or False, assign it to expected_discount_type.
#     #     - If discount_type is None (or False), assign 'fixed_cart' to expected_discount_type
#
#     # Here's the more verbose and readable version of this line:
#     # if discount_type:
#     #     expected_discount_type = discount_type
#     # else:
#     #     expected_discount_type = 'fixed_cart'
#
#     pct_off = str(random.randint(50, 90)) + ".00"
#     coupon_code = generate_random_coupon_code(5, 'Test')
#
#     # get the helper object
#     coupon_helper = shared_api_resources['coupon_helper']
#
#     # prepare data and call api
#     payload = dict()
#     payload['code'] = coupon_code  # Coupon code
#     payload['amount'] = pct_off  # The amount of discount. Should always be numeric, even if setting a percentage
#     if discount_type:
#         payload['discount_type'] = discount_type
#         # This condition checks if discount_type is True (i.e., not None, False, 0, "", etc.). If it is, it adds a
#         # 'discount_type' key to the payload dictionary.
#         # If a valid discount_type is passed (like 'percent'), it’s included in the request.
#         # If None is passed (or a false value), it’s omitted, letting the API fall back to its default behavior.
#     rs_coupon = coupon_helper.call_create_coupon(payload=payload)
#     coupon_id = rs_coupon['id']
#     with open('rs_create_coupon.json', 'w') as file:
#         json.dump(rs_coupon, file)
#     file.close()
#
#     # Track coupon for cleanup
#     shared_api_resources['created_coupons'].append(coupon_id)  # Add to a cleanup list
#
#     rs_coupon_2 = coupon_helper.call_retrieve_coupon(coupon_id)
#
#     # verify the response
#     assert rs_coupon_2['amount'] == pct_off, (f"Create coupon with 50% off responded {rs_coupon_2['amount']} for "
#                                               f"amount. Expected: {pct_off}, Actual: {rs_coupon_2['amount']}.")
#     assert rs_coupon_2['code'] == coupon_code.lower(), (f"Create coupon response has wrong 'code'. Expected: "
#                                                         f"{coupon_code.lower()}, Actual: {rs_coupon_2['code']}.")
#     assert rs_coupon_2['discount_type'] == expected_discount_type, (f"Create coupon responded with wrong "
#                                                                     f"'discount_type'. Expected: "
#                                                                     f"{expected_discount_type}, Actual: "
#                                                                     f"{rs_coupon_2['discount_type']}.")
#     # The lower() method returns a string where all characters are lower case. Symbols and Numbers are ignored.
#
#
# @pytest.mark.tcid40
# def test_create_coupon_with_invalid_discount_types(shared_api_resources):
#     """
#     Verifies using a random string in 'discount_type' of create order will fail with correct error message.
#     """
#
#     logger.info("Testing create coupon api for with invalid 'discount_type'.")
#
#     # get the helper object
#     coupon_helper = shared_api_resources['coupon_helper']
#
#     pct_off = str(random.randint(50, 90)) + ".00"
#     coupon_code = generate_random_coupon_code(5, 'Test')
#
#     # prepare data and call api
#     payload = dict()
#     payload['code'] = coupon_code  # Coupon code
#     payload['amount'] = pct_off  # The amount of discount. Should always be numeric, even if setting a percentage
#     payload['discount_type'] = generate_random_string()
#     rs_coupon = WooAPIUtility().post('coupons', params=payload, expected_status_code=400)
#
#     # import pdb;pdb.set_trace()
#
#     assert rs_coupon['code'] == 'rest_invalid_param', (f"Create coupon with invalid 'discount_type' returned 'code="
#                                                        f"{rs_coupon['code']}', Expected code = 'rest_invalid_param'")
#     assert rs_coupon['message'] == 'Invalid parameter(s): discount_type', (f"Create coupon with invalid 'discount_type' "
#                                                                            f"returned 'message={rs_coupon['message']}', "
#                                                                            f"Expected message = 'Invalid parameter(s): "
#                                                                            f"discount_type',")
#
