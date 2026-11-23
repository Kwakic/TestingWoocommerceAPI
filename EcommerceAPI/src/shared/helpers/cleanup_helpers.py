from collections import Counter
from functools import partial
from typing import Callable, Iterable, List, Optional, Any, Set, Dict
import logging as logger

from EcommerceAPI.src.clients.api_client import APIClient


# NOTE: we intentionally avoid importing APIClient here at module import time because
# creating network/HTTP client instances eagerly during import can cause side-effects,
# slow test collection, and makes mocking harder. Tests should provide the api client (fixture)
# and bind cleanup functions explicitly.
_default_api_client: Optional[APIClient] = None


def set_default_api_client(api_client: Any) -> None:
    """
    Set a default APIClient instance for module-level helpers.

    Use case:
      - Call this once (e.g., from conftest.py) to expose the legacy module-level cleanup_* helpers.

    Example (conftest.py):
        from ssqaapitest.src.helpers.cleanup_helpers import set_default_api_client
        set_default_api_client(api_client)

    CHANGED: This makes the dependency explicit instead of instantiating an API client here.
    """
    global _default_api_client
    _default_api_client = api_client


def cleanup_items(
    resource_type: str,
    resource_ids: Iterable[Any],
    delete_method: Callable[..., Any],
    label: Optional[str] = None,
    summary_log: Optional[List[str]] = None,
    total_created: int = 0,
    skip_message: Optional[str] = None,
    already_deleted_ids: Optional[Set[Any]] = None,
    *,
    outcomes: Optional[Counter[str]] = None,
) -> Set[Any]:
    """
    Generic teardown cleanup function for deleting test-created resources.

    🔧 Usage:
        Called from conftest.py fixture to clean up any WooCommerce resources
        created during the test run (e.g., customers, orders).

    Behavior:
      - Deduplicates IDs within the provided list.
      - Skips IDs that were already deleted during the test run (already_deleted_ids).
      - Attempts deletion via the provided delete_method and logs outcomes.
      - Appends a human-readable summary to summary_log if provided.

    Purpose:
        - Provide a single, well-documented cleanup_items(...) function that performs robust teardown logic.
        - Avoid creating an APIClient instance at module import time (so tests / CI can control instantiation
        via fixtures).
        - Provide helpers to create pre-bound cleanup callables from an APIClient instance (factory-style).
        - Offer a safe module-level fallback that must be explicitly initialized (so existing code that expects
          cleanup_orders etc. can keep working if you wire it in conftest).

    Args:
        resource_type: API resource path or logical name (e.g., "customers", "orders").
        resource_ids: Iterable of resource identifiers to attempt deletion on.
        label: Friendly singular label for logs (e.g., "customers"). Defaults to resource_type.rstrip("s").
        summary_log: Optional list to which a summary line will be appended.
        total_created: Number of distinct IDs registered in this fixture (for summary).
        skip_message: Optional message used when there is nothing to cleanup.
        already_deleted_ids: Set of IDs that were already removed during test execution.
        outcomes: Optional session reporting counter for this entity's teardown outcomes.
        delete_method: Callable used to perform deletions.
                       Expected to accept the endpoint or path and optional params.
                       Returns a response with an HTTP status_code (e.g. api_client.delete).
                       The function will be called like:
                         delete_method(f"{resource_type}/{resource_id}", params={"force": True})
                       (This preserves previous behaviour.)

    Returns:
        IDs for which the API confirmed deletion (HTTP 200 or 204).
    """

    label = label or resource_type.rstrip("s")
    deleted_ids: Set[Any] = set()
    skipped = failed = manually_deleted = not_found = 0
    seen_ids: Set[Any] = set()
    already_deleted_ids = already_deleted_ids or set()

    resource_ids_list = (
        list(resource_ids) if not isinstance(resource_ids, list) else resource_ids
    )

    if not resource_ids_list:
        msg = skip_message or f"🧹 Nothing to clean up for {label}(s)."
        logger.info(msg)
        if summary_log is not None:
            summary_log.append(f"{label}: 0 deleted ({total_created} registered)")
        return deleted_ids

    logger.info(f"🧹 Cleaning up {label}(s)... ({len(resource_ids_list)} queued)")

    for resource_id in resource_ids_list:
        # De-duplicate within the same run
        if resource_id in seen_ids:
            logger.debug(
                f"ℹ️ {label.capitalize()} ID {resource_id} already queued for cleanup. Skipping duplicate."
            )
            skipped += 1
            continue

        seen_ids.add(resource_id)

        # Skip if test already deleted it manually
        if resource_id in already_deleted_ids:
            logger.debug(
                f"↪️ Skipping {label} ID {resource_id} — already deleted during test execution."
            )
            manually_deleted += 1
            continue

        try:
            logger.debug(f"🔄 Deleting {label} ID: {resource_id}")
            # Keep the same call shape as before for compatibility:
            # callers typically pass a bound APIClient.delete method which accepts an endpoint string and params
            response = delete_method(
                f"{resource_type}/{resource_id}", params={"force": True}
            )
        except Exception as e:
            logger.error("Failed to delete %s ID %s: %s", label, resource_id, e)
            failed += 1
            continue

        status = getattr(response, "status_code", None)
        if status in (200, 204):
            deleted_ids.add(resource_id)
            logger.info("Deleted %s ID: %s", label, resource_id)
        elif status == 404:
            logger.warning("DELETE %s/%s returned HTTP 404", resource_type, resource_id)
            not_found += 1
        else:
            logger.error(
                "Unconfirmed DELETE %s/%s (status: %s)",
                resource_type,
                resource_id,
                status,
            )
            failed += 1

    if outcomes is not None:
        outcomes.update(
            deleted=len(deleted_ids),
            missing=not_found,
            failed=failed,
            skipped=manually_deleted,
        )

    summary_parts = [f"{len(deleted_ids)} deleted"]
    if not_found:
        summary_parts.append(f"{not_found} not found (HTTP 404)")
    if manually_deleted:
        summary_parts.append(
            f"{manually_deleted} skipped (already deleted during test execution)"
        )
    if skipped:
        summary_parts.append(f"{skipped} skipped (duplicate)")
    if failed:
        summary_parts.append(f"{failed} failed")

    summary = f"{label}: {', '.join(summary_parts)} ({total_created} registered)"

    if summary_log is not None:
        summary_log.append(summary)
    else:
        logger.info(summary)
    return deleted_ids


