"""
📦 Pagination Utility Module

Provides a generic utility function to paginate through WooCommerce API results.
Intended for use in test helpers like customers_helper, orders_helper, coupons_helper, etc.
"""

import logging
import time
from copy import deepcopy

from EcommerceAPI.src.utils.exceptions import UnexpectedStatusCodeError

logger = logging.getLogger(__name__)

# Status codes that should stop pagination immediately — retrying won't help.
# All 4xx EXCEPT 429: client errors (400, 401, 403, 404, 422, ...) are deterministic,
# so retrying the same request just wastes time. 429 (rate limit) is left out on
# purpose — APIClient already backs off on it, and a bit more waiting can still help.
DEFAULT_FAIL_FAST_STATUSES = frozenset(range(400, 500)) - {429}


class PaginationAbortedError(UnexpectedStatusCodeError):
    """
    Raised when pagination is stopped early due to an unrecoverable API error
    (fail-fast status, or a page that failed every retry).

    Inherits from UnexpectedStatusCodeError, so `response` / `response_json`
    are available for debugging — consistent with the rest of the framework.
    """


def paginate_all_results(
    api_client,
    endpoint,
    params=None,
    max_pages=1000,
    retries=3,
    retry_delay=1.0,
    fail_fast_statuses=DEFAULT_FAIL_FAST_STATUSES,
):
    """
    Generic pagination handler for WooCommerce-style endpoints with retry logic.

    🔧 Behavior:
        - Retries transient failures (network errors, 5xx, bad payloads) up to `retries` times per page.
        - Immediately aborts (no retries) on `fail_fast_statuses` (default: all 4xx except 429) —
          deterministic client errors (auth, permissions, bad params, not found, etc.) that a retry
          will never fix. 429 is excluded on purpose since it's a "try again later" signal.
        - Aborts pagination entirely if a page still fails after all retries are exhausted, instead of
          silently skipping to the next page.

    Args:
        api_client (APIClient): Utility class to perform authenticated requests.
        endpoint (str): API endpoint (e.g., 'customers', 'orders').
        params (dict, optional): Query parameters for filtering (e.g., per_page, created_after).
        max_pages (int): Maximum number of pages to fetch.
        retries (int): How many times to retry a failed page request.
        retry_delay (float): Delay (seconds) between retries.
        fail_fast_statuses (set[int]): HTTP status codes that abort pagination immediately
            instead of retrying. Defaults to all 4xx except 429.

    Returns:
        list: Aggregated list of all items fetched from the endpoint.

    Raises:
        PaginationAbortedError: If a fail-fast status is returned, or if a page still fails
            after all retries are exhausted.
    """
    logger.debug(f"🧰 Starting paginated fetch for '{endpoint}'")
    all_items = []
    params = deepcopy(params) if params else {}
    params.setdefault("per_page", 100)

    for i in range(1, max_pages + 1):
        params["page"] = i
        attempt = 0
        success = False
        response = None
        http_response = None

        while attempt < retries and not success:
            try:
                logger.debug(
                    f"📦 Fetching {endpoint} page {i} (attempt {attempt + 1}/{retries})"
                )
                http_response = api_client.get(endpoint, params=params)
                status_code = http_response.status_code

                # 🚨 Fail fast on deterministic client errors — retrying won't fix these
                if status_code in fail_fast_statuses:
                    raise PaginationAbortedError(
                        f"🚨 Pagination aborted for '{endpoint}' page={i}: "
                        f"got status {status_code}. This is a client error (4xx) — "
                        f"check credentials, permissions, or request params.",
                        response=http_response,
                        response_json=http_response.json,
                    )

                # ✅ Validate status code for pagination calls.
                # Explicit check, not `assert` — asserts get stripped under `python -O`
                # and raise a non-semantic AssertionError.
                if status_code != 200:
                    raise UnexpectedStatusCodeError(
                        f"❌ Pagination request failed for {endpoint} page={i}. "
                        f"Expected status 200, got {status_code}",
                        response=http_response,
                        response_json=http_response.json,
                    )

                logger.debug(
                    "📄 Pagination request OK: endpoint=%s page=%s status=%s",
                    endpoint,
                    i,
                    status_code,
                )

                response = http_response.json

                # Safety: stop pagination cleanly when the API reports no more results
                if not response:
                    logger.info(f"⛔ Stop pagination (no more results at page {i})")
                    logger.info(f"📊 Total pages fetched: {i - 1}")
                    return all_items

                if not isinstance(response, list):
                    raise TypeError(
                        f"Expected list response for pagination, got {type(response)}"
                    )

                items_count = len(response)
                logger.info(f"➡️ Page {i} → {items_count} items")

                success = True
            except PaginationAbortedError:
                # 🚫 Don't retry fail-fast errors — propagate immediately
                raise
            except Exception as e:
                attempt += 1
                logger.warning(
                    f"⚠️ Error fetching page {i} (attempt {attempt}) for '{endpoint}': {e}"
                )
                if attempt < retries:
                    time.sleep(retry_delay)
                else:
                    logger.error(
                        f"❌ Giving up on page {i} after {retries} failed attempts."
                    )

        if not success:
            # 🚫 Don't silently move on to the next page — a failed page means the dataset is incomplete
            raise PaginationAbortedError(
                f"🚨 Pagination aborted for '{endpoint}': page {i} failed after {retries} attempts.",
                response=http_response,
                response_json=http_response.json if http_response is not None else None,
            )

        all_items.extend(response)

    logger.info(f"📊 Total items fetched: {len(all_items)}")
    logger.debug(
        f"✅ Completed paginated fetch for '{endpoint}' — Total items: {len(all_items)}"
    )
    return all_items
