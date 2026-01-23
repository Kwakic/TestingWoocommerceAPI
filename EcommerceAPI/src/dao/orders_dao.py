from EcommerceAPI.src.utilities.dbUtility import DBUtility
import logging as logger


class OrdersDao(object):  # object in the parenthesis will inherit objects by default in Python 3

    def __init__(self):
        self.db_helper = DBUtility()
        self.table = 'new_kwaki.wp_posts'

    def get_order_lines_by_order_id(self, order_id):
        try:
            if not isinstance(order_id, int):
                raise ValueError(f"Expected 'order_id' to be int, got {type(order_id)}")

            sql = """
                   SELECT * FROM new_kwaki.wp_woocommerce_order_items
                   WHERE order_id = %s; 
                  """
            logger.debug(f"🛠 Fetching order lines for order_id {order_id}")
            rs_sql = self.db_helper.execute_select(sql, (order_id,))

            if not rs_sql:
                logger.warning(f"⚠️ No order lines found for order_id {order_id}")
            return rs_sql

        except Exception as e:
            logger.error(f"🚨 Error fetching order lines: {e}")
            raise

    def get_order_items_details(self, order_item_id):
        try:
            if not isinstance(order_item_id, int):
                raise ValueError(f"Expected 'order_item_id' to be int, got {type(order_item_id)}")

            sql = """
                SELECT * FROM new_kwaki.wp_woocommerce_order_itemmeta
                WHERE order_item_id = %s;
            """
            logger.debug(f"🛠 Fetching item metadata for order_item_id {order_item_id}")
            rs_sql = self.db_helper.execute_select(sql, (order_item_id,))

            if not rs_sql:
                logger.warning(f"⚠️ No metadata found for order_item_id {order_item_id}")
                return {}

            line_details = {
                meta['meta_key']: meta['meta_value']
                for meta in rs_sql if 'meta_key' in meta
            }

            logger.debug(f"✅ Retrieved {len(line_details)} meta fields for order_item_id {order_item_id}")
            return line_details

        except Exception as e:
            logger.error(f"🚨 Error fetching metadata for order_item_id {order_item_id}: {e}")
            raise

        # | Feature                      | Benefit                                |
        # | ---------------------------  | -------------------------------------- |
        # | ✅ Parameterized SQL         | Protects from SQL injection            |
        # | ✅ Cleaner Logging           | Easier debugging and traceability      |
        # | ✅ Better Error Messages     | Easier test and prod failure debugging |
        # | ✅ Scalable `execute_select` | Supports both raw and dynamic queries  |

        #
        # | Feature                 | f-string (`f"...{val}..."`)  | Parameterized (`"... %s"`) |
        # | ----------------------- | ---------------------------  | -------------------------- |
        # | Readability             | 👍 Easy                      | 👌 Slightly more verbose   |
        # | Safe from SQL injection | ❌ No                        | ✅ Yes                      |
        # | Auto-handles escaping   | ❌ No                        | ✅ Yes                      |
        # | Recommended for tests   | ✅ Sometimes                 | ✅ Always                   |
        # | Recommended in prod     | ❌ Never                     | ✅ Always                   |

        # - %s acts as a placeholder.
        # - The value is passed separately, and the database driver (PyMySQL) handles escaping it safely.
        # - Recommended for all SQL queries — even in test automation — because:
        #    - It avoids SQL injection risks.
        #    - It's more robust if the variable includes quotes, special characters, etc.

        # The reason for adding "params" in your execute_select() --> "cur.execute(sql, params)"  within the
        # "dbUtility.py" is specifically to make parameterized queries work safely and cleanly.

    # ✅ Add insert_order_item_meta() Example
    # Below is an insert method for order item metadata using your new execute_sql() safely:
    def insert_order_item_meta(self, order_item_id, meta_key, meta_value):
        try:
            if not all([isinstance(order_item_id, int), isinstance(meta_key, str), isinstance(meta_value, (str, int))]):
                raise ValueError("Invalid input types for inserting order item metadata.")

            sql = """
                INSERT INTO new_kwaki.wp_woocommerce_order_itemmeta 
                (order_item_id, meta_key, meta_value)
                VALUES (%s, %s, %s);
            """
            params = (order_item_id, meta_key, meta_value)
            logger.debug(f"🛠 Inserting meta: {params}")
            self.db_helper.execute_sql(sql, params)
            logger.info(f"✅ Inserted meta_key '{meta_key}' for order_item_id {order_item_id}")

        except Exception as e:
            logger.error(f"🚨 Error inserting metadata for order_item_id {order_item_id}: {e}")
            raise

    # ✅ Add update_order_item_meta() Example
    # Here’s how you could safely update existing metadata:
    def update_order_item_meta(self, order_item_id, meta_key, new_value):
        try:
            if not all([isinstance(order_item_id, int), isinstance(meta_key, str), isinstance(new_value, (str, int))]):
                raise ValueError("Invalid input types for updating order item metadata.")

            sql = """
                UPDATE new_kwaki.wp_woocommerce_order_itemmeta
                SET meta_value = %s
                WHERE order_item_id = %s AND meta_key = %s;
            """
            params = (new_value, order_item_id, meta_key)
            logger.debug(f"🛠 Updating meta_key '{meta_key}' with new value: {new_value}")
            self.db_helper.execute_sql(sql, params)
            logger.info(f"✅ Updated meta_key '{meta_key}' for order_item_id {order_item_id}")

        except Exception as e:
            logger.error(f"🚨 Error updating metadata for order_item_id {order_item_id}: {e}")
            raise

    # ✅ Add delete_order_item_meta() Example
    # Here’s how you could safely delete_it.py existing metadata:
    def delete_order_item_meta(self, order_item_id, meta_key):
        try:
            if not isinstance(order_item_id, int) or not isinstance(meta_key, str):
                raise ValueError("Expected 'order_item_id' as int and 'meta_key' as str.")

            sql = """
                DELETE FROM new_kwaki.wp_woocommerce_order_itemmeta
                WHERE order_item_id = %s AND meta_key = %s;
            """
            params = (order_item_id, meta_key)
            logger.debug(f"🗑️ Deleting meta_key '{meta_key}' for order_item_id {order_item_id}")
            self.db_helper.execute_sql(sql, params)
            logger.info(f"✅ Deleted meta_key '{meta_key}' for order_item_id {order_item_id}")

        except Exception as e:
            logger.error(f"🚨 Error deleting metadata for order_item_id {order_item_id}: {e}")
            raise



