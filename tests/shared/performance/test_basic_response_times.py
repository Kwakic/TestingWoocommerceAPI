"""
====================================================================================================
🧪 Performance Test Suite — API Response Times
   Read-only benchmark that measures response times for key API endpoints.
====================================================================================================

This file is intentionally small and focused. It:
 - Reuses centralized logging configured by conftest/custom_logger (no local logging setup).
 - Uses session_metadata (provided by conftest) to include git/CI/session context in outputs.
 - Is read-only and safe for CI (performs GET requests only).
 - Relies on structured JSONL logs as the canonical artifact (no per-run JSON files written by this test).

How to run
----------
pytest -m performance
pytest -m performance --perf-iterations=5

To enable structured JSONL output (where per-request timing lines are recorded):
  - Set ENABLE_STRUCTURED_LOGS=1 in the environment before running pytest (CI should set this).
  - The JSONL file will be created under LOG_DIR/<ENV>/test_debug_structured_<TIMESTAMP>.jsonl
  - conftest prints the path in the session banner as LAST_STRUCTURED_LOG.
"""

from __future__ import annotations

import time
import os
import statistics
import pytest
import logging
from typing import Dict, Any, Optional, Tuple

from EcommerceAPI.src.clients.api_client import APIClient
from EcommerceAPI.src.utils.exceptions import (
    SchemaValidationError,
    UnexpectedStatusCodeError,
    APIRequestException,
)

from EcommerceAPI.src.configs.config_loader import ENV

# Module logger (uses shared configuration from conftest/custom_logger)
logger = logging.getLogger(__name__)


pytestmark = [
    pytest.mark.performance,
    pytest.mark.shared,
]


def _build_display_endpoint(endpoint: str, params: Optional[Dict[str, Any]]) -> str:
    """
    Return a human-friendly endpoint representation, including an encoded querystring
    when params are provided. Falls back to a repr() of params on serialization errors.
    """
    if not params:
        return endpoint
    try:
        from urllib.parse import urlencode

        qs = urlencode(params, doseq=True)
        return f"{endpoint}?{qs}"
    except (TypeError, ValueError):
        return f"{endpoint}?{repr(params)}"


def measure_response_time(
    api_client: APIClient,
    endpoint: str,
    *,
    params: Dict[str, Any] = None,
) -> Tuple[float, Optional[Any]]:
    """
    Measure the duration of a GET request.

    Returns:
      (duration_seconds: float, response_or_none)
    """
    display_endpoint = _build_display_endpoint(endpoint, params)
    start = time.perf_counter()
    try:
        response = api_client.get(
            endpoint,
            params=params,
        )

        duration = time.perf_counter() - start
        logger.info("📡 GET %s → completed in %.3fs", display_endpoint, duration)
        return duration, response
    except (
        SchemaValidationError,
        UnexpectedStatusCodeError,
        APIRequestException,
    ) as api_err:
        duration = time.perf_counter() - start
        logger.exception(
            "❌ GET %s → API failure after %.3fs: %s",
            display_endpoint,
            duration,
            api_err,
        )
        return duration, None
    except Exception as err:
        duration = time.perf_counter() - start
        logger.exception(
            "❌ GET %s → unexpected error after %.3fs: %s",
            display_endpoint,
            duration,
            err,
        )
        return duration, None


