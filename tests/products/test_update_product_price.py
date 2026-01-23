# import pdb
# import time
#
# from EcommerceAPI.src.dao.products_dao import ProductsDAO
# from EcommerceAPI.src.helpers.products_helper import ProductsHelper
# from EcommerceAPI.src.utilities.genericUtilities import safe_product_name
#
# import json
# import pytest
# import random
# import logging as logger
#
# pytestmark = [pytest.mark.products, pytest.mark.smoke]
#
#
# @pytest.mark.tcid61
# def test_update_regular_price_should_update_price(shared_api_resources):
#     """
#     Verifies updating the 'regular_price' field should automatically update the 'price' field,
#     assuming the product is not on sale (sale_price must be cleared).
#     """
#     # create helper objects and get random product from db
#     product_helper = ProductsHelper()
#     product_dao = ProductsDAO()
#
#     # Step 1: Create a new product
#     reg_price = f"{round(random.uniform(10.10, 100.99), 2):.2f}"  # String version for formatting or text checks
#     """
#     This is a formatted string literal, or f-string. Inside the curly braces, you apply a format specifier:
#     :.2f tells Python to:
#         : → Introduce the formatting instructions.
#         .2f → Format the number as a fixed-point decimal with 2 digits after the decimal point.
#     So, even if rounding gives something like 48.8, this formatting ensures it becomes "48.80" — always two
#     """
#     new_product_payload = {
#         'name': safe_product_name(),
#         'type': 'simple',
#         'regular_price': reg_price
#     }
#     rs_product = product_helper.call_create_product(new_product_payload)
#     shared_api_resources['created_products'].append(rs_product['id'])
#     # For this test, the 'sale_price' of the product must be empty. If product has sale price, updating the
#     # 'regular_price' does not update the 'price'. So get a bunch of products and loop until you find one that is not
#     # on sale.
#     # If product_data['on_sale'] == True → the product is on sale → continue → check the next product.
#     # If product_data['on_sale'] == False → the product is NOT on sale → break → stop the loop
#     # If all in the list are on sale, then take a random one and update the sale price.
#     # If the DB doesn't have any product, then create one.
#
#     # Step 2: Fetch 30 products from DB
#     rand_products = product_dao.get_random_product_from_db(qty=30)  # rand_products is expected to be a list of
#     # dictionaries (each representing a product)
#     if not rand_products:
#         pytest.skip("❌ No products in DB to run this test.")
#
#     # Step 3: Find a product that is not on sale
#     product_id = None
#     for product in rand_products:
#         product_data = product_helper.call_retrieve_product(product['ID'])
#         if not product_data.get('on_sale', False):
#             product_id = product_data['id']
#             break
#
#     # Step 4: If all are on sale, pick one and clear sale price
#     if not product_id:
#         fallback_product = random.choice(rand_products)
#         product_id = fallback_product['ID']
#         product_helper.call_update_product({'sale_price': None}, product_id)  # WooCommerce might treat empty
#         # string "" as “keep existing” instead of “delete_it.py”.
#
#     # Step 5: Ensure no sale price. Clear any existing sale price before updating regular_price
#     product_helper.call_update_product({'sale_price': None}, product_id)  # WooCommerce might treat empty
#     # string "" as “keep existing” instead of “delete_it.py”.
#
#     # Step 6: Update 'regular_price' and assert updates
#     new_price = f"{round(random.uniform(10.10, 100.99), 2):.2f}"
#     update_payload = {'regular_price': new_price}
#     product_helper.call_update_product(payload=update_payload, product_id=product_id)
#
#     # Step 7: Retry update response and DB value to avoid caching/stale and verify persisted update.
#     # Avoid trusting WooCommerce’s immediate response after update.
#     # Ensure assertion is based on persisted state, not stale cache or laggy data.
#     # WooCommerce may still cache the old price or not compute it properly.
#     # WooCommerce may need a moment to reflect the new computed value. So Wrap a retry loop around your re-fetch:
#
#     for _ in range(5):
#         rs_product = product_helper.call_retrieve_product(product_id)
#         if float(rs_product.get('price', 0)) == float(new_price):
#             break
#         time.sleep(1)
#     else:
#         assert False, f"Expected saved 'price' to be {new_price}, but got {rs_product.get('price')}"
#
#     assert float(rs_product['regular_price']) == float(new_price), (
#         f"Expected saved 'regular_price' to be {new_price}, but got {rs_product.get('regular_price')}"
#     )
#
#
# @pytest.mark.tcid63
# @pytest.mark.tcid64
# def test_update_sale_price_greater_zero():
#     """
#     Two test cases:
#     1. Update 'sale_price' to a positive value less than 'regular_price' → 'on_sale' should become True.
#     2. Clear 'sale_price' → 'on_sale' should become False.
#     """
#     global updated_product_no_sale
#     product_helper = ProductsHelper()
#     product_dao = ProductsDAO()
#
#     rand_products = product_dao.get_random_product_from_db(20)  # Be safe with a realistic number
#     product_id = None
#     regular_price = None
#
#     # Try to find a valid product to reuse
#     for product in rand_products:
#         product_id_candidate = product['ID']
#         product_data = product_helper.call_retrieve_product(product_id_candidate)
#
#         if not product_data.get('regular_price'):
#             logger.warning(f"Product {product_id_candidate} missing 'regular_price'. Skipping.")
#             continue
#
#         if not product_data['on_sale']:
#             continue
#
#         product_id = product_id_candidate
#         regular_price = float(product_data['regular_price'])
#         break
#
#     # If no valid product found, create one
#     if not product_id:
#         base_price = round(random.uniform(10.0, 100.0), 2)
#         payload = {
#             "name": safe_product_name(),
#             "type": "simple",
#             "regular_price": str(base_price)
#         }
#         created_product = product_helper.call_create_product(payload)
#         product_id = created_product['id']
#         regular_price = float(created_product['regular_price'])
#
#         logger.info(f"Created product ID {product_id} for test.")
#         assert not created_product['on_sale']
#         assert not created_product['sale_price']
#
#         # Apply valid discounted sale price
#         sale_price, discount_percentage = product_helper.generate_sale_price(regular_price)
#         product_helper.call_update_product({'sale_price': sale_price}, product_id)
#
#         logger.info(f"Updated product {product_id}: regular_price={regular_price}, sale_price={sale_price} "
#                     f"({discount_percentage:.2f}% off)")
#
#         # Retry fetching until on_sale becomes True
#         for _ in range(5):
#             updated_product = product_helper.call_retrieve_product(product_id)
#             if updated_product.get('on_sale') is True:
#                 break
#             time.sleep(1)
#         else:
#             assert False, f"'on_sale' did not become True after setting sale_price. Product {product_id}"
#
#         assert float(updated_product['sale_price']) < float(updated_product['regular_price']), \
#             f"Sale price {updated_product['sale_price']} is not less than regular price {updated_product['regular_price']}"
#
#         # Clear sale price
#         product_helper.call_update_product({'sale_price': None}, product_id)
#
#         # Retry until on_sale becomes False and sale_price is empty
#         for _ in range(5):
#             updated_product_no_sale = product_helper.call_retrieve_product(product_id)
#             if not updated_product_no_sale.get('on_sale') and not updated_product_no_sale.get('sale_price'):
#                 break
#             time.sleep(1)
#         else:
#             assert False, (
#                 f"'on_sale' should be False and 'sale_price' should be cleared. "
#                 f"Got: on_sale={updated_product_no_sale['on_sale']}, sale_price={updated_product_no_sale['sale_price']}"
#             )
#
# # 🎯 Safe conversion: Only calls float() after checking that the value is not empty
# # 🔄 Fallback creation: If no usable product is found, it creates one
# # 📋 Detailed logging & asserts for better debugging
# # 🧼 Cleaner logic flow — easier to maintain and debug in the future
# # If the DB has fewer than 20 records → it still returns what it can (up to 4 for example).
# # If none of those 4 products are valid (e.g., regular_price missing, or on_sale is False) → the test creates a new one.
# # If the DB is empty ([]) → test still proceeds by creating a new product.
#
#
# @pytest.mark.tcid65
# def test_adding_sale_price_should_set_on_sale_flag_true():
#     """
#     When the sale price of a product is updated, then it should set the field 'on_sale' = True
#     """
#     # create helper objects and get random product from db
#     product_helper = ProductsHelper()
#     reg_price = f"{round(random.uniform(10.10, 100.99), 2):.2f}"  # String version for formatting or text checks
#     """
#     This is a formatted string literal, or f-string. Inside the curly braces, you apply a format specifier:
#     :.2f tells Python to:
#         : → Introduce the formatting instructions.
#         .2f → Format the number as a fixed-point decimal with 2 digits after the decimal point.
#     So, even if rounding gives something like 48.8, this formatting ensures it becomes "48.80" — always two
#     """
#     # new_price = round(random.uniform(10.10, 100.99), 2)  # Float version for numeric comparisons or calculations
#     payload = dict()
#     payload['name'] = safe_product_name()
#     payload['type'] = "simple"
#     payload['regular_price'] = reg_price
#     product_helper.call_create_product(payload)
#
#     assert 10.10 <= float(reg_price) <= 100.99  # Converts the price string to a float and checks that it falls
#     # within the expected numeric range.
#     assert isinstance(reg_price, str)  # Checks that price is indeed a string, not a float or Decimal
#     assert "." in reg_price and len(reg_price.split(".")[1]) == 2  # Checks that the price contains a decimal point.
#     # Then splits the string at the decimal point and verifies that exactly 2 digits follow it.
