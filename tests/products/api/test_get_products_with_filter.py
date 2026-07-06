# import pytest
# import json
# from EcommerceAPI.src.helpers.products_helper import ProductsHelper
# from EcommerceAPI.src.dao.products_dao import ProductsDAO
# from datetime import datetime, timedelta
#
#
# @pytest.mark.regression
# class TestListProductsWithFilter(object):
#
#     @pytest.mark.tcid51  # all the tests are going to be part of regression test that are part of this class
#     def test_list_products_with_filter_after(self):
#         # 1. Create data
#         # The datetime must be in ISO8601 format: 'YYYY-MM-DDTHH:MM:SS' (e.g.: 2024-04-24 22:54:06). "T" means ISO8601
#         # format. We create it using 'datetime' library. What we want is to get a product x days ago.
#         x_days_from_today = 300
#         _after_created_date = datetime.now().replace(microsecond=0) - timedelta(days=x_days_from_today)  # We needed
#         # to add '.replace(microsecond=0)' to get rid of milliseconds. Timedelta is a duration expressing the
#         # difference between two datetime or date instances to microsecond resolution.
#         # pdb.set_trace()  # response is: (2024, 3, 26, 17, 54, 53) which we need to convert into ISO8601 format
#         after_created_date = _after_created_date.isoformat()
#         # import pdb; pdb.set_trace()  # After conversion is like this: '2024-03-26T18:01:41'
#         # another way to create the date is as follows:
#         # tmp_date = datetime.now() - timedelta(days=x_days_from_today)
#         # after_created_date = tmp_date.strftime('%Y-%m-%dT%H:%M:%S')  # we specify the format
#         # # import pdb; pdb.set_trace()  # The outcome is: '2024-58-27T17:03:43'
#         payload = dict()
#         payload['after'] = after_created_date  # This will give us 30 days ago.
#         # payload['per_page'] = 100  --> NOTE!!! If we have more than 100 products created, the API will return max.100
#         # and test fails! We have to set new filter/parameter ‘per_page’ since by default returns only 10. So, we could
#         # add to our payload ‘payload['per_page'] = 100’ but the problem here is that if we have more than a hundred
#         # products in given date, then we receive an error. Instead, we go to our ‘product_helper.py’ to add a bunch
#         # of logics.
#
#         # 2. Make API call
#         rs_api = ProductsHelper().call_list_products(payload)
#         # import pdb; pdb.set_trace()
#         # Save the response into the JSON file
#         # with open("products_30days.json", "w") as file:
#         #     json.dump(rs_api, file)
#         assert rs_api, f"Empty response for list products with parameter/filter 'after'."
#
#         # 3. Get data from DB (making call to DB)
#         # We want to verify that actually returns the correct number of products for the last 30 days.
#         # We'll go to DB and use SQL to get all products created after the exact date and compare it with the API resp.
#         # The API documentation doesn’t specify if param ‘after’ is equal or greater nor if it starts from that date,
#         # including the date or not included that day. As it says, "after" we imagine that the day is not inclusive, so
#         # we will use the sign in our query greater to (>) instead of equal/greater to (>=).
#         db_products = ProductsDAO().get_products_created_after_given_date(after_created_date)  # The date we used to
#         # we use variable "after_created_date" for our SQL query.
#
#         # 4. Verify response matches DB (the number of products that returns APi is the same as the number of products
#         # that returns DB)
#         # NOTE!!! If we have more than 100 products created, the API will return max.100 and test fails!
#         # We have to set new filter/parameter ‘per_page’ since by default returns only 10. So, we could add to our
#         # payload ‘payload['per_page'] = 100’ but the problem here is that if we have more than a hundred products in
#         # given date, then we receive an error. Instead, we go to our ‘product_helper.py’ to add a bunch of logics.
#         assert len(rs_api) == len(db_products), (f"List products with filter 'after' returned unexpected number of "
#                                                  f"products. Expected: {db_products}, Actual: {rs_api}")
#         # Verify that products from API are actually the same as in DB(match the IDs).We get all the IDs in the DB
#         # and get all the IDs in the API and make sure they are all the same.
#         ids_in_api = [i['id'] for i in rs_api]  # We are going to loop through each one that will return a list of IDs.
#         # ids_in_api.sort()  # Ordering the values in numbers from smallest to largest for better reading in our print
#         ids_in_db = [i['ID'] for i in db_products]
#         # ids_in_db.sort()  # Ordering the values in numbers from smallest to largest for better reading in our print
#         # import pdb; pdb.set_trace()
#         # Now we have to compare that both lists are the same.There are many ways to do, but we pick one with only
#         # one line of code.
#         ids_diff = list(set(ids_in_api) - set(ids_in_db))  # First, we are going to convert each of the LIST as a SET.
#         # We are going to set(ids_in_api) and we subtract set(ids_in_db) and convert the result in two lists. If there
#         # is any difference, variable 'ids_diff' will have a value.
#         # Below assertion is here to make sure that ids_diff is empty.
#         assert not ids_diff, f"List products with filter. Product IDs in response mismatch in DB."
#
#         # -- Filter for Duplicates or Deleted Products--
#         # We want to find out:
#         # Which product IDs are returned by the API but not present in the DB.
#         # Which product IDs are in the DB but not returned by the API.
#         # Ensure that no soft-deleted or duplicated entries are included from the DB. Check:
#         # post_status = 'publish'
#         # post_type = 'product'
#         # No duplicated IDs or rows in the DB result set.
#
#         # Extract IDs from API and DB:
#         ids_in_api = [p['id'] for p in rs_api]
#         ids_in_db = [p['ID'] for p in db_products]
#         print("In API but not DB:", set(ids_in_api) - set(ids_in_db))
#         print("In DB but not API:", set(ids_in_db) - set(ids_in_api))
#         # This will pinpoint the one missing product and allow you to inspect it manually.
#
#         # the same but classic loop way:
#         # ids_in_api = []
#         # for product in rs_api:
#         #     ids_in_api.append(product['id'])
#         #
#         # ids_in_db = []
#         # for record in db_products:
#         #     ids_in_db.append(record['ID'])  # 'ID' comes from the DB schema
#
#         # Suggested Best Practice (Hybrid)
#         # For a bit more context during failures, here’s a slightly upgraded version:
#
#         # 1. Extract IDs from API and DB
#         # ids_in_api = [p['id'] for p in rs_api]
#         # ids_in_db = [p['ID'] for p in db_products]
#
#         # 2. Compare: API but not in DB
#         # api_not_in_db = list(set(ids_in_api) - set(ids_in_db))
#
#         # 3. Compare: DB but not in API
#         # db_not_in_api = list(set(ids_in_db) - set(ids_in_api))
#
#         # if api_not_in_db or db_not_in_api:
#         #     print(f"🔴 Mismatch detected!")
#         #     print(f"🟠 In API but not in DB: {api_not_in_db}")
#         #     print(f"🔵 In DB but not in API: {db_not_in_api}")
#         # This gives you a clean and readable format with flags and avoids flooding your logs when everything matches.
#
#         # Stick with your current code if:
#         #     - You're doing basic ID comparison.
#         #     - You don't need to debug deeper into product data.
#
#         # Use the hybrid or full-loop version when:
#         # - You're actively debugging.
#         # - You want full product details tied to mismatches.
