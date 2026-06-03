# import pytest
# import logging as logger
#
# from EcommerceAPI.src.helpers.woo_orders_helper import OrdersHelper
# from EcommerceAPI.src.helpers.products_helper import ProductsHelper
# from EcommerceAPI.src.helpers.woo_coupons_helper import CouponsHelper
# from EcommerceAPI.src.utils.genericUtilities import generate_random_coupon_code, generate_random_string
#
#
# @pytest.mark.parametrize(
#     "discount_type, amount, minimum_amount, product_price_offset, expected_status_code, expect_discount, free_shipping",
#     [
#         # ✅ Percentage discount - Valid
#         ("percent", "50.00", "35", 5, 201, True, False),
#
#         # ❌ Percentage discount - Price under minimum
#         ("percent", "50.00", "35", -10, 400, False, False),
#
#         # ✅ Fixed amount discount - Valid
#         ("fixed_cart", "15.00", "30", 10, 201, True, False),
#
#         # ❌ Fixed amount discount - Under a minimum
#         ("fixed_cart", "10.00", "40", -5, 400, False, False),
#
#         # ✅ Free shipping only - No discount
#         ("fixed_cart", "0.00", "0", 5, 201, False, True)
#     ]
# )
# #
# # | Scenario                          | Discount Applied | Free Shipping | Pass/Fail |
# # | --------------------------------- | ---------------- | ------------- | --------- |
# # | 50% off coupon meets minimum      | ✅ Yes            | ❌ No          | ✅ Pass    |
# # | 50% off but under minimum         | ❌ No             | ❌ No          | ❌ Fail    |
# # | \$15 off fixed cart meets minimum | ✅ Yes            | ❌ No          | ✅ Pass    |
# # | \$10 off fixed cart under minimum | ❌ No             | ❌ No          | ❌ Fail    |
# # | Free shipping only                | ❌ No             | ✅ Yes         | ✅ Pass    |
# #
# #
# # Explanation of Each Key:
# # | Key                    | Purpose                                                            |
# # | ---------------------- | ------------------------------------------------------------------ |
# # | `discount_type`        | Must be `percent`, `fixed_cart`, or `fixed_product`                |
# # | `amount`               | Discount value — string formatted as WooCommerce expects           |
# # | `minimum_amount`       | Minimum cart total required for coupon to apply                    |
# # | `product_price_offset` | Offset added to `minimum_amount` to calculate product price        |
# # | `expected_status_code` | What the test should expect — `201` for success, `400` for failure |
# # | `expect_discount`      | Whether you expect the coupon to affect the total                  |
# # | `free_shipping`        | Optional boolean to enable free shipping via coupon                |
# #
# @pytest.mark.tcid66
# def test_coupon_combinations(
#         shared_api_resources,
#         discount_type,
#         amount,
#         minimum_amount,
#         product_price_offset,
#         expected_status_code,
#         expect_discount,
#         free_shipping
# ):
#     coupon_code = generate_random_coupon_code(5, 'Test').lower()
#
#     coupon_payload = {
#         'code': coupon_code,
#         'discount_type': discount_type,
#         'amount': amount,
#         'minimum_amount': minimum_amount,
#         'free_shipping': free_shipping
#     }
#
#     rs_coupon = shared_api_resources['coupon_helper'].call_create_coupon(coupon_payload)
#     shared_api_resources['created_coupons'].append(rs_coupon['id'])
#
#     # Create product based on price offset
#     product_price = float(minimum_amount) + product_price_offset
#     product_payload = {
#         'name': generate_random_string(10),
#         'type': 'simple',
#         'regular_price': str(product_price)
#     }
#
#     rs_product = shared_api_resources['product_helper'].call_create_product(product_payload)
#     shared_api_resources['created_products'].append(rs_product['id'])
#
#     order_payload = {
#         "line_items": [{"product_id": rs_product['id'], "quantity": 1}],
#         "shipping_lines": [{
#             "method_id": "flat_rate",
#             "method_title": "Flat Rate",
#             "total": "5.00" if not free_shipping else "0.00"
#         }],
#         "coupon_lines": [{"code": coupon_code}]
#     }
#
#     rs_order = shared_api_resources['order_helper'].create_order(
#         additional_args=order_payload,
#         expected_status_code=expected_status_code
#     )
#
#     if expected_status_code == 201:
#         shared_api_resources['created_orders'].append(rs_order['id'])
#
#         product_price_val = float(rs_product['price'])
#
#         # Calculate expected total
#         if expect_discount:
#             if discount_type == "percent":
#                 discount = product_price_val * float(amount) / 100
#             elif discount_type == "fixed_cart":
#                 discount = min(float(amount), product_price_val)
#             else:
#                 discount = 0.0
#         else:
#             discount = 0.0
#
#         shipping_cost = 0.0 if free_shipping else 5.00
#         expected_total = round(product_price_val - discount + shipping_cost, 2)
#         actual_total = round(float(rs_order['total']), 2)
#
#         assert actual_total == expected_total, (
#             f"Expected total: {expected_total}, got: {actual_total} "
#             f"(Discount type: {discount_type}, Amount: {amount}, Free shipping: {free_shipping})"
#         )
#
#     else:
#         # Negative test: check response structure and error message
#         assert rs_order.get('data', {}).get('status') == expected_status_code, (
#             f"Expected status {expected_status_code}, got {rs_order.get('data', {}).get('status')}"
#         )
#         assert 'message' in rs_order, "Missing error message in response"
#         assert 'minimum spend' in rs_order.get('message', '').lower(), (
#             f"Expected minimum spend error message. Got: {rs_order.get('message')}"
#         )
