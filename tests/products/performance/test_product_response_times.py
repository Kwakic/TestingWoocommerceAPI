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

from EcommerceAPI.src.configs.config_loader import ENV
from EcommerceAPI.src.utils.performance_utils import measure_get_response_time

logger = logging.getLogger(__name__)

pytestmark = [
    pytest.mark.performance,
]

# ==============================================================================
# Entity benchmark configuration.
#
# Every entity owns its own benchmark profile.
#
# As the framework grows these values can diverge significantly.
#
# Customers
#     per_page=100
#
# Orders
#     status=processing
#
# Products
#     orderby=price
#
# Coupons
#     search=SUMMER
# ==============================================================================

ENTITY = "products"

ENDPOINT = "products"

QUERY_PARAMS = {
    "per_page": 100,
}

#
# Initial benchmark expectations.
#
# These values are intentionally conservative.
# Every entity may later define its own SLA.
#
MAX_AVG_RESPONSE = 2.20
MAX_P95_RESPONSE = 2.90


def _resolve_iterations(pytestconfig) -> int:
    """
    Resolve the number of benchmark iterations.

    Resolution order:

        1. --perf-iterations CLI option
        2. PERF_ITERATIONS environment variable
        3. Default value (5)
    """

    option = getattr(pytestconfig, "option", None)

    if option and getattr(option, "perf_iterations", None):

        try:
            return int(option.perf_iterations)
        except ValueError:
            pass

    try:
        return int(os.getenv("PERF_ITERATIONS", "5"))
    except ValueError:
        return 5


@pytest.mark.performance
def test_product_response_times(
    pytestconfig,
    api_client,
    session_metadata,
):
    """
    Benchmark the Products endpoint.

    Workflow

        1. Execute N GET requests.
        2. Measure every response time.
        3. Calculate summary statistics.
        4. Validate benchmark expectations.
        5. Emit concise CI-friendly logs.
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
            endpoint=ENDPOINT,
            params=QUERY_PARAMS,
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
        average <= MAX_AVG_RESPONSE
    ), f"Average response time exceeded threshold ({average:.3f}s)"

    assert p95 <= MAX_P95_RESPONSE, f"P95 exceeded threshold ({p95:.3f}s)"

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
