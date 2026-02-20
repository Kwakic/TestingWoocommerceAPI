"""
📦 Pagination Utility Module

Provides a generic utility function to paginate through WooCommerce API results.
Intended for use in test helpers like customers_helper, orders_helper, coupons_helper, etc.
"""

import logging as logger
import time
from copy import deepcopy


def paginate_all_results(request_utility, endpoint, params=None, max_pages=1000, retries=3, retry_delay=1.0):
    """
        Generic pagination handler for WooCommerce-style endpoints with simple retry logic.

    🔧 ADDED:
        - Added retry logic per page fetch (retries=3, delay=1.0s).
        - Keeps logic explicit (no recursion or decorators) for readability.

    Args:
        request_utility (RequestUtility): Utility class to perform authenticated requests.
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
                logger.debug(f"📦 Fetching {endpoint} page {i} (attempt {attempt + 1}/{retries})")
                http_response = request_utility.get(endpoint, params=params)
                response = http_response.json

                # Safety: ensure response is an iterable list. Stop pagination if no response or empty list is returned
                if not response:
                    logger.info(f"⛔ No more results at page {i}. Ending pagination for '{endpoint}'")
                    return all_items  # ✅ STOP EVERYTHING

                if not isinstance(response, list):
                    raise TypeError(f"Expected list response for pagination, got {type(response)}")

                success = True
            except Exception as e:
                attempt += 1
                logger.warning(f"⚠️ Error fetching page {i} (attempt {attempt}) for '{endpoint}': {e}")
                if attempt < retries:
                    time.sleep(retry_delay)
                else:
                    logger.error(f"❌ Giving up on page {i} after {retries} failed attempts.")
                    break

        if success and response:
            all_items.extend(response)

    logger.debug(f"✅ Completed paginated fetch for '{endpoint}' — Total items: {len(all_items)}")
    return all_items

# NOTE: You can to make this retry logic configurable via environment variable (e.g. PAGINATION_RETRY_COUNT)?
# That’s sometimes handy when you run tests on unstable remote WooCommerce hosts.
