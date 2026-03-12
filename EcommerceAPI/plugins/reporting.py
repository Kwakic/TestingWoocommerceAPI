"""
pytest reporting plugin.

Responsibilities:
- Add Allure labels: team / env / service
- Attach structured JSONL logs to Allure on FAILED tests only
- Keep reporting lightweight and failure-focused

Design notes:
- Allure attachments MUST be added during an active test lifecycle
- Session-level attachments are NOT visible in Allure UI
- Structured logging remains owned by the logging plugin
"""

from __future__ import annotations

import logging
from pathlib import Path
import pytest

log = logging.getLogger(__name__)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Enrich tests with:
      - Allure labels (team / env / service) [always, best-effort]
      - Structured JSONL attachment [FAILED tests only]

    This hook runs in the ONLY lifecycle phase where Allure attachments are valid.
    """
    outcome = yield
    rep = outcome.get_result()

    # Only operate during the test call phase
    if rep.when != "call":
        return

    # ------------------------------------------------------------------
    # Allure labels (best-effort, never fatal)
    # ------------------------------------------------------------------
    try:
        import allure
        from EcommerceAPI.src.utils.team_discovery import extract_team_from_nodeid
        from EcommerceAPI.src.configs.config_loader import ENV

        team = extract_team_from_nodeid(item.nodeid)
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