# -------------------------------------------------
# Factory helpers — create pre-bound cleanup callables
# -------------------------------------------------
def make_cleanup_partial(
    api_client: APIClient, resource_type: str, label: Optional[str] = None
) -> Callable[..., Set[Any]]:
    """
    Create a pre-bound cleanup callable for a specific resource type using the provided API client.

    Args:
        api_client: APIClient-like object exposing `.delete(...)`
        resource_type: The resource path (e.g., "customers").
        label: Optional friendly label (e.g., "customers").

    Returns:
        Callable that accepts the same args as cleanup_items except "delete_method" and "resource_type".
    """
    return partial(
        cleanup_items, resource_type, delete_method=api_client.delete, label=label
    )


def make_all_cleanups(api_client: Any) -> Dict[str, Callable[..., Set[Any]]]:
    """
    Convenience factory to build a small dictionary of common cleanup callables bound to the given API client.

    Example:
        cleanups = make_all_cleanups(api_client)
        cleanups["customers"](resource_ids, summary_log=my_log)
    """
    return {
        "orders": make_cleanup_partial(api_client, "orders", label="order"),
        "products": make_cleanup_partial(api_client, "products", label="product"),
        "customers": make_cleanup_partial(api_client, "customers", label="customers"),
        "coupons": make_cleanup_partial(api_client, "coupons", label="coupon"),
    }


# -------------------------------------------------
# Optional: module-level helpers (explicit opt-in)
# -------------------------------------------------
# For backwards compatibility we provide module-level names (cleanup_orders, etc.), but they will raise a clear
# error if the default APIClient  is not set via `set_default_api_client(...)`.
#
# This prevents accidental network calls during import time while allowing a small migration path:
#   1) In conftest.py, after creating your api_client fixture, call:
#       from EcommerceAPI.src.helpers.cleanup_helpers import set_default_api_client
#       set_default_api_client(api_client)
#   2) Existing code that calls cleanup_orders(...) will keep working.


def _require_default_api_client() -> Any:
    if _default_api_client is None:
        raise RuntimeError(
            "Default APIClient is not set for cleanup_helpers. "
            "Either call make_cleanup_partial(api_client, ...) or "
            "set the default API client with set_default_api_client(api_client)"
        )
    return _default_api_client


# -------------------------------------------------
# 👇 Pre-bound helper functions for manual cleanup
# -------------------------------------------------
# Those are currently not used anywhere unless you manually call them elsewhere in your codebase.
# ✅ When are these useful?
#     If you want to manually clean up a specific type in a standalone test script or debug session
#     If you want to use cleanup_helpers.py independently of conftest.py


def cleanup_orders(resource_ids: Iterable[Any], **kwargs) -> None:
    api_client = _require_default_api_client()
    make_cleanup_partial(api_client, "orders", label="order")(resource_ids, **kwargs)


def cleanup_products(resource_ids: Iterable[Any], **kwargs) -> None:
    api_client = _require_default_api_client()
    make_cleanup_partial(api_client, "products", label="product")(
        resource_ids, **kwargs
    )


def cleanup_customers(resource_ids: Iterable[Any], **kwargs) -> None:
    api_client = _require_default_api_client()
    make_cleanup_partial(api_client, "customers", label="customers")(
        resource_ids, **kwargs
    )


def cleanup_coupons(resource_ids: Iterable[Any], **kwargs) -> None:
    api_client = _require_default_api_client()
    make_cleanup_partial(api_client, "coupons", label="coupon")(resource_ids, **kwargs)
