# import pytest
# import logging
#
# logger = logging.getLogger(__name__)
#
# pytestmark = [pytest.mark.products, pytest.mark.smoke]
#
#
# @pytest.mark.tcid24
# def test_get_all_products(all_resources):
#     """
#     Use shared RequestUtility from fixtures instead of constructing a new client.
#     """
#     client = all_resources.request
#     rs_api = client.get("products")
#     assert rs_api, "Response of list of products is empty"
#     assert rs_api != []
#     assert rs_api is not None
#
#
# @pytest.mark.tcid25
# def test_get_product_by_id(all_resources):
#     """
#     Use the DAO and helper from the dynamic registry (all_resources.entities) rather than instantiating them.
#     """
#     # 1. Get a Product (test data) from DB. We need a product for this test case. Either we can create the product or
#     # get it from a DB. In this case, we get a product (test data) from db.
#     # To get information from the database, we will be using DAO. So we need to create DAO because it is not going to
#     # be the only time that we need to get a product from DB.
#     # Access helper and dao from the shared registry
#
#     product_helper = all_resources.entities["products"].helper
#     assert product_helper is not None, "Products bundle not found in registry"
#
#     product_dao = all_resources.entities["products"].dao
#
#     rand_product = product_dao.get_random_product_from_db(1)
#     assert rand_product and len(rand_product) > 0, "No product found in DB to use for the test"
#     rand_product_id = rand_product[0]["ID"]
#     db_name = rand_product[0]["post_title"]
#
#     rs_api = product_helper.call_retrieve_product(rand_product_id)
#     api_name = rs_api.get("name")
#     assert db_name == api_name, (
#         f"Get product by id returned wrong product. ID: {rand_product_id} DB name: {db_name}, API name {api_name}"
#     )
#
#
# @pytest.mark.tcid66
# def test_products_db_not_empty(all_resources):
#     """
#     Use DAO from fixtures to assert DB has products.
#     """
#     product_bundle = all_resources.entities.get("products")
#     assert product_bundle is not None, "Products bundle not found in registry"
#
#     product_dao = product_bundle.dao
#     total_product = product_dao.count_product_in_db()
#     assert total_product and len(total_product) > 0, "count_product_in_db returned no rows"
#     count = total_product[0].get("COUNT(*)") or total_product[0].get("count") or total_product[0].get("count(*)")
#     assert count is not None and int(count) > 0, "No products present in DB"
