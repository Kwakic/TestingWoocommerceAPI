"""
ProductsDAO — Data Access Object for Products (WooCommerce wp_posts table).

Responsibilities:
- Direct database queries via DBUtility
- No business logic
- No assertions
- No HTTP calls
- Secure parameterized queries
- Consistent logging and error handling

Design Principles:
✔ Thin wrapper around DB
✔ One query per method
✔ Input validation on every method
✔ Clear, descriptive method names
✔ Structured logging (info/debug/warning/error)
✔ Always return consistent types (dict, list, or None)
✔ Let exceptions bubble up (caller's responsibility)
"""

from __future__ import annotations

import logging
from typing import Optional, List, Dict, Any

from EcommerceAPI.src.utils.db_utility import DBUtility

logger = logging.getLogger(__name__)


class ProductsDAO(object):
    """
    Data Access Object for Products (wp_posts table).

    Provides secure database access for product data without business logic.
    """

    def __init__(self):
        """Initialize DB connection and table reference."""
        self.db_helper = DBUtility()
        self.table_name = (
            f"{self.db_helper.database}.{self.db_helper.table_prefix}posts"
        )
        logger.debug("🗄️ ProductsDAO initialized: table=%s", self.table_name)

    # -------- READ (SINGLE) --------

    def get_product_by_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single product by ID.

        Args:
            product_id (int): Product ID (post ID in wp_posts)

        Returns:
            dict: Product record or None if not found

        Raises:
            ValueError: If product_id is invalid
            Exception: If database query fails
        """
        if not isinstance(product_id, int) or product_id <= 0:
            raise ValueError(
                f"Invalid product ID: {product_id}. Must be a positive integer."
            )

        sql = (
            f"SELECT * FROM {self.table_name} "
            f"WHERE ID = :product_id AND post_type = 'product' LIMIT 1;"
        )
        params = {"product_id": product_id}

        try:
            results = self.db_helper.execute_select(sql, params)

            if not results:
                logger.info("🔍 No product found for ID=%s", product_id)
                return None

            product = results[0]

            logger.debug("ℹ️ Found product for ID=%s: %s", product_id, product)

            return product

        except Exception as e:
            logger.exception("❌ Error retrieving product by ID %s: %s", product_id, e)
            raise

    def get_product_by_sku(self, sku: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single product by SKU.

        Args:
            sku (str): Product SKU (stored in postmeta)

        Returns:
            dict: Product record or None if not found

        Raises:
            ValueError: If SKU is invalid
            Exception: If database query fails
        """
        if not isinstance(sku, str) or not sku.strip():
            raise ValueError("Invalid SKU provided. Must be a non-empty string.")

        sql = (
            f"SELECT p.* FROM {self.table_name} p "
            f"INNER JOIN {self.db_helper.database}.{self.db_helper.table_prefix}postmeta pm "
            f"ON p.ID = pm.post_id "
            f"WHERE pm.meta_key = '_sku' AND pm.meta_value = :sku "
            f"AND p.post_type = 'product' LIMIT 1;"
        )
        params = {"sku": sku.strip()}

        try:
            results = self.db_helper.execute_select(sql, params)
            product = results[0] if results else None

            if product:
                logger.debug("ℹ️ Found product with SKU %s", sku)
            else:
                logger.info("🔍 No product found for SKU %s", sku)

            return product

        except Exception as e:
            logger.exception("❌ Error retrieving product by SKU %s: %s", sku, e)
            raise

    # -------- READ (MULTIPLE) --------

    def get_all_published_products(self, limit: int = 5000) -> List[Dict[str, Any]]:
        """
        Retrieve all published products.

        Args:
            limit (int): Max records to fetch (safety limit)

        Returns:
            list: Published product records (empty list if none found)

        Raises:
            Exception: If database query fails
        """
        if not isinstance(limit, int) or limit <= 0:
            raise ValueError("Limit must be a positive integer.")

        sql = (
            f"SELECT * FROM {self.table_name} "
            f"WHERE post_type = 'product' "
            f"AND post_status = 'publish' "
            f"AND sku = :sku "
            f"ORDER BY post_date DESC LIMIT 1;"
        )
        # Fetch MANY products:

        # limit = int(limit)  # ensure it's safe
        #
        # sql = (
        #     f"SELECT * FROM {self.table_name} "
        #     f"WHERE post_type = 'product' AND post_status = 'publish' "
        #     f"ORDER BY post_date DESC "
        #     f"LIMIT {limit};"
        # )

        params = {"limit": limit}

        try:
            results = self.db_helper.execute_select(sql, params)
            logger.info("✅ Retrieved %d published products", len(results))
            return results

        except Exception as e:
            logger.exception("❌ Error retrieving all published products: %s", e)
            raise

    def get_products_created_after(self, post_date: str) -> List[Dict[str, Any]]:
        """
        Retrieve all published products created after a given date.

        Args:
            post_date (str): Date threshold (ISO 8601 or MySQL format)
                            e.g., '2025-03-24 17:17:01' or '2025-03-24'

        Returns:
            list: Product records created after the date (empty list if none)

        Raises:
            ValueError: If post_date is invalid
            Exception: If database query fails

        Note:
            - Only returns published products (post_status = 'publish')
            - MySQL handles date comparison automatically
            - ISO 8601 format (2025-02-24T13:19:03Z) is converted by MySQL
        """
        if not isinstance(post_date, str) or not post_date.strip():
            raise ValueError("Invalid post_date provided. Must be a non-empty string.")

        sql = (
            f"SELECT * FROM {self.table_name} "
            f"WHERE post_type = 'product' AND post_status = 'publish' "
            f"AND post_date >= :post_date "
            f"ORDER BY post_date DESC LIMIT 10000;"
        )
        params = {"post_date": post_date.strip()}

        try:
            results = self.db_helper.execute_select(sql, params)
            logger.info(
                "✅ Retrieved %d products created after %s", len(results), post_date
            )
            return results

        except Exception as e:
            logger.exception(
                "❌ Error retrieving products created after %s: %s", post_date, e
            )
            raise

    def get_random_product_from_db(
        self, qty: int = 1, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve random product(s) from the database, optionally filtered.

        Args:
            qty (int): Number of random products to retrieve
            filters (dict, optional): Filter conditions
                                     e.g., {'post_status': 'publish', 'post_type': 'product'}

        Returns:
            list: Random product records (empty list if none available)

        Raises:
            ValueError: If qty is invalid or filter column is invalid
            Exception: If database query fails

        Note:
            - Default filters: post_type='product' (required)
            - Uses LIMIT 5000 before randomization (efficient)
            - Uses ORDER BY RAND() for randomization
            - Returns fewer than qty if not enough records available
        """
        if not isinstance(qty, int) or qty <= 0:
            raise ValueError("Quantity must be a positive integer.")

        # ✅ Whitelist allowed filter columns (prevent SQL injection)
        VALID_FILTER_COLUMNS = {
            "ID",
            "post_title",
            "post_content",
            "post_status",
            "post_type",
            "post_author",
            "post_date",
            "post_date_gmt",
            "post_modified",
            "post_modified_gmt",
        }

        # ✅ Base SQL with required post_type filter
        base_sql = f"SELECT * FROM {self.table_name} WHERE post_type = 'product'"
        where_clauses = []
        params = {"post_type": "product"}

        # ✅ Dynamically build WHERE clause for optional filters
        if filters:
            for column, value in filters.items():
                if column not in VALID_FILTER_COLUMNS:
                    raise ValueError(
                        f"Invalid filter column '{column}'. "
                        f"Allowed columns: {', '.join(sorted(VALID_FILTER_COLUMNS))}"
                    )
                where_clauses.append(f"{column} = :{column}")
                params[column] = value

        if where_clauses:
            base_sql += " AND " + " AND ".join(where_clauses)

        # ✅ Add randomization and limit
        base_sql += " ORDER BY RAND() LIMIT :qty;"
        params["qty"] = qty

        try:
            results = self.db_helper.execute_select(base_sql, params)

            if not results:
                logger.warning("⚠️ No products found with filters: %s", filters or {})
                return []

            logger.debug(
                "✅ Retrieved %d random product(s) with filters %s",
                len(results),
                filters or {},
            )
            return results

        except Exception as e:
            logger.exception(
                "❌ Error retrieving random products with filters %s: %s", filters, e
            )
            raise

    # -------- COUNT --------

    def count_products(self) -> int:
        """
        Get total count of products in database.

        Returns:
            int: Total product count

        Raises:
            Exception: If database query fails
        """
        sql = (
            f"SELECT COUNT(*) as total FROM {self.table_name} "
            f"WHERE post_type = 'product' LIMIT 5000;"
        )

        try:
            results = self.db_helper.execute_select(sql)
            count = results[0]["total"] if results else 0
            logger.debug("📊 Total product count: %d", count)
            return count

        except Exception as e:
            logger.exception("❌ Error counting products: %s", e)
            raise

    def count_published_products(self) -> int:
        """
        Get count of published products only.

        Returns:
            int: Published product count

        Raises:
            Exception: If database query fails
        """
        sql = (
            f"SELECT COUNT(*) as total FROM {self.table_name} "
            f"WHERE post_type = 'product' AND post_status = 'publish';"
        )

        try:
            results = self.db_helper.execute_select(sql)
            count = results[0]["total"] if results else 0
            logger.debug("📊 Published product count: %d", count)
            return count

        except Exception as e:
            logger.exception("❌ Error counting published products: %s", e)
            raise

    # -------- EXISTENCE CHECKS --------

    def product_exists(self, product_id: int) -> bool:
        """
        Check if a product exists by ID.

        Args:
            product_id (int): Product ID

        Returns:
            bool: True if exists, False otherwise

        Raises:
            ValueError: If product_id is invalid
        """
        if not isinstance(product_id, int) or product_id <= 0:
            raise ValueError(
                f"Invalid product ID: {product_id}. Must be a positive integer."
            )

        product = self.get_product_by_id(product_id)
        return product is not None

    def sku_exists(self, sku: str) -> bool:
        """
        Check if a product with the given SKU exists.

        Args:
            sku (str): Product SKU

        Returns:
            bool: True if exists, False otherwise

        Raises:
            ValueError: If SKU is invalid
        """
        if not isinstance(sku, str) or not sku.strip():
            raise ValueError("Invalid SKU provided. Must be a non-empty string.")

        product = self.get_product_by_sku(sku)
        return product is not None

    # -------- METADATA --------

    def get_product_meta(
        self, product_id: int, meta_key: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve product metadata by key.

        Args:
            product_id (int): Product ID
            meta_key (str): Meta key name (e.g., '_price', '_sku', '_stock')

        Returns:
            dict: Meta record or None if not found

        Raises:
            ValueError: If product_id or meta_key is invalid
            Exception: If database query fails
        """
        if not isinstance(product_id, int) or product_id <= 0:
            raise ValueError(
                f"Invalid product ID: {product_id}. Must be a positive integer."
            )

        if not isinstance(meta_key, str) or not meta_key.strip():
            raise ValueError("Invalid meta_key provided. Must be a non-empty string.")

        sql = (
            f"SELECT * FROM {self.db_helper.database}.{self.db_helper.table_prefix}postmeta "
            f"WHERE post_id = :product_id AND meta_key = :meta_key LIMIT 1;"
        )
        params = {"product_id": product_id, "meta_key": meta_key.strip()}

        try:
            results = self.db_helper.execute_select(sql, params)
            meta = results[0] if results else None

            if meta:
                logger.debug(
                    "ℹ️ Found metadata for product %s key=%s", product_id, meta_key
                )
            else:
                logger.debug(
                    "🔍 No metadata found for product %s key=%s",
                    product_id,
                    meta_key,
                )

            return meta

        except Exception as e:
            logger.exception(
                "❌ Error retrieving metadata for product %s key=%s: %s",
                product_id,
                meta_key,
                e,
            )
            raise

    def get_product_price_meta(self, product_id: int) -> Optional[float]:
        """
        Retrieve product regular price from metadata.

        Args:
            product_id (int): Product ID

        Returns:
            float: Price value or None if not found

        Raises:
            ValueError: If product_id is invalid
            Exception: If database query fails
        """
        if not isinstance(product_id, int) or product_id <= 0:
            raise ValueError(
                f"Invalid product ID: {product_id}. Must be a positive integer."
            )

        meta = self.get_product_meta(product_id, "_price")

        if meta:
            try:
                price = float(meta.get("meta_value", 0))
                logger.debug("ℹ️ Product %s price: %.2f", product_id, price)
                return price
            except (ValueError, TypeError) as e:
                logger.warning(
                    "⚠️ Could not convert price to float for product %s: %s",
                    product_id,
                    e,
                )
                return None

        logger.info("🔍 No price metadata found for product %s", product_id)
        return None
