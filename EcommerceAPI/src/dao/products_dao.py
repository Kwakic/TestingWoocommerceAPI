
from EcommerceAPI.src.utilities.dbUtility import DBUtility
import random


class ProductsDAO(object):
    def __init__(self):
        # 1. We need to import DB helper
        self.db_helper = DBUtility()

    class ProductsDAO(object):
        def __init__(self):
            self.db_helper = DBUtility()

    def get_random_product_from_db(self, qty=1):
        """
        Returns up to `qty` random product records from the DB.
        If fewer records exist, returns as many as available.
        If no products exist, returns an empty list.
        """
        # We’ll make this method safe, so it never raises ValueError if qty > available products.
        # We'll also validate qty is positive.
        if qty <= 0:
            raise ValueError("Quantity must be a positive integer.")

        sql = 'SELECT * FROM new_kwaki.wp_posts WHERE post_type = "product" LIMIT 5000;'
        rs_sql = self.db_helper.execute_select(sql)

        if not rs_sql:
            return []

        return random.sample(rs_sql, min(qty, len(rs_sql)))
        #  Handles empty product list, excessive qty, and invalid input.

    def count_product_in_db(self):     # My own test for practice (not part of learning class)
        sql = f"SELECT COUNT(*) FROM new_kwaki.wp_posts WHERE post_type ='product' LIMIT 5000;"
        rs_sql = self.db_helper.execute_select(sql)
        return rs_sql

    def get_product_by_id(self, product_id):
        sql = f"SELECT * FROM new_kwaki.wp_posts WHERE ID = {product_id};"
        rs_sql = self.db_helper.execute_select(sql)
        return rs_sql

    def get_products_created_after_given_date (self, post_date):
        # The date format (2025-03-24 17:17:01) in SQL DB is different than we use from WordPress
        # (2025-02-2T13:19:03 - isoformat). We don't need to format it here because the SQL is clever enough to
        # figure it out.

        # Note! API call (via WooCommerce) returns only status: "publish" products, while your DB query might be
        # returning all statuses.
        sql = (f"SELECT * FROM new_kwaki.wp_posts WHERE post_type = 'product' AND post_status = 'publish' AND "
               f"post_date >= '{post_date}' LIMIT 10000;")
        return self.db_helper.execute_select(sql)




