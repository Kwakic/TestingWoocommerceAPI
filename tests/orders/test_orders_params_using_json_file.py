#
# # Here's the test function that reads from the JSON and parameterizes each row
#
# # BENEFITS:
# # | JSON test matrix    | ✅          |
# # | Discount logic      | ✅          |
# # | Error checks        | ✅          |
# # | Reusable & scalable | ✅          |
# #
#
# # | Key                    | Purpose                                                            |
# # | ---------------------- | ------------------------------------------------------------------ |
# # | `name`                 | Just for logging/debugging purposes                                |
# # | `discount_type`        | Must be `percent`, `fixed_cart`, or `fixed_product`                |
# # | `amount`               | Discount value — string formatted as WooCommerce expects           |
# # | `minimum_amount`       | Minimum cart total required for coupon to apply                    |
# # | `product_price_offset` | Offset added to `minimum_amount` to calculate product price        |
# # | `expected_status_code` | What the test should expect — `201` for success, `400` for failure |
# # | `expect_discount`      | Whether you expect the coupon to affect the total                  |
# # | `free_shipping`        | Optional boolean to enable free shipping via coupon                |
#
# import pytest
# import json
# import os
# from EcommerceAPI.src.utilities.genericUtilities import generate_random_coupon_code, generate_random_string
# from EcommerceAPI.src.utilities.data_utils import load_coupon_scenarios
#
#
# @pytest.mark.parametrize("scenario", load_coupon_scenarios())
# @pytest.mark.tcid555
# def test_coupon_scenarios(shared_api_resources, scenario):
#     coupon_helper = shared_api_resources['coupon_helper']
#     product_helper = shared_api_resources['product_helper']
#     order_helper = shared_api_resources['order_helper']
#
#     # --- Create Coupon ---
#     coupon_payload = {
#         "code": generate_random_coupon_code(5, "Test"),
#         "discount_type": scenario["discount_type"],
#         "amount": scenario["amount"],
#         "minimum_amount": scenario["minimum_amount"]
#     }
#
#     if scenario.get("free_shipping"):
#         coupon_payload["free_shipping"] = True
#
#     rs_coupon = coupon_helper.call_create_coupon(coupon_payload)
#     shared_api_resources['created_coupons'].append(rs_coupon["id"])  # ✅ Track for cleanup
#
#     rs_coupon_code = rs_coupon["code"]
#     rs_discount = float(rs_coupon["amount"])
#     min_amount = float(rs_coupon["minimum_amount"])
#
#     assert rs_coupon_code == coupon_payload["code"].lower()
#
#     # --- Create Product ---
#     price_offset = scenario.get("product_price_offset", 1)
#     product_price = round(min_amount + price_offset, 2)
#
#     product_payload = {
#         "name": generate_random_string(8),
#         "type": "simple",
#         "regular_price": str(product_price)
#     }
#
#     rs_product = product_helper.call_create_product(product_payload)
#     shared_api_resources['created_products'].append(rs_product["id"])  # ✅ Track for cleanup
#
#     rs_product_id = rs_product["id"]
#     rs_price = float(rs_product["price"])
#
#     # --- Create Order ---
#     shipping_total = 0.0 if scenario.get("free_shipping") else 5.00
#
#     order_payload = {
#         "line_items": [{"product_id": rs_product_id, "quantity": 1}],
#         "shipping_lines": [{
#             "method_id": "flat_rate",
#             "method_title": "Flat Rate",
#             "total": str(shipping_total)
#         }],
#         "coupon_lines": [{"code": rs_coupon_code}]
#     }
#
#     rs_order = order_helper.create_order(
#         additional_args=order_payload,
#         expected_status_code=scenario["expected_status_code"]
#     )
#
#     # --- If 400 Expected (Negative Test) ---
#     if scenario["expected_status_code"] == 400:
#         assert rs_order["code"] == "woocommerce_rest_invalid_coupon"
#         assert "minimum spend" in rs_order["message"].lower()
#         return
#
#     shared_api_resources['created_orders'].append(rs_order["id"])  # ✅ Track for cleanup
#
#     # --- Positive Test: Verify Coupon Applied Correctly ---
#     expected_total = rs_price
#
#     if scenario.get("expect_discount", True):
#         if scenario["discount_type"] == "percent":
#             discount = rs_price * rs_discount / 100
#         else:
#             discount = rs_discount
#         expected_total -= discount
#
#     expected_total += shipping_total
#     expected_total = round(expected_total, 2)
#
#     actual_total = round(float(rs_order["total"]), 2)
#
#     assert actual_total == expected_total, (
#         f"{scenario['name']} - Discount mismatch. Expected: {expected_total}, Got: {actual_total}"
#     )
#
#     if scenario.get("free_shipping"):
#         assert float(rs_order.get("shipping_total", 0)) == 0.0, (
#             f"{scenario['name']} - Shipping was not free as expected."
#         )
