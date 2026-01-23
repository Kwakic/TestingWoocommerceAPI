# import json
# import pytest
# import logging as logger
# from EcommerceAPI.src.utilities.genericUtilities import generate_random_coupon_code, generate_random_string
#
#
# @pytest.mark.tcid60
# def test_valid_coupon_applies_50_percent_discount(shared_api_resources):
#     coupon_code = generate_random_coupon_code(5, '50OFF').lower()
#     coupon_payload = {
#         'code': coupon_code,
#         'discount_type': 'percent',
#         'amount': '50.00',
#         'minimum_amount': '35'
#     }
#
#     # Create coupon
#     rs_coupon = shared_api_resources['coupon_helper'].call_create_coupon(coupon_payload)
#     shared_api_resources['created_coupons'].append(rs_coupon['id'])
#     assert rs_coupon['code'].lower() == coupon_code
#
#     # Create product above minimum amount
#     product_price = float(coupon_payload['minimum_amount']) + 5
#     product_payload = {
#         'name': generate_random_string(10),
#         'type': 'simple',
#         'regular_price': str(product_price)
#     }
#
#     rs_product = shared_api_resources['product_helper'].call_create_product(product_payload)
#     shared_api_resources['created_products'].append(rs_product['id'])
#     rs_price = float(rs_product['price'])
#
#     # Create order with product + coupon
#     order_payload = {
#         "line_items": [{"product_id": rs_product['id'], "quantity": 1}],
#         "shipping_lines": [{"method_id": "flat_rate", "method_title": "Flat Rate", "total": "0.00"}],
#         "coupon_lines": [{"code": coupon_code}]
#     }
#
#     rs_order = shared_api_resources['order_helper'].create_order(additional_args=order_payload)
#     shared_api_resources['created_orders'].append(rs_order['id'])
#
#     expected_total = round(rs_price * 0.5, 2)
#     actual_total = round(float(rs_order['total']), 2)
#
#     assert actual_total == expected_total, (
#         f"Expected 50% off total: {expected_total}, Got: {actual_total}"
#     )
#
#
# @pytest.mark.tcid61
# # Despite the expected failure 400, WooCommerce still creates a draft or failed order entry in the DB — this is a known
# # WooCommerce quirk. Even invalid orders can leave behind DB records, especially if WooCommerce’s REST API validation
# # fails after the order is partially processed.
# def test_coupon_not_applied_if_under_minimum_amount(shared_api_resources):
#     # Step 1: Create a 50% off coupon with a minimum required amount
#     coupon_code = generate_random_coupon_code(5, 'Test').lower()
#     coupon_payload = {
#         'code': coupon_code,
#         'discount_type': 'percent',
#         'amount': '50.00',
#         'minimum_amount': '35'
#     }
#
#     rs_coupon = shared_api_resources['coupon_helper'].call_create_coupon(coupon_payload)
#     shared_api_resources['created_coupons'].append(rs_coupon['id'])
#
#     # Step 2: Create a product BELOW the minimum amount
#     product_price = float(coupon_payload['minimum_amount']) - 5
#     product_payload = {
#         'name': generate_random_string(10),
#         'type': 'simple',
#         'regular_price': str(product_price)
#     }
#
#     rs_product = shared_api_resources['product_helper'].call_create_product(product_payload)
#     shared_api_resources['created_products'].append(rs_product['id'])
#
#     # Step 3: Attempt to create an order with the coupon (expect failure)
#     order_payload = {
#         "line_items": [{"product_id": rs_product['id'], "quantity": 1}],
#         "shipping_lines": [{"method_id": "flat_rate", "method_title": "Flat Rate", "total": "0.00"}],
#         "coupon_lines": [{"code": coupon_code}]
#     }
#
#     # Expecting failure due to coupon restriction
#     rs_order = shared_api_resources['order_helper'].create_order(additional_args=order_payload, expected_status_code=400)
#
#     # Step 4: Assert the exact error response
#     assert rs_order['code'] == 'woocommerce_rest_invalid_coupon', f"Unexpected error code: {rs_order.get('code')}"
#
#     assert 'minimum spend' in rs_order['message'].lower(), \
#         f"Error message does not mention minimum spend: {rs_order.get('message')}"
#
#     assert rs_order['data']['status'] == 400, f"Expected HTTP 400 but got: {rs_order['data'].get('status')}"
#
#
# # Use ['key'] when you're asserting the key must be present.
# # Use .get('key') in assert messages, logging, or optional handling, where you want to avoid crashing if the key is
# # missing. Your test fails cleanly with a helpful message. You avoid it getting derailed by secondary errors
# # (like KeyError or AttributeError).
# """
# .get('message')
#     Returns None (or a default you set) if the key doesn't exist.
#     Prevents test crashes inside the assert message, which would obscure the actual assertion failure.
# """
