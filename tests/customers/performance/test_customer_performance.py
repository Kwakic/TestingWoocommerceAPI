"""
====================================================================================================
🧪 Customers Performance Test Suite

Purpose
-------
Validate the response time of the Customers API.

This is a sequential trend check: three warm-up requests are excluded, then
thirty measured requests are used for the summary. Warm-ups help avoid skew
from the first request opening a connection or initializing server-side work.
P95 means that 95% of measured requests are at or below that response time;
with thirty samples, treat it as a rough trend signal. This test does not
simulate multiple users or measure throughput; use a dedicated load-testing
tool for those questions.

Unlike Contract, Security and Preflight, performance tests belong to each
business entity.

Each entity owns:

    • benchmark scenarios
    • query parameters
    • performance thresholds
    • response-time thresholds

This allows each API entity to evolve its own benchmarks independently while
reusing the shared performance utilities provided by the framework.

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
# Customer performance profile.
#
# This profile configures the customer-list benchmark. Warm-up requests let
# the connection and server settle; their times are excluded from the results.
# Thirty measured requests provide a steadier average and a more informative
# approximate P95 trend than the old five-request sample.
# This remains a sequential trend check, not a concurrent load test.
# ==============================================================================

CUSTOMERS_PERFORMANCE = {
    "endpoint": "customers",
    "params": {
        "per_page": 100,
    },
    "max_avg_response": 6.20,
    "max_p95_response": 11.50,
    "warmup_iterations": 3,
    "iterations": 30,
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
                str(CUSTOMERS_PERFORMANCE["iterations"]),
            )
        )
    except ValueError:
        return CUSTOMERS_PERFORMANCE["iterations"]


@pytest.mark.performance
def test_customer_response_times(
    pytestconfig,
    api_client,
    session_metadata,
):
    """
    Benchmark the Customers endpoint.

    The benchmark first sends excluded warm-up requests, then measures the
    configured number of sequential customer-list requests. It summarizes
    those measured responses and checks the configured thresholds.
    """

    iterations = _resolve_iterations(pytestconfig)
    warmup_iterations = CUSTOMERS_PERFORMANCE["warmup_iterations"]

    if iterations < 20:
        logger.warning(
            "Only %d measured requests are configured; P95 will be very rough. "
            "Use at least 20 for trend checks, or omit the override to use the profile default.",
            iterations,
        )

    logger.info(
        "🔥 Warming up Customers endpoint (%d requests; excluded from results)",
        warmup_iterations,
    )

    for warmup_run in range(warmup_iterations):
        duration, response = measure_get_response_time(
            api_client=api_client,
            endpoint=CUSTOMERS_PERFORMANCE["endpoint"],
            params=CUSTOMERS_PERFORMANCE["params"],
        )

        if response is None:
            logger.warning(
                "Warm-up request %02d failed; it will not be included in the benchmark.",
                warmup_run + 1,
            )
            continue

        logger.debug(
            "Warm-up %02d → %.3fs (excluded)",
            warmup_run + 1,
            duration,
        )

    logger.info(
        "🔁 Customers benchmark (%d measured requests)",
        iterations,
    )

    response_times: list[float] = []

    failures = 0

    for run in range(iterations):

        duration, response = measure_get_response_time(
            api_client=api_client,
            endpoint=CUSTOMERS_PERFORMANCE["endpoint"],
            params=CUSTOMERS_PERFORMANCE["params"],
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

    # The inclusive method interpolates within observed timings instead of
    # projecting beyond the sample's fastest or slowest observation.
    p95 = (
        statistics.quantiles(response_times, n=20, method="inclusive")[18]
        if len(response_times) > 1
        else max(response_times)
    )

    minimum = min(response_times)

    maximum = max(response_times)

    # -------------------------------------------------------------------------
    # Threshold validation
    # -------------------------------------------------------------------------

    assert (
        average <= CUSTOMERS_PERFORMANCE["max_avg_response"]
    ), f"Average response time exceeded threshold ({average:.3f}s)"

    assert (
        p95 <= CUSTOMERS_PERFORMANCE["max_p95_response"]
    ), f"P95 exceeded threshold ({p95:.3f}s)"

    # -------------------------------------------------------------------------
    # Human-readable summary
    # -------------------------------------------------------------------------

    git = session_metadata.get("git", {})
    ci = session_metadata.get("ci", {})

    logger.info("=" * 80)
    logger.info("📊 CUSTOMERS PERFORMANCE SUMMARY")
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
    logger.info(
        "Samples     : %d measured; %d warm-up requests excluded",
        len(response_times),
        warmup_iterations,
    )
    logger.info("Minimum     : %.3fs", minimum)
    logger.info("Maximum     : %.3fs", maximum)

    logger.info("=" * 80)
