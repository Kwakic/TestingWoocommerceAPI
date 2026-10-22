"""Database access for WooCommerce orders and order line items.

The DAO returns database records for callers to inspect. It does not make API
requests, validate response models, or contain order-specific assertions.

Order records are read from the authoritative WooCommerce storage selected in
``wp_options``: either the legacy posts tables or the HPOS order tables. The
DAO normalizes both storage formats to the same mapping for validators.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from EcommerceAPI.src.utils.db_utility import DBUtility


logger = logging.getLogger(__name__)


class OrdersDAO:
    """Read and update WooCommerce order and order-item records.

    Table names use the database and WordPress table prefix configured for
    :class:`DBUtility`. Order reads follow WooCommerce's active storage mode:
    legacy WordPress posts or High-Performance Order Storage (HPOS).
    """

    HPOS_METADATA_KEYS = (
        "_order_key",
        "_customer_user",
        "_order_currency",
        "_payment_method",
        "_payment_method_title",
        "_transaction_id",
        "_created_via",
        "_order_version",
        "_customer_ip_address",
        "_customer_user_agent",
        "_cart_discount",
        "_cart_discount_tax",
        "_order_shipping",
        "_order_shipping_tax",
        "_order_tax",
        "_order_total",
    )

    def __init__(self) -> None:
        """Initialize the shared database helper and order table references."""
        self.db_helper = DBUtility()
        database = self.db_helper.database
        prefix = self.db_helper.table_prefix

        self.posts_table = f"{database}.{prefix}posts"
        self.postmeta_table = f"{database}.{prefix}postmeta"
        self.options_table = f"{database}.{prefix}options"
        self.hpos_orders_table = f"{database}.{prefix}wc_orders"
        self.hpos_order_operational_data_table = (
            f"{database}.{prefix}wc_order_operational_data"
        )
        self.hpos_order_meta_table = f"{database}.{prefix}wc_orders_meta"
        self.order_items_table = f"{database}.{prefix}woocommerce_order_items"
        self.order_itemmeta_table = f"{database}.{prefix}woocommerce_order_itemmeta"
        self.hpos_enabled = self._is_hpos_enabled()

        logger.debug(
            "OrdersDAO initialized: hpos_enabled=%s, posts=%s, hpos_orders=%s, "
            "order_items=%s, order_itemmeta=%s",
            self.hpos_enabled,
            self.posts_table,
            self.hpos_orders_table,
            self.order_items_table,
            self.order_itemmeta_table,
        )

    def _is_hpos_enabled(self) -> bool:
        """Return whether WooCommerce's HPOS tables are authoritative.

        WooCommerce records this setting as
        ``woocommerce_custom_orders_table_enabled`` in ``wp_options``.
        Missing or false values mean the legacy post tables are authoritative.
        """
        sql = (
            f"SELECT option_value FROM {self.options_table} "
            "WHERE option_name = 'woocommerce_custom_orders_table_enabled' "
            "LIMIT 1;"
        )
        rows = self.db_helper.execute_select(sql)
        if not rows:
            return False

        enabled_value = str(rows[0].get("option_value", "")).strip().lower()
        return enabled_value in {"yes", "true", "1", "on", "b:1;"}

    @staticmethod
    def _validate_positive_id(value: int, name: str) -> None:
        """Raise ``ValueError`` unless *value* is a positive integer ID."""
        if type(value) is not int or value <= 0:
            raise ValueError(f"Invalid {name}: {value}. Must be a positive integer.")

    @staticmethod
    def _validate_meta_key(meta_key: str) -> None:
        """Raise ``ValueError`` unless *meta_key* is a non-empty string."""
        if not isinstance(meta_key, str) or not meta_key.strip():
            raise ValueError("Invalid meta_key. Must be a non-empty string.")

    # ------------------------------------------------------------------
    # Read order records
    # ------------------------------------------------------------------

    def get_order_by_id(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a single WooCommerce order by ID from active storage.

        Args:
            order_id: Order ID, stored in the active WooCommerce order store.

        Returns:
            A normalized order record, or ``None`` if the ID is not a
            WooCommerce order. The normalized mapping exposes the keys used by
            the Order DB validator for both legacy storage and HPOS.

        Raises:
            ValueError: If ``order_id`` is not a positive integer.
            Exception: If the database query fails.
        """
        self._validate_positive_id(order_id, "order ID")

        try:
            if self.hpos_enabled:
                order = self._get_hpos_order_by_id(order_id)
            else:
                order = self._get_legacy_order_by_id(order_id)

            if order is None:
                logger.info("No WooCommerce order found for ID=%s", order_id)
            else:
                logger.debug(
                    "Retrieved WooCommerce order ID=%s from %s storage",
                    order_id,
                    "HPOS" if self.hpos_enabled else "legacy",
                )

            return order
        except Exception:
            logger.exception("Error retrieving WooCommerce order ID=%s", order_id)
            raise

    def _get_legacy_order_by_id(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve an order from the legacy ``posts`` table."""
        sql = (
            f"SELECT * FROM {self.posts_table} "
            "WHERE ID = :order_id AND post_type = 'shop_order' LIMIT 1;"
        )
        results = self.db_helper.execute_select(sql, {"order_id": order_id})
        return results[0] if results else None

    def _get_hpos_order_by_id(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve and normalize an order from WooCommerce's HPOS tables.

        Core order and operational columns are aliased to the legacy field and
        metadata names consumed by the existing validator. Custom order
        metadata remains available through ``get_order_metadata``.
        """
        sql = (
            "SELECT "
            "o.id AS ID, "
            "o.type AS post_type, "
            "o.status AS post_status, "
            "o.customer_note AS post_excerpt, "
            "o.customer_id AS _customer_user, "
            "o.currency AS _order_currency, "
            "o.payment_method AS _payment_method, "
            "o.payment_method_title AS _payment_method_title, "
            "o.transaction_id AS _transaction_id, "
            "o.ip_address AS _customer_ip_address, "
            "o.user_agent AS _customer_user_agent, "
            "o.tax_amount AS _order_tax, "
            "o.total_amount AS _order_total, "
            "operational.order_key AS _order_key, "
            "operational.created_via AS _created_via, "
            "operational.woocommerce_version AS _order_version, "
            "operational.discount_total_amount AS _cart_discount, "
            "operational.discount_tax_amount AS _cart_discount_tax, "
            "operational.shipping_total_amount AS _order_shipping, "
            "operational.shipping_tax_amount AS _order_shipping_tax "
            f"FROM {self.hpos_orders_table} AS o "
            f"LEFT JOIN {self.hpos_order_operational_data_table} AS operational "
            "ON operational.order_id = o.id "
            "WHERE o.id = :order_id AND o.type = 'shop_order' LIMIT 1;"
        )
        results = self.db_helper.execute_select(sql, {"order_id": order_id})
        return results[0] if results else None

    def get_order_lines_by_order_id(self, order_id: int) -> List[Dict[str, Any]]:
        """Retrieve all line, shipping, fee, and coupon rows for an order.

        Args:
            order_id: Order ID associated with the item rows.

        Returns:
            The matching order-item records, or an empty list if none exist.

        Raises:
            ValueError: If ``order_id`` is not a positive integer.
            Exception: If the database query fails.
        """
        self._validate_positive_id(order_id, "order ID")

        sql = (
            f"SELECT * FROM {self.order_items_table} "
            "WHERE order_id = :order_id ORDER BY order_item_id ASC;"
        )
        params = {"order_id": order_id}

        try:
            results = self.db_helper.execute_select(sql, params)
            if not results:
                logger.info("No order items found for order ID=%s", order_id)
            else:
                logger.debug(
                    "Retrieved %d order item(s) for order ID=%s",
                    len(results),
                    order_id,
                )
            return results
        except Exception:
            logger.exception("Error retrieving order items for order ID=%s", order_id)
            raise

    def get_order_metadata(self, order_id: int) -> Dict[str, Any]:
        """Retrieve Order metadata as a mapping from key to value.

        Legacy storage reads ``wp_postmeta``. HPOS reads ``wc_orders_meta`` and
        adds canonical aliases for core order properties that HPOS stores in
        order and operational-data columns rather than metadata rows. When a
        key occurs more than once, the row with the greatest metadata ID is
        retained.

        Args:
            order_id: Order ID used by the active order store.

        Returns:
            A mapping of metadata keys to their stored values. Returns an empty
            mapping if no metadata exists.

        Raises:
            ValueError: If ``order_id`` is not a positive integer.
            Exception: If the database query fails.
        """
        self._validate_positive_id(order_id, "order ID")

        try:
            if self.hpos_enabled:
                sql = (
                    f"SELECT meta_key, meta_value FROM {self.hpos_order_meta_table} "
                    "WHERE order_id = :order_id ORDER BY id ASC;"
                )
                results = self.db_helper.execute_select(
                    sql,
                    {"order_id": order_id},
                )
            else:
                sql = (
                    f"SELECT meta_key, meta_value FROM {self.postmeta_table} "
                    "WHERE post_id = :order_id ORDER BY meta_id ASC;"
                )
                results = self.db_helper.execute_select(
                    sql,
                    {"order_id": order_id},
                )

            metadata = {
                row["meta_key"]: row["meta_value"]
                for row in results
                if row.get("meta_key") is not None
            }

            if self.hpos_enabled:
                order = self._get_hpos_order_by_id(order_id)
                if order is not None:
                    metadata.update(
                        {
                            key: order[key]
                            for key in self.HPOS_METADATA_KEYS
                            if order.get(key) is not None
                        }
                    )

            logger.debug(
                "Retrieved %d metadata value(s) for order ID=%s from %s storage",
                len(metadata),
                order_id,
                "HPOS" if self.hpos_enabled else "legacy",
            )
            return metadata
        except Exception:
            logger.exception("Error retrieving metadata for order ID=%s", order_id)
            raise

    def get_order_items_details(self, order_item_id: int) -> Dict[str, Any]:
        """Retrieve metadata for one order item as a key-to-value mapping.

        Args:
            order_item_id: Primary key of the WooCommerce order-item row.

        Returns:
            The item's metadata, or an empty mapping if no metadata exists.

        Raises:
            ValueError: If ``order_item_id`` is not a positive integer.
            Exception: If the database query fails.
        """
        self._validate_positive_id(order_item_id, "order item ID")

        sql = (
            f"SELECT meta_key, meta_value FROM {self.order_itemmeta_table} "
            "WHERE order_item_id = :order_item_id ORDER BY meta_id ASC;"
        )
        params = {"order_item_id": order_item_id}

        try:
            results = self.db_helper.execute_select(sql, params)
            details = {
                row["meta_key"]: row["meta_value"]
                for row in results
                if row.get("meta_key") is not None
            }
            if not details:
                logger.info("No metadata found for order item ID=%s", order_item_id)
            else:
                logger.debug(
                    "Retrieved %d metadata value(s) for order item ID=%s",
                    len(details),
                    order_item_id,
                )
            return details
        except Exception:
            logger.exception(
                "Error retrieving metadata for order item ID=%s", order_item_id
            )
            raise

    # ------------------------------------------------------------------
    # Write order-item metadata
    # ------------------------------------------------------------------

    def insert_order_item_meta(
        self, order_item_id: int, meta_key: str, meta_value: Any
    ) -> None:
        """Insert one metadata value for an order item.

        Args:
            order_item_id: Primary key of the order-item row.
            meta_key: Non-empty metadata key.
            meta_value: String or integer value to store.

        Raises:
            ValueError: If an argument has an unsupported value or type.
            Exception: If the database insert fails.
        """
        self._validate_positive_id(order_item_id, "order item ID")
        self._validate_meta_key(meta_key)
        if not isinstance(meta_value, (str, int)):
            raise ValueError("Invalid meta_value. Must be a string or integer.")

        sql = (
            f"INSERT INTO {self.order_itemmeta_table} "
            "(order_item_id, meta_key, meta_value) "
            "VALUES (:order_item_id, :meta_key, :meta_value);"
        )
        params = {
            "order_item_id": order_item_id,
            "meta_key": meta_key.strip(),
            "meta_value": meta_value,
        }

        try:
            self.db_helper.execute_sql(sql, params)
            logger.info(
                "Inserted metadata key '%s' for order item ID=%s",
                meta_key,
                order_item_id,
            )
        except Exception:
            logger.exception(
                "Error inserting metadata for order item ID=%s key=%s",
                order_item_id,
                meta_key,
            )
            raise

    def update_order_item_meta(
        self, order_item_id: int, meta_key: str, new_value: Any
    ) -> None:
        """Update an existing metadata value for an order item.

        Args:
            order_item_id: Primary key of the order-item row.
            meta_key: Non-empty metadata key to update.
            new_value: String or integer value to store.

        Raises:
            ValueError: If an argument has an unsupported value or type.
            Exception: If the database update fails.
        """
        self._validate_positive_id(order_item_id, "order item ID")
        self._validate_meta_key(meta_key)
        if not isinstance(new_value, (str, int)):
            raise ValueError("Invalid new_value. Must be a string or integer.")

        sql = (
            f"UPDATE {self.order_itemmeta_table} SET meta_value = :new_value "
            "WHERE order_item_id = :order_item_id AND meta_key = :meta_key;"
        )
        params = {
            "new_value": new_value,
            "order_item_id": order_item_id,
            "meta_key": meta_key.strip(),
        }

        try:
            self.db_helper.execute_sql(sql, params)
            logger.info(
                "Updated metadata key '%s' for order item ID=%s",
                meta_key,
                order_item_id,
            )
        except Exception:
            logger.exception(
                "Error updating metadata for order item ID=%s key=%s",
                order_item_id,
                meta_key,
            )
            raise

    def delete_order_item_meta(self, order_item_id: int, meta_key: str) -> None:
        """Delete metadata rows matching a key for an order item.

        Args:
            order_item_id: Primary key of the order-item row.
            meta_key: Non-empty metadata key to delete.

        Raises:
            ValueError: If ``order_item_id`` or ``meta_key`` is invalid.
            Exception: If the database delete fails.
        """
        self._validate_positive_id(order_item_id, "order item ID")
        self._validate_meta_key(meta_key)

        sql = (
            f"DELETE FROM {self.order_itemmeta_table} "
            "WHERE order_item_id = :order_item_id AND meta_key = :meta_key;"
        )
        params = {
            "order_item_id": order_item_id,
            "meta_key": meta_key.strip(),
        }

        try:
            self.db_helper.execute_sql(sql, params)
            logger.info(
                "Deleted metadata key '%s' for order item ID=%s",
                meta_key,
                order_item_id,
            )
        except Exception:
            logger.exception(
                "Error deleting metadata for order item ID=%s key=%s",
                order_item_id,
                meta_key,
            )
            raise


# Preserve the previous class name for any existing imports.
OrdersDao = OrdersDAO


__all__ = ["OrdersDAO", "OrdersDao"]
