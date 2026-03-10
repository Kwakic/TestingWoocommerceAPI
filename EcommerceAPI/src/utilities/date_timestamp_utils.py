
# utilities/date_timestamp_utils.py

import logging

from datetime import datetime, timedelta, timezone
from typing import Tuple
from dateutil.parser import isoparse

logger = logging.getLogger(__name__)


def build_created_after_before_window(
        base_time: datetime,
        before_minutes: int = 1,
        after_minutes: int = 5,
        negative: bool = False
) -> Tuple[str, str]:
    """
    Builds a timestamp window around a given base_time for use in filtering resources by creation time.

    ✅ Positive case (default, negative=False):
        - Constructs a window that includes base_time:
            • created_after  = base_time - after_minutes
            • created_before = base_time + before_minutes
        - Useful for testing inclusion: confirms resource appears when created within this range.

    🚫 Negative case (negative=True):
        - Constructs a logically invalid/inverted window that excludes base_time:
            • created_after  = base_time + after_minutes
            • created_before = base_time - before_minutes
        - Used for exclusion tests: API should return an empty result set.

    This helper prevents flaky filters by avoiding reliance on local clock drift or timezone bugs.

    🧠 Why Use a Time Window (created_after and created_before)?
    Here’s why we don’t just call /customers with no filters:
        - Efficiency & Focus: Most /customers endpoints return paginated results. You don’t want to search through
        10,000 customers just to check if one was excluded.
        - Precision: You're narrowing the scope of your query to only the time when the deleted customers could’ve existed.
        - Edge Case Coverage: This helps test whether filtering logic (e.g., on created_at) leaks deleted data when
        users query by time.

    But in practice, if you don't pair it with created_before, you widen the query unnecessarily, increasing chances of:
        - Random, unrelated results that might slow down the test.
        - Flaky behavior (e.g., if another customers gets created in the test run and appears in the response)
        - Time drift issues (e.g., if server and test time differ)

    Args:
        base_time (datetime): Reference point for constructing the window (e.g., resource creation time).
        before_minutes (int): Offset added *after* base_time to calculate created_before.
        after_minutes (int): Offset subtracted *before* base_time to calculate created_after.
        negative (bool): Whether to build a negative (exclusion) window.

    Returns:
        Tuple[str, str]: (created_after, created_before) as ISO 8601 UTC-formatted strings with 'Z' suffix.
    """

    if not negative:  # Builds a window that includes base_time .It uses a real base_time for accuracy (rather than
        # naïve datetime.now()), Strip microseconds
        created_after = (base_time - timedelta(minutes=after_minutes)).replace(microsecond=0).isoformat().replace(
            "+00:00", "Z")
        created_before = (base_time + timedelta(minutes=before_minutes)).replace(microsecond=0).isoformat().replace(
            "+00:00", "Z")
    else:  # Builds a window that excludes base_time (inverted range)
        created_after = (base_time + timedelta(minutes=after_minutes)).replace(microsecond=0).isoformat().replace(
            "+00:00", "Z")
        created_before = (base_time - timedelta(minutes=before_minutes)).replace(microsecond=0).isoformat().replace(
            "+00:00", "Z")

    return created_after, created_before


def get_customers_in_window(helper, created_at: datetime, before_min: int = 1, after_min: int = 1,
                            negative: bool = False):
    """
    Fetches customers from API filtered by a time window around `created_at`.

    Args:
        helper: The customers helper with API call method.
        created_at (datetime): Timestamp to build the filter window around.
        before_min (int): +/- window size in minutes.
        after_min (int): +/- window size in minutes.
        negative (bool): If True, it builds an inverted time window (should exclude the timestamp).

    Returns:
        list: Customers returned from the API in the given time window.
    """
    # ⏳ Parse server timestamps the exact creation time from the customers response (in GMT) using ISO parser to
    # avoid datetime bugs.
    created_after, created_before = build_created_after_before_window(
        base_time=created_at,
        before_minutes=before_min,
        after_minutes=after_min,
        negative=negative
    )

    logger.info(f"🔍 Filtering customers using window:"
                f" created_after={created_after}, created_before={created_before}, negative={negative}")

    customers = helper.list_customers_paginated(
        created_after=created_after,
        created_before=created_before
    )

    logger.info(f"📞 API returned {len(customers)} customers in the filtered window.")
    return customers


