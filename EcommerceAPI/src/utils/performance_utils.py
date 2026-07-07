"""
====================================================================================================
Performance Utilities

Reusable helper functions shared by entity performance tests.

Purpose
-------
Provide common building blocks for measuring API response times while keeping
each entity responsible for its own benchmark scenarios.

These helpers intentionally contain NO business knowledge.

The framework owns:
    • request timing
    • endpoint formatting
    • exception handling
    • shared logging

Each entity owns:
    • endpoint under test
    • query parameters
    • benchmark thresholds
    • assertions
    • reporting

This separation keeps the framework reusable while allowing every microservice
team to evolve its own performance benchmarks independently.
====================================================================================================
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlencode

from EcommerceAPI.src.clients.api_client import APIClient
from EcommerceAPI.src.utils.exceptions import (
    APIRequestException,
    SchemaValidationError,
    UnexpectedStatusCodeError,
)

logger = logging.getLogger(__name__)


def build_display_endpoint(
    endpoint: str,
    params: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Build a human-readable endpoint.

    Examples
    --------
    customers
    customers?per_page=100
    products?orderby=price
    """

    if not params:
        return endpoint

    try:
        return f"{endpoint}?{urlencode(params, doseq=True)}"
    except (TypeError, ValueError):
        return f"{endpoint}?{params!r}"


def measure_get_response_time(
    api_client: APIClient,
    endpoint: str,
    *,
    params: Optional[Dict[str, Any]] = None,
) -> Tuple[float, Optional[Any]]:
    """
    Execute a GET request and measure its duration.

    Returns
    -------
    tuple
        (duration_in_seconds, response)

    A failed request never raises framework exceptions back to the caller.
    Instead the failure is logged and (duration, None) is returned so the
    performance test can decide how to handle partial failures.
    """

    display_endpoint = build_display_endpoint(endpoint, params)

    start = time.perf_counter()

    try:

        response = api_client.get(
            endpoint,
            params=params,
        )

        duration = time.perf_counter() - start

        logger.info(
            "📡 GET %s → %.3fs",
            display_endpoint,
            duration,
        )

        return duration, response

    except (
        SchemaValidationError,
        UnexpectedStatusCodeError,
        APIRequestException,
    ) as exc:

        duration = time.perf_counter() - start

        logger.exception(
            "❌ GET %s failed after %.3fs: %s",
            display_endpoint,
            duration,
            exc,
        )

        return duration, None

    except Exception as exc:

        duration = time.perf_counter() - start

        logger.exception(
            "❌ Unexpected error for %s after %.3fs: %s",
            display_endpoint,
            duration,
            exc,
        )

        return duration, None
