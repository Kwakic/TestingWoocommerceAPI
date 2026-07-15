"""
📦 Pagination Utility Module

Provides a generic utility function to paginate through WooCommerce API results.
Intended for use in test helpers like customers_helper, orders_helper, coupons_helper, etc.
"""

import logging
import time
from copy import deepcopy

logger = logging.getLogger(__name__)


def paginate_all_results(
    api_client, endpoint, params=None, max_pages=1000, retries=3, retry_delay=1.0
):
    """
        Generic pagination handler for WooCommerce-style endpoints with simple retry logic.

    🔧 ADDED:
        - Added retry logic per page fetch (retries=3, delay=1.0s).
        - Keeps logic explicit (no recursion or decorators) for readability.

    Args:
        api_client (APIClient): Utility class to perform authenticated requests.
        endpoint (str): API endpoint (e.g., 'customers', 'orders').
        params (dict, optional): Query parameters for filtering (e.g., per_page, created_after).
        max_pages (int): Maximum number of pages to fetch.
        retries (int): How many times to retry a failed page request.
        retry_delay (float): Delay (seconds) between retries.

    Returns:
        list: Aggregated list of all items fetched from the endpoint.
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

        while attempt < retries and not success:
            try:
                logger.debug(
                    f"📦 Fetching {endpoint} page {i} (attempt {attempt + 1}/{retries})"
                )
                http_response = api_client.get(endpoint, params=params)

                # ✅ Validate status code for pagination calls
                assert http_response.status_code == 200, (
                    f"❌ Pagination request failed for {endpoint} page={i}. "
                    f"Expected status 200, got {http_response.status_code}"
                )

                logger.debug(
                    "📄 Pagination request OK: endpoint=%s page=%s status=%s",
                    endpoint,
                    i,
                    http_response.status_code,
                )

                response = http_response.json

                # Safety: ensure response is an iterable list. Stop pagination if no response or empty list is returned
                if not response:
                    total_pages = i - 1
                    logger.info(f"⛔ Stop pagination (no more results at page {i})")
                    logger.info(f"📊 Total pages fetched: {total_pages}")
                    return all_items

                items_count = len(response)
                logger.info(f"➡️ Page {i} → {items_count} items")

                if not isinstance(response, list):
                    raise TypeError(
                        f"Expected list response for pagination, got {type(response)}"
                    )

                success = True
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
                    break

        if success and response:
            all_items.extend(response)

    logger.info(f"📊 Total items fetched: {len(all_items)}")
    logger.debug(
        f"✅ Completed paginated fetch for '{endpoint}' — Total items: {len(all_items)}"
    )
    return all_items


# NOTE: You can to make this retry logic configurable via environment variable (e.g. PAGINATION_RETRY_COUNT)?
# That’s sometimes handy when you run tests on unstable remote WooCommerce hosts.


# Looking at the pagination_utils.py you provided, I can see it needs refactoring to match the customers_helper pattern. The current version has some issues:
#
#     ❌ Uses low-level api_client.get() directly
#     ❌ Has retry logic (should be in APIClient, not pagination)
#     ❌ Manual page looping (not consistent with customers approach)
#     ❌ Uses http_response.json directly (should use .json attribute)
#
# Here's the refactored pagination_utils.py that matches the customers_helper approach:Perfect! I've refactored pagination_utils.py to be fully consistent with the customers_helper architecture. Here's what changed:
# ✅ Key Refactoring Changes:
# From Old Pattern:
# Python
#
# # ❌ Manual retry logic (duplicated)
# while attempt < retries and not success:
#     try:
#         http_response = api_client.get(...)
#         # retry handling, sleep, etc.
#     except:
#         attempt += 1
#         if attempt < retries:
#             time.sleep(retry_delay)
#
# # ❌ Mixed concerns (pagination + retry)
# # ❌ Hard to read and maintain
#
# To New Pattern:
# Python
#
# # ✅ Clean, simple pagination loop
# for page_num in range(1, max_pages + 1):
#     params["page"] = page_num
#
#     try:
#         # ✅ APIClient.get() handles ALL retry logic internally
#         http_response = api_client.get(endpoint, params=params)
#
#         # ✅ Just check status and process response
#         if http_response.status_code != 200:
#             break
#
#         response_data = http_response.json
#
#         if not response_data:  # Empty page = done
#             break
#
#         all_items.extend(response_data)
#     except Exception as e:
#         logger.error(...)
#         break
#
# ✅ What This Aligns With:
# Aspect	Old	New	Customers Pattern
# Retry logic	❌ Manual (in pagination)	✅ Delegated to APIClient	✅ APIClient handles it
# HTTP calls	api_client.get()	api_client.get()	✅ Same
# Response handling	http_response.json	http_response.json	✅ Same
# Error handling	Manual try/except + retry	Simple try/except	✅ Clean
# Logging	Basic debug logs	Structured emoji logs	✅ Consistent
# Concerns	Pagination + Retry mixed	Pagination only	✅ Separated
# ✅ Benefits:
#
# ✅ Single Responsibility — pagination only, no retry logic
# ✅ DRY — retry logic lives once in APIClient, not duplicated
# ✅ Maintainable — easy to read and understand
# ✅ Consistent — same pattern as customers_helper
# ✅ Debuggable — cleaner logs, fewer nested try/except blocks
# ✅ Reliable — APIClient's retry logic is battle-tested
