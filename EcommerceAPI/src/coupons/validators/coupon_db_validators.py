from __future__ import annotations

import logging
from decimal import Decimal, InvalidOperation
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

    The validator compares the API representation with the
    corresponding wp_posts and wp_postmeta values.
    """

    assert db_coupon, f"❌ No DB record found for coupon ID={coupon.id}"
    assert (
        db_coupon_meta is not None
    ), f"❌ No DB metadata returned for coupon ID={coupon.id}"

    # Validate the main coupon record stored in wp_posts.
    assert str(db_coupon["ID"]) == str(
        coupon.id
    ), f"Coupon ID mismatch. DB='{db_coupon['ID']}' API='{coupon.id}'"

    assert db_coupon["post_title"] == coupon.code, (
        f"Coupon code mismatch. " f"DB='{db_coupon['post_title']}' API='{coupon.code}'"
    )

    # API field -> WooCommerce postmeta key.
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
        _assert_meta_value(
            db_coupon_meta,
            meta_key,
            api_value,
        )

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

    # Optional API fields do not require a DB value.
    if api_value is None:
        return

    # WooCommerce may omit metadata rows for default values.
    if meta_key not in db_coupon_meta:
        assert _is_allowed_missing_metadata(
            meta_key, api_value
        ), f"Missing coupon metadata '{meta_key}' in DB"
        return

    db_value = db_coupon_meta[meta_key].get("meta_value")

    assert _normalize_value(db_value, meta_key) == _normalize_value(
        api_value,
        meta_key,
    ), (
        f"Coupon metadata mismatch for '{meta_key}'. "
        f"DB='{db_value}' API='{api_value}'"
    )


def _is_allowed_missing_metadata(
    meta_key: str,
    api_value: Any,
) -> bool:
    """
    Return True when WooCommerce is allowed to omit the metadata row.

    Currently this applies to the default zero values for
    minimum_amount and maximum_amount.
    """

    defaults = {
        "minimum_amount": "0",
        "maximum_amount": "0",
    }

    expected_default = defaults.get(meta_key)

    if expected_default is None:
        return False

    return _normalize_value(api_value, meta_key) == expected_default


def _normalize_value(
    value: Any,
    meta_key: str,
) -> str:
    """Normalize API and DB representations before comparison."""

    if meta_key == "free_shipping":
        return _normalize_boolean(value)

    if meta_key in {
        "coupon_amount",
        "minimum_amount",
        "maximum_amount",
    }:
        return _normalize_numeric(value)

    return str(value).strip()


def _normalize_boolean(value: Any) -> str:
    """Normalize common WooCommerce boolean representations."""

    if isinstance(value, bool):
        return "true" if value else "false"

    value = str(value).strip().lower()

    if value in {"1", "yes", "true", "on"}:
        return "true"

    if value in {"0", "no", "false", "off"}:
        return "false"

    return value


def _normalize_numeric(value: Any) -> str:
    """Normalize numeric values such as '0', '0.00' and '10.00'."""

    try:
        return format(Decimal(str(value)), "f").rstrip("0").rstrip(".") or "0"
    except (InvalidOperation, ValueError):
        return str(value).strip()