@pytest.mark.performance
def test_api_response_times(pytestconfig, api_client, session_metadata):
    """
    Run lightweight GET-only benchmarks for a set of endpoints and emit concise summaries.

    Flow:
      1. Read endpoints and iterations from CLI option --perf-iterations.
      2. For each endpoint run N iterations and collect durations.
      3. Compute metrics (min/max/avg/p95) and log concise summary lines.
      4. No on-disk perf JSON reports are produced by this test; structured logging captures per-request info.
    """
    client = api_client

    endpoints = {
        "customers": ("internal", "customers"),
        "products": ("internal", "products"),
        "orders": ("internal", "orders"),
        "coupons": ("internal", "coupons"),
    }

    # Resolve iterations in a simple, idiomatic and robust way:
    # 1) Prefer the attribute set on pytestconfig.option (perf_iterations) — this reflects CLI (--perf-iterations)
    # 2) Fall back to getoption variants for compatibility
    # 3) Fall back to PERF_ITERATIONS env var (from .env / CI)
    # 4) Final fallback: 5
    opt = getattr(pytestconfig, "option", None)
    if opt is not None and getattr(opt, "perf_iterations", None) is not None:
        try:
            iterations = int(opt.perf_iterations)
        except (TypeError, ValueError):
            # If the CLI value is malformed, fall back to env/default
            iterations = int(os.getenv("PERF_ITERATIONS", "5"))
    else:
        # CLI did not provide it — fall back to PERF_ITERATIONS env or default 5
        try:
            iterations = int(os.getenv("PERF_ITERATIONS", "5"))
        except (TypeError, ValueError):
            iterations = 5

    try:
        iterations = int(iterations)
    except (TypeError, ValueError):
        iterations = 5

    results: Dict[str, Any] = {}

    logger.info("🔁 Iterations per endpoint: %d", iterations)

    for name, (_, endpoint) in endpoints.items():
        logger.info("⏱️ Testing endpoint: %s (%s)", name, endpoint)

        times: list[float] = []
        failures = 0

        for i in range(iterations):
            duration, response = measure_response_time(
                api_client=client,
                endpoint=endpoint,
                params={"per_page": 100},
            )

            if response is None:
                failures += 1
                logger.debug("   • Run %02d: FAILED", i + 1)
                continue

            times.append(duration)
            logger.debug("   • Run %02d: %.3fs", i + 1, duration)

        # 🚨 HARD FAIL: all failed
        if failures == iterations:
            pytest.fail(f"❌ All {iterations} requests failed for endpoint: {name}")

        # ⚠️ PARTIAL FAILURES
        if failures > 0:
            logger.warning(
                "⚠️ %s → %d/%d requests failed", name.upper(), failures, iterations
            )
            pytest.xfail(f"{failures}/{iterations} requests failed for {name}")

        # 🚨 NO VALID TIMINGS
        if not times:
            pytest.fail(f"❌ No successful requests for endpoint: {name}")

        # 🚨 THIS is your key requirement (0.000s detection)
        if all(t < 0.001 for t in times):
            pytest.fail(
                f"❌ Suspicious timings detected for {name}: all values ~0.000s"
            )

        avg = statistics.mean(times)
        p95 = statistics.quantiles(times, n=100)[94] if len(times) >= 2 else max(times)

        results[name] = {
            "iterations": len(times),
            "min": round(min(times), 3),
            "max": round(max(times), 3),
            "avg": round(avg, 3),
            "p95": round(p95, 3),
        }

        logger.info(
            "✅ %s → avg: %.3fs | p95: %.3fs | min: %.3fs | max: %.3fs",
            name.upper(),
            avg,
            p95,
            min(times),
            max(times),
        )

    # Final concise summary (human-friendly)
    git_info = session_metadata.get("git", {})
    ci_info = session_metadata.get("ci", {})

    logger.info("📊 PERFORMANCE TEST SUMMARY — ENV: %s", ENV.upper())
    if ci_info.get("is_ci"):
        logger.info(
            "🏗️ CI Provider: %s | Job ID: %s",
            ci_info.get("provider"),
            ci_info.get("job_id"),
        )
    if git_info.get("commit"):
        logger.info(
            "🔖 Git Commit: %s (%s)", git_info.get("commit"), git_info.get("branch")
        )

    for name, stats in results.items():
        if "error" in stats:
            logger.error("❌ %s: %s", name, stats["error"])
        else:
            logger.info(
                "✅ %s: avg=%ss, p95=%ss, min=%ss, max=%ss",
                name,
                stats["avg"],
                stats["p95"],
                stats["min"],
                stats["max"],
            )
