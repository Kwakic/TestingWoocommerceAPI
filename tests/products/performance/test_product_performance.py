"""
====================================================================================================
🧪 Products Performance Test Suite

Purpose
-------
Validate the response time of the Products  API.

Unlike Contract, Security and Preflight, performance tests belong to each
business entity.

Each entity owns:

    • benchmark scenarios
    • query parameters
    • performance thresholds
    • SLA expectations

This allows every microservice team to evolve its own benchmarks independently
while reusing the shared performance utilities provided by the framework.

Future examples
---------------

Customers
    GET /customers?per_page=100

Orders
    GET /orders?status=processing

Products
    GET /products?orderby=price

Coupons
    GET /coupons?search=SUMMER

The framework owns only the reusable timing utilities.
====================================================================================================
"""

from __future__ import annotations

import logging
import os
import statistics

import pytest

from EcommerceAPI.src.configs.runtime_config import get_config

from EcommerceAPI.src.utils.performance_utils import measure_get_response_time

logger = logging.getLogger(__name__)

pytestmark = [
    pytest.mark.performance,
]

ENV = get_config().ENV

# ==============================================================================
# Entity performance profile.
#
# Every business entity owns its benchmark configuration.
#
# The shared framework is responsible only for measuring request duration.
# Individual entities define:
#
# • endpoint under test
# • benchmark request parameters
# • performance thresholds
# • default benchmark iterations
#
# These values may evolve independently as each API grows.
# ==============================================================================

PRODUCTS_PERFORMANCE = {
    "endpoint": "products",
    "params": {
        "per_page": 100,
    },
    "max_avg_response": 6.20,
    "max_p95_response": 11.50,
    "iterations": 5,
}


def _resolve_iterations(pytestconfig) -> int:
    """
    Resolve the number of benchmark iterations.

    Resolution order

        1. --perf-iterations CLI option
        2. PERF_ITERATIONS environment variable
        3. Entity benchmark profile
    """

    option = getattr(pytestconfig, "option", None)

    if option and getattr(option, "perf_iterations", None):
        try:
            return int(option.perf_iterations)
        except ValueError:
            pass

    try:
        return int(
            os.getenv(
                "PERF_ITERATIONS",
                str(PRODUCTS_PERFORMANCE["iterations"]),
            )
        )
    except ValueError:
        return PRODUCTS_PERFORMANCE["iterations"]


@pytest.mark.performance
def test_product_response_times(
    pytestconfig,
    api_client,
    session_metadata,
):
    """
    Benchmark the Products endpoint.

    The benchmark executes multiple requests, measures their response times,
    calculates summary statistics, and validates the configured performance
    thresholds.
    """

    iterations = _resolve_iterations(pytestconfig)

    logger.info(
        "🔁 Products benchmark (%d iterations)",
        iterations,
    )

    response_times: list[float] = []

    failures = 0

    for run in range(iterations):

        duration, response = measure_get_response_time(
            api_client=api_client,
            endpoint=PRODUCTS_PERFORMANCE["endpoint"],
            params=PRODUCTS_PERFORMANCE["params"],
        )

        if response is None:

            failures += 1

            logger.debug("Run %02d → FAILED", run + 1)

            continue

        response_times.append(duration)

        logger.debug("Run %02d → %.3fs", run + 1, duration)

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------

    if failures == iterations:
        pytest.fail(
            "Performance test could not be completed because the API was unreachable."
        )

    if failures:

        logger.warning(
            "%d/%d benchmark requests failed.",
            failures,
            iterations,
        )

        pytest.xfail(f"{failures}/{iterations} benchmark requests failed.")

    if not response_times:
        pytest.fail("No successful benchmark requests.")

    if all(t < 0.001 for t in response_times):
        pytest.fail("Suspicious benchmark timings detected (~0.000s).")

    average = statistics.mean(response_times)

    p95 = (
        statistics.quantiles(response_times, n=100)[94]
        if len(response_times) > 1
        else max(response_times)
    )

    minimum = min(response_times)

    maximum = max(response_times)

    # -------------------------------------------------------------------------
    # Threshold validation
    # -------------------------------------------------------------------------

    assert (
        average <= PRODUCTS_PERFORMANCE["max_avg_response"]
    ), f"Average response time exceeded threshold ({average:.3f}s)"

    assert (
        p95 <= PRODUCTS_PERFORMANCE["max_p95_response"]
    ), f"P95 exceeded threshold ({p95:.3f}s)"

    # -------------------------------------------------------------------------
    # Human-readable summary
    # -------------------------------------------------------------------------

    git = session_metadata.get("git", {})
    ci = session_metadata.get("ci", {})

    logger.info("=" * 80)
    logger.info("📊 PRODUCTS PERFORMANCE SUMMARY")
    logger.info("=" * 80)

    logger.info("Environment : %s", ENV.upper())

    if ci.get("is_ci"):
        logger.info(
            "CI          : %s (%s)",
            ci.get("provider"),
            ci.get("job_id"),
        )

    if git.get("commit"):
        logger.info(
            "Git         : %s (%s)",
            git.get("commit"),
            git.get("branch"),
        )

    logger.info("Average     : %.3fs", average)
    logger.info("P95         : %.3fs", p95)
    logger.info("Minimum     : %.3fs", minimum)
    logger.info("Maximum     : %.3fs", maximum)

    logger.info("=" * 80)
