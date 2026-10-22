"""
Order Database Validation Layer

This module contains pure validators that compare a validated Orders API
model with WooCommerce database records retrieved by the DAO.

Responsibilities
----------------
• Confirm the Order record and its product line items exist in the database
• Compare API identity, status, metadata, totals, and line-item values with
  their corresponding database values
• Normalize equivalent WooCommerce representations before comparison

Important design rule:
These validators ONLY compare supplied data.

They must NOT:
    - call the Orders API
    - query the database
    - create test data
    - orchestrate workflows

Data fetching is handled by:
    Tests or Helpers using ``OrdersDAO``.

Architecture
------------
TEST / HELPER
      ↓
OrdersDAO → Database records
      ↓
OrderModel + database records
      ↓
ORDER DB VALIDATORS

assert_order_matches_db → Order and line-item consistency validation
                         (INTEGRATION)

"""

from __future__ import annotations

import logging
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Dict, List, Mapping

from EcommerceAPI.src.entities.orders.models.order_model import OrderModel


logger = logging.getLogger(__name__)


def assert_order_matches_db(
    order: OrderModel,
    db_order: Dict[str, Any],
    db_order_meta: Dict[str, Any],
    db_order_lines: List[Dict[str, Any]],
    db_order_item_meta: Mapping[Any, Dict[str, Any]],
) -> None:
    """Assert that a validated API order matches its WooCommerce DB records.

    This is a pure comparison function. The caller retrieves each database
    record with ``OrdersDAO`` and passes the results here. For product line
    items, ``db_order_item_meta`` is keyed by ``order_item_id`` and contains
    the mapping returned by ``OrdersDAO.get_order_items_details``.

    The validator checks the order record, core order metadata, and product
    line items. Shipping, fee, tax, and coupon rows are stored separately from
    the API's ``line_items`` collection and are not compared by this function.

    Args:
        order: Order response already parsed as an ``OrderModel``.
        db_order: Order post row returned by ``OrdersDAO.get_order_by_id``.
        db_order_meta: Order metadata mapping returned by
            ``OrdersDAO.get_order_metadata``.
        db_order_lines: Order item rows returned by
            ``OrdersDAO.get_order_lines_by_order_id``.
        db_order_item_meta: Item metadata mappings keyed by order item ID.

    Raises:
        AssertionError: If a required record is missing or a compared value
            differs between the API response and the database.
    """
    assert db_order, f"No DB order record found for order ID={order.id}"
    assert db_order_meta is not None, f"No DB metadata returned for order ID={order.id}"
    assert (
        db_order_lines is not None
    ), f"No DB order-item rows returned for order ID={order.id}"
    assert (
        db_order_item_meta is not None
    ), f"No order-item metadata mapping returned for order ID={order.id}"

    _assert_order_record(order, db_order)
    _assert_order_metadata(order, db_order_meta)
    _assert_order_line_items(order, db_order_lines, db_order_item_meta)

    logger.info(
        "API order matches DB records: ID=%s status=%s",
        order.id,
        order.status,
    )


def _assert_order_record(order: OrderModel, db_order: Dict[str, Any]) -> None:
    """Compare API identity and status with the DAO's normalized order row.

    ``OrdersDAO`` presents the same validator-facing keys regardless of
    whether WooCommerce uses the legacy posts table or HPOS tables.
    """
    assert _normalize_identifier(db_order["ID"]) == _normalize_identifier(
        order.id
    ), f"Order ID mismatch. DB='{db_order['ID']}' API='{order.id}'"

    assert db_order["post_type"] == "shop_order", (
        f"Unexpected post type for order ID={order.id}: " f"'{db_order['post_type']}'"
    )

    db_status = _normalize_order_status(db_order["post_status"])
    assert db_status == order.status, (
        f"Order status mismatch. DB='{db_order['post_status']}' "
        f"API='{order.status}'"
    )

    # The DAO maps the customer note to this canonical field for both stores.
    if order.customer_note is not None:
        db_customer_note = db_order["post_excerpt"]
        assert _normalize_text(db_customer_note) == _normalize_text(
            order.customer_note
        ), (
            "Order customer note mismatch. "
            f"DB='{db_customer_note}' API='{order.customer_note}'"
        )


def _assert_order_metadata(
    order: OrderModel,
    db_order_meta: Dict[str, Any],
) -> None:
    """Compare API order fields with normalized database metadata.

    ``OrdersDAO`` reads legacy ``wp_postmeta`` values or HPOS metadata and
    maps HPOS order/operational columns to the corresponding legacy metadata
    keys expected below.
    """
    required_mappings = (
        ("_order_key", order.order_key, _normalize_text),
        ("_customer_user", order.customer_id, _normalize_identifier),
        ("_order_currency", order.currency, _normalize_text),
    )
    for meta_key, api_value, normalizer in required_mappings:
        _assert_meta_value(
            db_order_meta,
            meta_key,
            api_value,
            normalizer,
        )

    optional_mappings = (
        ("_payment_method", order.payment_method, _normalize_text, False),
        ("_payment_method_title", order.payment_method_title, _normalize_text, False),
        ("_transaction_id", order.transaction_id, _normalize_text, False),
        ("_created_via", order.created_via, _normalize_text, False),
        ("_order_version", order.version, _normalize_text, False),
        ("_customer_ip_address", order.customer_ip_address, _normalize_text, False),
        ("_customer_user_agent", order.customer_user_agent, _normalize_text, False),
        ("_cart_discount", order.discount_total, _normalize_decimal, True),
        ("_cart_discount_tax", order.discount_tax, _normalize_decimal, True),
        ("_order_shipping", order.shipping_total, _normalize_decimal, True),
        ("_order_shipping_tax", order.shipping_tax, _normalize_decimal, True),
        ("_order_tax", order.cart_tax, _normalize_decimal, True),
        ("_order_total", order.total, _normalize_decimal, True),
    )
    for meta_key, api_value, normalizer, allow_missing_zero in optional_mappings:
        _assert_meta_value(
            db_order_meta,
            meta_key,
            api_value,
            normalizer,
            allow_missing_zero=allow_missing_zero,
        )

    # The REST field is the combined order tax. WooCommerce stores cart and
    # shipping tax separately in _order_tax and _order_shipping_tax.
    if order.total_tax is not None:
        cart_tax = db_order_meta.get("_order_tax", "0")
        shipping_tax = db_order_meta.get("_order_shipping_tax", "0")
        db_total_tax = _normalize_decimal(cart_tax) + _normalize_decimal(shipping_tax)
        api_total_tax = _normalize_decimal(order.total_tax)
        assert db_total_tax == api_total_tax, (
            "Order total tax mismatch. "
            f"DB='{cart_tax} + {shipping_tax}' API='{order.total_tax}'"
        )


