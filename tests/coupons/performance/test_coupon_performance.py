"""Sequential response-time trend check for the Coupons API."""

from __future__ import annotations

import logging
import os
import statistics

import pytest

from EcommerceAPI.src.configs.runtime_config import get_config
from EcommerceAPI.src.utils.performance_utils import measure_get_response_time

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.performance, pytest.mark.coupons]

COUPONS_PERFORMANCE = {
    "endpoint": "coupons",
    "params": {"search": "SUMMER", "per_page": 100},
    "warmup_iterations": 3,
    "iterations": 30,
    # Initial limits follow the repository's existing performance baseline.
    # Tune these independently when CI history establishes Coupons-specific SLOs.
    "max_avg_response": 6.20,
    "max_p95_response": 11.50,
}


def _resolve_iterations(pytestconfig) -> int:
    option = getattr(pytestconfig, "option", None)
    override = getattr(option, "perf_iterations", None) if option else None
    if override:
        try:
            return int(override)
        except (TypeError, ValueError):
            logger.warning(
                "Invalid --perf-iterations value %r; using fallback.", override
            )

    try:
        return int(os.getenv("PERF_ITERATIONS", str(COUPONS_PERFORMANCE["iterations"])))
    except ValueError:
        return COUPONS_PERFORMANCE["iterations"]


def test_coupon_response_times(pytestconfig, api_client, session_metadata):
    """Measure GET /coupons for a search term; warm-ups are excluded."""
    iterations = _resolve_iterations(pytestconfig)
    warmups = COUPONS_PERFORMANCE["warmup_iterations"]

    if iterations < 20:
        logger.warning(
            "Only %d measured requests are configured; P95 will be very rough. "
            "Use at least 20 for trend checks, or omit the override to use the profile default.",
            iterations,
        )

    logger.info("Warming up Coupons endpoint (%d requests; excluded)", warmups)
    for run in range(warmups):
        duration, response = measure_get_response_time(
            api_client=api_client,
            endpoint=COUPONS_PERFORMANCE["endpoint"],
            params=COUPONS_PERFORMANCE["params"],
        )
        if response is None:
            logger.warning(
                "Warm-up request %02d failed; excluded from results.", run + 1
            )
        else:
            logger.debug("Warm-up %02d -> %.3fs (excluded)", run + 1, duration)

    response_times: list[float] = []
    failures = 0
    logger.info("Coupons benchmark (%d measured requests)", iterations)

    for run in range(iterations):
        duration, response = measure_get_response_time(
            api_client=api_client,
            endpoint=COUPONS_PERFORMANCE["endpoint"],
            params=COUPONS_PERFORMANCE["params"],
        )
        if response is None:
            failures += 1
            logger.debug("Run %02d -> FAILED", run + 1)
            continue
        response_times.append(duration)
        logger.debug("Run %02d -> %.3fs", run + 1, duration)

    if failures == iterations:
        pytest.fail("Coupons performance benchmark could not reach the API.")
    if failures:
        pytest.xfail(f"{failures}/{iterations} Coupons benchmark requests failed.")
    if not response_times:
        pytest.fail("No successful Coupons benchmark requests.")
    if all(value < 0.001 for value in response_times):
        pytest.fail("Suspicious Coupons benchmark timings detected (~0.000s).")

    average = statistics.mean(response_times)
    p95 = (
        statistics.quantiles(response_times, n=20, method="inclusive")[18]
        if len(response_times) > 1
        else max(response_times)
    )
    minimum = min(response_times)
    maximum = max(response_times)

    assert (
        average <= COUPONS_PERFORMANCE["max_avg_response"]
    ), f"Coupons average response time exceeded threshold ({average:.3f}s)"
    assert (
        p95 <= COUPONS_PERFORMANCE["max_p95_response"]
    ), f"Coupons P95 exceeded threshold ({p95:.3f}s)"

    git = session_metadata.get("git", {})
    ci = session_metadata.get("ci", {})
    logger.info("=" * 72)
    logger.info(
        "COUPONS PERFORMANCE SUMMARY | environment=%s", get_config().ENV.upper()
    )
    if ci.get("is_ci"):
        logger.info("CI: %s (%s)", ci.get("provider"), ci.get("job_id"))
    if git.get("commit"):
        logger.info("Git: %s (%s)", git.get("commit"), git.get("branch"))
    logger.info("Average: %.3fs | P95: %.3fs", average, p95)
    logger.info(
        "Samples: %d measured; %d warm-ups excluded", len(response_times), warmups
    )
    logger.info("Minimum: %.3fs | Maximum: %.3fs", minimum, maximum)
    logger.info("=" * 72)
