"""
pytest reporting plugin.

Responsibilities:
- Add Allure labels: team / env / service
- Attach structured JSONL logs to Allure on FAILED tests only
- Attach local Playwright traces or safe CI trace references to failed UI tests
- Keep reporting lightweight and failure-focused

Design notes:
- Allure attachments MUST be added during an active test lifecycle
- Session-level attachments are NOT visible in Allure UI
- Structured logging remains owned by the logging plugin
- CI trace ZIPs stay out of the public Allure report
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
import pytest

from EcommerceAPI.src.configs.runtime_config import get_config

log = logging.getLogger(__name__)


def _find_playwright_traces(item) -> list[Path]:
    """Find traces for one failed UI test after pytest-playwright teardown."""
    try:
        output_root = Path(item.config.getoption("output", default="test-results"))
    except (AttributeError, ValueError):
        output_root = Path("test-results")

    traces: set[Path] = set()

    # pytest-playwright resolves the per-test folder using its output_path
    # fixture. Its recorder has moved retained traces there by teardown.
    output_path = getattr(item, "funcargs", {}).get("output_path")
    if output_path:
        traces.update(Path(output_path).glob("trace*.zip"))

    # The session-persistence test must use persistent browser profiles, so
    # its trace helper writes to a sibling custom-traces folder.
    test_id = re.sub(r"[^A-Za-z0-9_.-]+", "_", item.nodeid)
    traces.update((output_root / "custom-traces" / test_id).glob("*.zip"))

    return sorted(path for path in traces if path.is_file())


def _attach_playwright_trace_evidence(item, allure) -> None:
    """Attach local trace ZIPs or a safe CI reference to a failed UI result."""
    traces = _find_playwright_traces(item)
    if not traces:
        return

    is_ci = (
        os.getenv("CI", "").lower() in {"1", "true", "yes"}
        or os.getenv("GITHUB_ACTIONS", "").lower() == "true"
    )

    if not is_ci:
        for trace_path in traces:
            allure.attach.file(
                source=str(trace_path),
                name=f"playwright-{trace_path.stem}",
                attachment_type=allure.attachment_type.ZIP,
            )
        return

    # CI Allure HTML is published to a public QA Portal. Keep trace contents
    # out of that report; traces can contain page data and network details.
    artifact_enabled = get_config().PLAYWRIGHT_TRACE_ARTIFACT_ENABLED
    browser = getattr(item, "funcargs", {}).get("browser_name", "unknown")
    if hasattr(item, "callspec"):
        browser = item.callspec.params.get("browser_name", browser)

    if artifact_enabled:
        artifact_name = f"ui-{browser}-playwright-traces"
        repository = os.getenv("GITHUB_REPOSITORY")
        run_id = os.getenv("GITHUB_RUN_ID")
        server = os.getenv("GITHUB_SERVER_URL", "https://github.com")
        if repository and run_id:
            run_url = f"{server}/{repository}/actions/runs/{run_id}"
            body = (
                "<p>Playwright trace ZIPs for this failed test are available in "
                f"<code>{artifact_name}</code>. "
                f'<a href="{run_url}">Open the GitHub Actions run</a> and '
                "download that artifact.</p>"
            )
        else:
            body = (
                "Playwright trace ZIPs for this failed test are available in "
                f"the CI artifact {artifact_name}."
            )
        attachment_type = allure.attachment_type.HTML
    else:
        body = (
            "Trace files were not uploaded from this CI run. Because traces "
            "can contain page and network data, reproduce this failure in a "
            "trusted environment with --tracing retain-on-failure."
        )
        attachment_type = allure.attachment_type.TEXT

    allure.attach(
        body,
        name="Playwright trace location",
        attachment_type=attachment_type,
    )


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Enrich tests with:
      - Allure labels (team / env / service) [always, best-effort]
      - Structured JSONL attachment [FAILED tests only]
      - Playwright trace evidence [FAILED UI tests only, during teardown]

    Allure attachments are added while the test result is still active. Logs
    are ready during the call report; Playwright trace files are ready at
    teardown after the browser fixtures have closed their contexts.
    """
    outcome = yield
    rep = outcome.get_result()

    # The Playwright plugin writes retained trace files while its fixtures
    # tear down. Attach trace evidence at teardown, after those files exist.
    if rep.when == "teardown":
        setup_report = getattr(item, "rep_setup", None)
        call_report = getattr(item, "rep_call", None)
        failed = (
            rep.failed
            or bool(setup_report and setup_report.failed)
            or bool(call_report and call_report.failed)
        )
        if not failed or not item.get_closest_marker("ui"):
            return

        try:
            import allure

            _attach_playwright_trace_evidence(item, allure)
        except Exception as exc:
            log.debug(
                "Failed to attach Playwright trace evidence to Allure: %s",
                exc,
                exc_info=True,
            )
        return

    # Labels and structured logs are handled during the test call phase.
    if rep.when != "call":
        return

    # ------------------------------------------------------------------
    # Allure labels (best-effort, never fatal)
    # ------------------------------------------------------------------
    try:
        import allure
        from EcommerceAPI.src.utils.entity_discovery import extract_entity_from_nodeid
        from EcommerceAPI.src.configs.runtime_config import get_config

        ENV = get_config().ENV

        team = extract_entity_from_nodeid(item.nodeid)
        if team:
            allure.dynamic.label("team", team)
            allure.dynamic.label("service", team)

        allure.dynamic.label("env", ENV)

    except (ImportError, AttributeError, ValueError) as exc:
        log.debug("Skipping Allure labels: %s", exc)

    # ------------------------------------------------------------------
    # FAILED tests only beyond this point
    # ------------------------------------------------------------------
    if not rep.failed:
        return

    # ------------------------------------------------------------------
    # Attach structured JSONL log (source of truth)
    # ------------------------------------------------------------------
    try:
        import allure
        from EcommerceAPI.src.utils.custom_logger import LAST_STRUCTURED_LOG
    except ImportError:
        return

    if not LAST_STRUCTURED_LOG:
        return

    jsonl_path = Path(LAST_STRUCTURED_LOG)
    if not jsonl_path.exists():
        return

    try:
        allure.attach.file(
            source=str(jsonl_path),
            name="structured-logs.jsonl",
            attachment_type=allure.attachment_type.JSON,
        )
    except (OSError, RuntimeError, ValueError) as exc:
        # Never break pytest because of reporting
        log.debug(
            "Failed to attach structured JSONL log to Allure: %s",
            exc,
            exc_info=True,
        )