def _assert_order_line_items(
    order: OrderModel,
    db_order_lines: List[Dict[str, Any]],
    db_order_item_meta: Mapping[Any, Dict[str, Any]],
) -> None:
    """Compare API product line items with WooCommerce order-item records."""
    db_product_lines = {
        _normalize_identifier(row["order_item_id"]): row
        for row in db_order_lines
        if row["order_item_type"] == "line_item"
    }
    api_line_ids = {_normalize_identifier(item.id) for item in order.line_items}

    assert len(api_line_ids) == len(
        order.line_items
    ), f"Duplicate API line-item IDs in order ID={order.id}"
    assert len(db_product_lines) == sum(
        row["order_item_type"] == "line_item" for row in db_order_lines
    ), f"Duplicate DB line-item IDs in order ID={order.id}"
    assert api_line_ids == set(db_product_lines), (
        f"Order line-item IDs mismatch. "
        f"DB={sorted(db_product_lines)} API={sorted(api_line_ids)}"
    )

    for api_line in order.line_items:
        line_id = _normalize_identifier(api_line.id)
        db_line = db_product_lines[line_id]
        db_line_meta = _get_line_item_metadata(db_order_item_meta, line_id)

        assert _normalize_text(db_line["order_item_name"]) == _normalize_text(
            api_line.name
        ), (
            f"Order line-item name mismatch for ID={api_line.id}. "
            f"DB='{db_line['order_item_name']}' API='{api_line.name}'"
        )

        _assert_meta_value(
            db_line_meta,
            "_product_id",
            api_line.product_id,
            _normalize_identifier,
            context=f"order line item ID={api_line.id}",
        )
        _assert_meta_value(
            db_line_meta,
            "_qty",
            api_line.quantity,
            _normalize_decimal,
            context=f"order line item ID={api_line.id}",
        )
        _assert_meta_value(
            db_line_meta,
            "_variation_id",
            api_line.variation_id,
            _normalize_identifier,
            allow_missing_zero=True,
            context=f"order line item ID={api_line.id}",
        )

        line_meta_mappings = (
            ("_line_subtotal", api_line.subtotal),
            ("_line_subtotal_tax", api_line.subtotal_tax),
            ("_line_total", api_line.total),
            ("_line_tax", api_line.total_tax),
        )
        for meta_key, api_value in line_meta_mappings:
            _assert_meta_value(
                db_line_meta,
                meta_key,
                api_value,
                _normalize_decimal,
                allow_missing_zero=True,
                context=f"order line item ID={api_line.id}",
            )


def _get_line_item_metadata(
    db_order_item_meta: Mapping[Any, Dict[str, Any]],
    line_id: int,
) -> Dict[str, Any]:
    """Return metadata for a line item, accepting integer or string keys."""
    metadata = db_order_item_meta.get(line_id)
    if metadata is None:
        metadata = db_order_item_meta.get(str(line_id))  # type: ignore[arg-type]

    assert (
        metadata is not None
    ), f"No DB metadata found for order line item ID={line_id}"
    return metadata


def _assert_meta_value(
    db_metadata: Dict[str, Any],
    meta_key: str,
    api_value: Any,
    normalizer: Callable[[Any], Any],
    *,
    allow_missing_zero: bool = False,
    context: str = "order",
) -> None:
    """Compare one API value with its WooCommerce metadata value."""
    if api_value is None:
        return

    if meta_key not in db_metadata:
        if allow_missing_zero and normalizer(api_value) == normalizer(0):
            return
        assert False, f"Missing DB metadata '{meta_key}' for {context}"

    db_value = db_metadata[meta_key]
    assert normalizer(db_value) == normalizer(api_value), (
        f"Order metadata mismatch for '{meta_key}' ({context}). "
        f"DB='{db_value}' API='{api_value}'"
    )


def _normalize_order_status(value: Any) -> str:
    """Remove WooCommerce's database-only ``wc-`` status prefix."""
    status = _normalize_text(value)
    return status[3:] if status.startswith("wc-") else status


def _normalize_text(value: Any) -> str:
    """Normalize text values without changing their case or meaning."""
    return str(value).strip()


def _normalize_identifier(value: Any) -> Any:
    """Normalize numeric IDs stored as integers or numeric strings."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return str(value).strip()


def _normalize_decimal(value: Any) -> Decimal:
    """Normalize equivalent monetary values such as ``'4.00'`` and ``4``."""
    try:
        return Decimal(str(value)).normalize()
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise AssertionError(f"Expected a numeric order value, got {value!r}") from exc


__all__ = ["assert_order_matches_db"]
