from __future__ import annotations

import logging
from typing import Any, Dict

from EcommerceAPI.src.coupons.models.coupon_model import CouponModel

logger = logging.getLogger(__name__)


# ================================================================
# DB VALIDATION
# ================================================================


def assert_coupon_matches_db(
    coupon: CouponModel,
    db_coupon: Dict[str, Any],
    db_coupon_meta: Dict[str, Dict[str, Any]],
) -> None:
    """
    Validate that the API coupon matches the corresponding
    WooCommerce database records.

    API -> DB mappings validated:
        coupon.id                  -> wp_posts.ID
        coupon.code                -> wp_posts.post_title
        coupon.discount_type       -> postmeta.discount_type
        coupon.amount              -> postmeta.coupon_amount
        coupon.usage_count         -> postmeta.usage_count
        coupon.usage_limit         -> postmeta.usage_limit
        coupon.usage_limit_per_user -> postmeta.usage_limit_per_user
        coupon.limit_usage_to_x_items -> postmeta.limit_usage_to_x_items
        coupon.free_shipping       -> postmeta.free_shipping
        coupon.minimum_amount      -> postmeta.minimum_amount
        coupon.maximum_amount      -> postmeta.maximum_amount

    The validator only compares supplied data. Database access belongs
    to CouponsDAO.
    """
    assert db_coupon, f"❌ No DB record found for coupon ID={coupon.id}"

    assert (
        db_coupon_meta is not None
    ), f"❌ No DB metadata returned for coupon ID={coupon.id}"

    assert str(db_coupon["ID"]) == str(coupon.id), (
        f"Coupon ID mismatch. " f"DB='{db_coupon['ID']}' API='{coupon.id}'"
    )

    assert db_coupon["post_title"] == coupon.code, (
        f"Coupon code mismatch. " f"DB='{db_coupon['post_title']}' API='{coupon.code}'"
    )

    meta_mappings = {
        "discount_type": coupon.discount_type,
        "coupon_amount": coupon.amount,
        "usage_count": coupon.usage_count,
        "usage_limit": coupon.usage_limit,
        "usage_limit_per_user": coupon.usage_limit_per_user,
        "limit_usage_to_x_items": coupon.limit_usage_to_x_items,
        "free_shipping": coupon.free_shipping,
        "minimum_amount": coupon.minimum_amount,
        "maximum_amount": coupon.maximum_amount,
    }

    for meta_key, api_value in meta_mappings.items():
        _assert_meta_value(db_coupon_meta, meta_key, api_value)

    logger.info(
        "✅ API coupon matches DB records: ID=%s code=%s",
        coupon.id,
        coupon.code,
    )


def _assert_meta_value(
    db_coupon_meta: Dict[str, Dict[str, Any]],
    meta_key: str,
    api_value: Any,
) -> None:
    """Compare one API coupon field with its wp_postmeta value."""
    if api_value is None:
        return

    assert meta_key in db_coupon_meta, f"Missing coupon metadata '{meta_key}' in DB"

    db_value = db_coupon_meta[meta_key].get("meta_value")

    assert _normalize_db_value(db_value) == _normalize_api_value(api_value), (
        f"Coupon metadata mismatch for '{meta_key}'. "
        f"DB='{db_value}' API='{api_value}'"
    )


def _normalize_db_value(value: Any) -> Any:
    if value is None:
        return None
    return value.strip() if isinstance(value, str) else str(value).strip()


def _normalize_api_value(value: Any) -> str:
    if isinstance(value, bool):
        return "1" if value else "0"
    return str(value).strip()