def safe_parse_utc_datetime(raw_ts: str) -> datetime:
    """
    Parses an ISO 8601 datetime string into a timezone-aware UTC datetime with microseconds stripped.

    Use when exact precision is not required — e.g., negative tests or debug logging.

    Ensures returned datetime is:
        • timezone-aware (UTC)
        • normalized to UTC timezone
        • stripped of microseconds (clean second precision)

    Direction: string → datetime
    What it does:
        - Similar to precise_parse, but strips microseconds.
        - Makes datetime comparisons more forgiving.

    When to use it:
        ✅ Negative tests where precision is not critical.
        ✅ Human-friendly logging: logger.info(f"Created at: {safe_parse_utc_datetime(ts)}")
        ✅ Timestamp rounding or when filters don't need precision: safe_parse_utc_datetime("2025-07-31T12:00:00.456Z")
          →  2025-07-31T12:00:00Z

    Args:
        raw_ts (str): ISO 8601 timestamp string to parse.

    Returns:
        datetime: UTC-aware datetime with microseconds set to zero.

    Raises:
        ValueError: If input is empty or None.
    """
    if not raw_ts:
        raise ValueError("Cannot parse empty timestamp")

    # Parse the ISO 8601 string into a datetime object
    dt = isoparse(raw_ts)

    # If datetime is naive (no tzinfo), assume UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    # Convert to UTC and strip microseconds for clean, consistent comparisons
    return dt.astimezone(timezone.utc).replace(microsecond=0)


def precise_parse_utc_datetime(raw_ts: str) -> datetime:
    """
    Parses an ISO 8601 datetime string into a timezone-aware UTC datetime, preserving microseconds.

    Use when precision matters — e.g., timestamp equality between DB and API.

    Ensures returned datetime is:
        • timezone-aware (UTC)
        • normalized to UTC timezone
        • microsecond-preserving

    Direction: string → datetime
    What it does:
        - Parses ISO string into a UTC-aware datetime object.
        ✅ Preserves microseconds.
        - Handles naive timestamps (assumes UTC if needed).

    When to use it:
        ✅ Full timestamp comparison tests: assert precise_parse_utc_datetime(api_ts) == db_record.created_at
        ✅ E2E tests where sub-second accuracy matters.
        ✅ Avoid false negatives from precision loss.

    Args:
        raw_ts (str): ISO 8601 timestamp string to parse.

    Returns:
        datetime: UTC-aware datetime with full microsecond precision.

    Raises:
        ValueError: If input is empty or None.
    """
    if not raw_ts:
        raise ValueError("Cannot parse empty timestamp")

    # Parse the ISO 8601 string into a datetime object
    dt = isoparse(raw_ts)

    # If datetime is naive (no tzinfo), assume UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    # Convert to UTC but preserve microseconds for accurate timestamp filtering
    return dt.astimezone(timezone.utc)


def to_iso_utc(dt: datetime) -> str:
    """
    Formats a datetime object as an ISO 8601 UTC string with 'Z' suffix,
    stripping microseconds for clean filtering.
    Example:
        dt = datetime(2025, 7, 31, 10, 0, tzinfo=timezone.utc)
        to_iso_utc(dt)
        '2025-07-31T10:00:00Z'

    Direction: datetime → string
    What it does:
        - Converts any datetime to UTC ISO string with 'Z' suffix.
        - Removes microseconds for cleaner string (helps avoid filtering mismatches).

    When to use it:
        ✅ API queries like: customers?created_after=2025-07-31T10:00:00Z
        ✅ Avoiding microsecond noise in string filters.
        ✅ build_created_after_before_window() uses this under the hood.

    Args:
        dt (datetime): A timezone-aware UTC datetime.

    Returns:
        str: ISO-formatted UTC string (e.g., '2025-07-31T10:00:00Z').
    """
    return dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def get_now_utc_floor() -> datetime:
    """
    Returns the current time in UTC with microseconds stripped (rounded to the nearest second).
    """
    return datetime.now(timezone.utc).replace(microsecond=0)

def unix_to_utc_datetime(unix_ts: int) -> datetime:
    return datetime.fromtimestamp(unix_ts, tz=timezone.utc).replace(microsecond=0)