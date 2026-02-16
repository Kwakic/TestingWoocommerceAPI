from EcommerceAPI.src.utilities.dbUtility import DBUtility
import random


class CouponsDAO(object):
    def __init__(self):
        self.db_helper = DBUtility()

    def get_random_shop_coupon(self, qty=1):
        sql = f"SELECT * FROM new_kwaki.wp_posts WHERE post_type = 'shop_coupon' LIMIT 5000;"
        rs_sql = self.db_helper.execute_select(sql)
        return random.sample(rs_sql, int(qty))

    def get_product_by_id(self, coupon_id):
        sql = f"SELECT * FROM new_kwaki.wp_posts WHERE post_type = 'shop_coupon' AND {coupon_id} = 384 LIMIT 5000;"
        rs_sql = self.db_helper.execute_select(sql)
        return rs_sql



