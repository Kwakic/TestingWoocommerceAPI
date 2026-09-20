from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from EcommerceAPI.src.utils.db_utility import DBUtility


logger = logging.getLogger(__name__)


class CouponsDAO(object):
    """
    Data Access Object for WooCommerce coupons.

    WooCommerce coupons are stored as posts with:
        post_type = 'shop_coupon'

    Coupon-specific attributes are stored in postmeta.

    Responsibilities:
    -----------------
    ✔ Direct database queries via DBUtility
    ✔ Parameterized SQL
    ✔ Return database records
    ✔ Validate DAO method inputs

    Non-responsibilities:
    ---------------------
    ✘ No HTTP calls
    ✘ No API interaction
    ✘ No business logic
    ✘ No assertions
    ✘ No Pydantic/schema validation
    ✘ No test/fixture logic
    """

    def __init__(self):
        """Initialize DB connection and table references."""
        self.db_helper = DBUtility()

        self.posts_table = (
            f"{self.db_helper.database}.{self.db_helper.table_prefix}posts"
        )

        self.postmeta_table = (
            f"{self.db_helper.database}.{self.db_helper.table_prefix}postmeta"
        )

        logger.debug(
            "🗄️ CouponsDAO initialized: posts=%s, postmeta=%s",
            self.posts_table,
            self.postmeta_table,
        )

    # ------------------------------------------------------------------
    # READ (SINGLE)
    # ------------------------------------------------------------------

    def get_coupon_by_id(
        self,
        coupon_id: int,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single WooCommerce coupon by ID.

        Args:
            coupon_id:
                Coupon ID (post ID in wp_posts).

        Returns:
            dict:
                Coupon post record.

            None:
                If the coupon does not exist.
        """
        if not isinstance(coupon_id, int) or coupon_id <= 0:
            raise ValueError(
                f"Invalid coupon ID: {coupon_id}. " "Must be a positive integer."
            )

        sql = (
            f"SELECT * FROM {self.posts_table} "
            f"WHERE ID = :coupon_id "
            f"AND post_type = 'shop_coupon' "
            f"LIMIT 1;"
        )

        params = {"coupon_id": coupon_id}

        try:
            results = self.db_helper.execute_select(sql, params)

            if not results:
                logger.info(
                    "🔍 No coupon found for ID=%s",
                    coupon_id,
                )
                return None

            coupon = results[0]

            logger.debug(
                "ℹ️ Found coupon for ID=%s: %s",
                coupon_id,
                coupon,
            )

            return coupon

        except Exception as e:
            logger.exception(
                "❌ Error retrieving coupon by ID %s: %s",
                coupon_id,
                e,
            )
            raise

    # ------------------------------------------------------------------
    # READ (BY CODE)
    # ------------------------------------------------------------------

    def get_coupon_by_code(
        self,
        code: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single WooCommerce coupon by coupon code.

        WooCommerce stores the coupon code as the post title.

        Args:
            code:
                Coupon code.

        Returns:
            dict:
                Coupon post record.

            None:
                If the coupon does not exist.
        """
        if not isinstance(code, str) or not code.strip():
            raise ValueError("Invalid coupon code. " "Must be a non-empty string.")

        sql = (
            f"SELECT * FROM {self.posts_table} "
            f"WHERE post_type = 'shop_coupon' "
            f"AND post_title = :code "
            f"LIMIT 1;"
        )

        params = {"code": code.strip()}

        try:
            results = self.db_helper.execute_select(sql, params)

            coupon = results[0] if results else None

            if coupon:
                logger.debug(
                    "ℹ️ Found coupon with code=%s",
                    code,
                )
            else:
                logger.info(
                    "🔍 No coupon found with code=%s",
                    code,
                )

            return coupon

        except Exception as e:
            logger.exception(
                "❌ Error retrieving coupon by code %s: %s",
                code,
                e,
            )
            raise

    # ------------------------------------------------------------------
    # READ (MULTIPLE)
    # ------------------------------------------------------------------

    def get_all_coupons(
        self,
        limit: int = 5000,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve WooCommerce coupons.

        Args:
            limit:
                Maximum number of records to fetch.

        Returns:
            list:
                Coupon post records.
                Empty list if no coupons exist.
        """
        if not isinstance(limit, int) or limit <= 0:
            raise ValueError("Limit must be a positive integer.")

        sql = (
            f"SELECT * FROM {self.posts_table} "
            f"WHERE post_type = 'shop_coupon' "
            f"ORDER BY post_date DESC "
            f"LIMIT :limit;"
        )

        params = {"limit": limit}

        try:
            results = self.db_helper.execute_select(
                sql,
                params,
            )

            logger.info(
                "✅ Retrieved %d coupon(s)",
                len(results),
            )

            return results

        except Exception as e:
            logger.exception(
                "❌ Error retrieving coupons: %s",
                e,
            )
            raise

    # ------------------------------------------------------------------
    # METADATA
    # ------------------------------------------------------------------

    def get_coupon_meta(
        self,
        coupon_id: int,
        meta_key: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve coupon metadata by key.

        Examples of WooCommerce coupon metadata include:
            discount_type
            coupon_amount
            usage_count
            usage_limit
            usage_limit_per_user
            free_shipping
            minimum_amount
            maximum_amount

        Args:
            coupon_id:
                Coupon ID.

            meta_key:
                WooCommerce coupon metadata key.

        Returns:
            dict:
                Metadata record.

            None:
                If the metadata does not exist.
        """
        if not isinstance(coupon_id, int) or coupon_id <= 0:
            raise ValueError(
                f"Invalid coupon ID: {coupon_id}. " "Must be a positive integer."
            )

        if not isinstance(meta_key, str) or not meta_key.strip():
            raise ValueError("Invalid meta_key. " "Must be a non-empty string.")

        sql = (
            f"SELECT * FROM {self.postmeta_table} "
            f"WHERE post_id = :coupon_id "
            f"AND meta_key = :meta_key "
            f"LIMIT 1;"
        )

        params = {
            "coupon_id": coupon_id,
            "meta_key": meta_key.strip(),
        }

        try:
            results = self.db_helper.execute_select(
                sql,
                params,
            )

            meta = results[0] if results else None

            if meta:
                logger.debug(
                    "ℹ️ Found coupon metadata: coupon=%s key=%s",
                    coupon_id,
                    meta_key,
                )
            else:
                logger.debug(
                    "🔍 No coupon metadata found: coupon=%s key=%s",
                    coupon_id,
                    meta_key,
                )

            return meta

        except Exception as e:
            logger.exception(
                "❌ Error retrieving coupon metadata: " "coupon=%s key=%s: %s",
                coupon_id,
                meta_key,
                e,
            )
            raise

    def get_coupon_metadata(
        self,
        coupon_id: int,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Retrieve all metadata for a WooCommerce coupon.

        Returns:
            dict:
                Metadata records keyed by meta_key.
                Example:
                {
                    "discount_type": {"meta_value": "percent", ...},
                    "coupon_amount": {"meta_value": "50.00", ...},
                }
        """
        if not isinstance(coupon_id, int) or coupon_id <= 0:
            raise ValueError(
                f"Invalid coupon ID: {coupon_id}. " "Must be a positive integer."
            )

        sql = (
            f"SELECT * FROM {self.postmeta_table} "
            f"WHERE post_id = :coupon_id "
            f"ORDER BY meta_id ASC;"
        )
        params = {"coupon_id": coupon_id}

        try:
            results = self.db_helper.execute_select(sql, params)
            metadata = {row["meta_key"]: row for row in results if row.get("meta_key")}

            logger.info(
                "✅ Retrieved %d metadata record(s) for coupon=%s",
                len(metadata),
                coupon_id,
            )
            return metadata

        except Exception as e:
            logger.exception(
                "❌ Error retrieving coupon metadata: coupon=%s: %s",
                coupon_id,
                e,
            )
            raise
