"""
Allure reporting integration plugin.

Responsibilities:
────────────────────────────────────────────────────────────
✔ Prepare and clean Allure results directory
✔ Collect executed teams dynamically during test execution
✔ Generate environment.properties for Allure UI
✔ Attach framework configuration once per session
✔ Auto-generate HTML report at session end (optional)

Extended reporting features:
────────────────────────────────────────────────────────────
✔ Inject CI metadata into Allure Environment tab
✔ Inject Git metadata into Allure Environment tab
✔ Deterministic session identity
✔ Ownership-aware reporting (teams)
✔ Auto-link Allure report to CI job URL
✔ Attach run summary to Allure
✔ Failed test breakdown by team
✔ Auto-generate categories.json
✔ Attach CI links on last test.

Design principles:
────────────────────────────────────────────────────────────
- Reporting must NEVER fail the test run
- Allure is optional (best-effort integration)
- Attachments must always be associated with a test
- Session data is collected globally and attached once
"""

from __future__ import annotations

import os
import subprocess
import logging
import shutil
import time
import json
from pathlib import Path
from typing import Optional
from collections import defaultdict

import pytest

from EcommerceAPI.src.utilities.team_discovery import extract_team_from_nodeid
from EcommerceAPI.plugins._config import get_config

from EcommerceAPI.plugins.logging_plugin import SESSION_METADATA
from EcommerceAPI.plugins._config import SESSION_ID as FRAMEWORK_SESSION_ID

from importlib.metadata import version, PackageNotFoundError

log = logging.getLogger(__name__)

# # ============================================================================
# # SIMULATE!!! Enrich CI metadata from environment (supports local simulation)
# # ============================================================================
# """
# # 1 - set environments in Power shell
# # $env:CI_PROVIDER="gitlab"
# # $env:CI_JOB_ID="98765"
# # $env:CI_JOB_URL="https://gitlab.com/org/project/-/jobs/98765"
# # $env:CI_PIPELINE_URL="https://gitlab.com/org/project/-/pipelines/12345"
# # $env:SESSION_ID="testsession567"
# """

# 2 - Uncomment the code block below and run pytest in the same shell
# ci = SESSION_METADATA.setdefault("ci", {})
#
# env_provider = os.getenv("CI_PROVIDER")
# env_job_id = os.getenv("CI_JOB_ID")
# env_job_url = os.getenv("CI_JOB_URL")
# env_pipeline_url = os.getenv("CI_PIPELINE_URL")
#
# if env_provider or env_job_id or env_job_url:
#     ci.update(
#         {
#             "is_ci": True,
#             "provider": env_provider,
#             "job_id": env_job_id,
#             "job_url": env_job_url,
#             "pipeline_url": env_pipeline_url,
#         }
#     )
#
#     log.info("✅ CI metadata enriched from environment: %s", ci)
# else:
#     log.debug("ℹ️ No CI environment variables detected")


# ============================================================================
# Session identity
# ============================================================================
"""
This gives you:
    - deterministic session identity
    - reusable across environment + attachment
"""

# Prefer explicit env var override, then the framework SESSION_ID from _config.py
_SESSION_ID: str = os.getenv("SESSION_ID") or FRAMEWORK_SESSION_ID


_SESSION_START_TIME = time.time()

_EXECUTED_TEAMS: set[str] = set()

# ============================================================================
# Runtime statistics
# ============================================================================

_TEST_STATS = {
    "passed": 0,
    "failed": 0,
    "skipped": 0,
}

_FAILED_BY_TEAM: dict[str, int] = defaultdict(int)

_TOTAL_TESTS = 0
_COMPLETED_TESTS = 0


# ============================================================================
# Allure results directory resolution
# ============================================================================

def _locate_alluredir(config) -> Optional[Path]:
    """
    Resolve Allure results directory.

    Resolution order:
    1. pytest --alluredir option
    2. ALLURE_RESULTS_DIR env var
    3. ./reports/allure-results
    """
    try:
        option = config.option
    except AttributeError:
        option = None

    alluredir = getattr(option, "alluredir", None) if option else None
    if alluredir:
        return Path(alluredir)

    env_dir = os.getenv("ALLURE_RESULTS_DIR")
    if env_dir:
        return Path(env_dir)

    return Path.cwd() / "reports" / "allure-results"


# ============================================================================
# Allure Environment properties/metadata (UI-visible)
# ============================================================================

def get_framework_version() -> str:
    """
    It goes to pyproject.toml file and search the version which will return.
    If not found, it returns "dev-local"

    """
    try:
        return version("EcommerceAPI")
    except PackageNotFoundError:
        return "dev-local"


def _write_allure_environment(cfg, results_dir: Path) -> None:
    """
    Write environment.properties for Allure UI.

    IMPORTANT:
    - This is the ONLY way Allure shows environment metadata
    - Labels like env/team/service are NOT rendered in UI

    This file populates the "Environment" tab in Allure report.
    This file defines run identity, not framework internals.

    Example UI:
        ENV=test
        teams=customers,orders
        framework=EcommerceAPI
        framework_version=dev
        session_id=8f3c1c42
        git_commit=.....
        git_branch=.....
        ci_provider=github
        ci_job_id=....
        ci_job_url=https://github.com/org/repo/actions/runs/123
    """
    try:
        # ------------------------------------------------------------------
        # Teams executed in this run
        # ------------------------------------------------------------------
        teams = ",".join(sorted(_EXECUTED_TEAMS)) or "unknown"

        # ------------------------------------------------------------------
        # Create variables for GIt and CI
        # ------------------------------------------------------------------

        git = SESSION_METADATA.get("git", {})
        ci = SESSION_METADATA.get("ci", {})

        # ------------------------------------------------------------------
        # CI metadata (optional)
        # ------------------------------------------------------------------
        lines = [
            f"ENV={getattr(cfg, 'ENV', 'unknown')}",
            f"teams={teams}",
            "framework=EcommerceAPI",
            f"framework_version={get_framework_version()}",
            f"session_id={_SESSION_ID}",
        ]

        # -----------------------------
        # Git metadata
        # -----------------------------
        if git.get("commit"):
            lines.append(f"git_commit={git['commit']}")

        if git.get("branch"):
            lines.append(f"git_branch={git['branch']}")

        # -----------------------------
        # CI metadata
        # -----------------------------
        if ci.get("is_ci"):
            if ci.get("provider"):
                lines.append(f"ci_provider={ci['provider']}")
            if ci.get("job_id"):
                lines.append(f"ci_job_id={ci['job_id']}")

            # auto-link URLs
            if ci.get("job_url"):
                lines.append(f"ci_job_url={ci['job_url']}")

            if ci.get("pipeline_url"):
                lines.append(f"ci_pipeline_url={ci['pipeline_url']}")

        env_file = results_dir / "environment.properties"
        env_file.write_text("\n".join(lines), encoding="utf-8")

        log.info("Allure environment properties generated → %s", results_dir, extra={
            "suppress_nodeid": True,
            "suppress_correlation": True,
        })

    except Exception as exc:
        # Reporting must NEVER block tests
        log.debug("Failed writing environment metadata: %s", exc, exc_info=True)


# ============================================================================
# Write Allure Categories.json
# ============================================================================
def _write_allure_categories(results_dir: Path) -> None:
    """
    Generate Allure categories.json.

    Categories group failures in the UI and greatly improve signal-to-noise ratio for API test suites.
    """
    try:
        categories = [
            {
                "name": "API Contract Failures",
                "matchedStatuses": ["failed"],
                "messageRegex": ".*assert.*|.*schema.*",
            },
            {
                "name": "Server Errors (5xx)",
                "matchedStatuses": ["failed"],
                "messageRegex": ".*500.*|.*502.*|.*503.*",
            },
            {
                "name": "Timeouts",
                "matchedStatuses": ["failed"],
                "messageRegex": ".*timeout.*|.*timed out.*",
            },
        ]

        file = results_dir / "categories.json"
        file.write_text(json.dumps(categories, indent=2), encoding="utf-8")

        log.info("Allure categories.json generated → %s", results_dir, extra={
            "suppress_nodeid": True,
            "suppress_correlation": True,
        })

    except Exception as exc:
        log.debug(
            "Failed generating categories.json: %s",
            exc,
            exc_info=True,
        )


# ============================================================================
# Run summary attachment
# ============================================================================
def _attach_run_summary(cfg) -> None:
    """
    Attaches a session-level run summary to the LAST executed test.

    This is required because Allure does not support session-level attachments.

    This provides immediate visibility into:
    - run identity
    - duration
    - total tests
    - pass/fail/skipped counts
    - failure ownership by team
    """
    try:
        import allure
        from allure_commons.types import AttachmentType

        duration = int(time.time() - _SESSION_START_TIME)
        minutes, seconds = divmod(duration, 60)

        total = sum(_TEST_STATS.values())

        lines = [
            f"Session ID: {_SESSION_ID}",
            f"ENV: {getattr(cfg, 'ENV', 'unknown')}",
            "",
            f"Duration: {minutes}m {seconds}s",
            "",
            f"Total tests: {total}",
            f"Passed: {_TEST_STATS['passed']}",
            f"Failed: {_TEST_STATS['failed']}",
            f"Skipped: {_TEST_STATS['skipped']}",
            "",
            "Failures by team:",
        ]

        if _FAILED_BY_TEAM:
            for team, count in sorted(_FAILED_BY_TEAM.items()):
                lines.append(f"- {team}: {count}")
        else:
            lines.append("None 🎉")

        allure.attach(
            "\n".join(lines),
            name="🧭 Run Summary",
            attachment_type=AttachmentType.TEXT,
        )

        log.info("🧭 Run summary attached to Allure")

    except Exception as exc:
        log.debug(
            "Failed to attach run summary: %s",
            exc,
            exc_info=True,
        )


# ============================================================================
# CI Links attachment (clickable links inside Allure)
# ============================================================================
def _attach_ci_links():
    """
    Attach CI job & pipeline links as HTML to Allure.
    Called once per test session.
    """
    try:
        import allure
        from allure_commons.types import AttachmentType
        import os

        job_url = os.getenv("CI_JOB_URL")
        pipeline_url = os.getenv("CI_PIPELINE_URL")

        if not job_url and not pipeline_url:
            return

        html = "<h3>🔗 CI Links</h3><ul>"

        if pipeline_url:
            html += f'<li><a href="{pipeline_url}" target="_blank">Pipeline</a></li>'

        if job_url:
            html += f'<li><a href="{job_url}" target="_blank">Job</a></li>'

        html += "</ul>"

        allure.attach(
            html,
            name="🔗 CI Links",
            attachment_type=AttachmentType.HTML,
        )

        log.info("🔗 CI links attached to Allure")

    except Exception as exc:
        log.debug("Failed to attach CI links: %s", exc, exc_info=True)


# ============================================================================
# Pytest hooks
# ============================================================================

def pytest_collection_finish(session):
    """
    Capture total number of collected tests.
    Required to detect the LAST executed test.
    """
    global _TOTAL_TESTS
    _TOTAL_TESTS = len(session.items)


@pytest.hookimpl(tryfirst=True)
def pytest_sessionstart(session):
    """
    Pytest hook executed at session startup.

    Responsibilities:
    - Clean Allure results directory
    - Create environment.properties for Allure UI
    """

    config = getattr(session, "config", None)
    if config is None:
        log.debug("No pytest config available; skipping Allure preparation")
        return

    results_dir = _locate_alluredir(config)

    try:
        # Ensure clean results directory
        if results_dir.exists():
            for child in results_dir.iterdir():
                try:
                    if child.is_dir():
                        shutil.rmtree(child)
                    else:
                        child.unlink()
                except Exception as exc:
                    log.debug(
                        "Failed removing Allure artifact %s: %s",
                        child,
                        exc,
                        exc_info=True,
                    )
            log.info("Cleared Allure results directory: %s", results_dir)

        else:
            results_dir.mkdir(parents=True, exist_ok=True)
            log.info("Created Allure results directory: %s", results_dir)

    except Exception as exc:
        # Reporting must never block pytest startup
        log.debug(
            "Allure sessionstart handling failed: %s",
            exc,
            exc_info=True,
        )


# ============================================================================
# Framework configuration snapshot (attachment)
# ============================================================================

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    """
    Attach framework configuration snapshot ONCE per test session.

    Why here:
    - Allure attachments must be associated with a test
    - Session-level attachments do not exist in Allure model

    Implementation:
    - First test attaches config
    - Remaining tests skip
    """

    # Track executed teams for environment metadata
    team = extract_team_from_nodeid(item.nodeid)
    if team:
        _EXECUTED_TEAMS.add(team)

    if not hasattr(item.session, "_framework_config_attached"):
        item.session._framework_config_attached = True

        try:
            import allure
            from allure_commons.types import AttachmentType
            from dataclasses import asdict

            cfg = get_config()
            raw = asdict(cfg)

            # Convert Path objects → strings
            snapshot = {
                k: (str(v) if hasattr(v, "__fspath__") else v)
                for k, v in raw.items()
            }

            snapshot["SESSION_ID"] = _SESSION_ID

            allure.attach(
                json.dumps(snapshot, indent=2),
                name="Framework Configuration",
                attachment_type=AttachmentType.JSON,
            )

            log.info("📎 Framework configuration attached to Allure")

        except Exception as exc:
            log.debug(
                "Framework config attachment skipped: %s",
                exc,
                exc_info=True,
            )

    yield


@pytest.hookimpl(trylast=True)
def pytest_runtest_logreport(report):
    """
    Collect per-test execution results and attach run summary + CI links on last test.
    """
    global _COMPLETED_TESTS

    if report.when != "call":
        return

    # Track test results
    if report.passed:
        _TEST_STATS["passed"] += 1
    elif report.failed:
        _TEST_STATS["failed"] += 1
        team = extract_team_from_nodeid(report.nodeid)
        _FAILED_BY_TEAM[team or "unknown"] += 1
    elif report.skipped:
        _TEST_STATS["skipped"] += 1

    _COMPLETED_TESTS += 1

    # Attach run summary and CI links on LAST test
    if _COMPLETED_TESTS == _TOTAL_TESTS:
        try:
            # Attach run summary
            _attach_run_summary(get_config())
        except Exception as exc:
            log.debug("Failed to attach run summary: %s", exc, exc_info=True)

        # Attach CI links once per session
        if not hasattr(report, "_ci_links_attached"):
            try:
                report._ci_links_attached = True
                _attach_ci_links()
            except Exception as exc:
                log.debug("Failed to attach CI links: %s", exc, exc_info=True)


# ============================================================================
# Pytest session finish
# ============================================================================

@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    """
    Pytest hook executed at session end.

    Responsibilities:
    - Auto-generate Allure HTML report (optional)
    - Never fail test execution
    """
    config = getattr(session, "config", None)
    if config is None:
        return

    results_dir = _locate_alluredir(config)
    if not results_dir.exists() or not any(results_dir.iterdir()):
        log.warning(
            "Allure results directory empty — skipping HTML generation: %s",
            results_dir,
        )
        return

    # ✅ write environment AFTER tests → teams known
    cfg = get_config()
    _write_allure_environment(cfg, results_dir)
    _write_allure_categories(results_dir)

    if os.getenv("AUTO_ALLURE_REPORT", "").lower() not in ("1", "true", "yes"):
        log.debug("AUTO_ALLURE_REPORT disabled — skipping HTML generation")
        return

    report_dir = results_dir.parent / "allure-report"
    allure_cmd = shutil.which("allure")

    if not allure_cmd:
        log.error("Allure CLI not found — report generation skipped")
        return

    log.info(
        "Auto-generating Allure report → %s",
        report_dir,
        extra={
            "suppress_nodeid": True,
            "suppress_correlation": True,
        },
    )

    try:
        subprocess.run(
            [
                allure_cmd,
                "generate",
                str(results_dir),
                "-o",
                str(report_dir),
                "--clean",
            ],
            check=True,
        )

    except subprocess.CalledProcessError as exc:
        log.error("Allure generation failed (exit code %s)", exc.returncode)
    except Exception as exc:
        log.exception("Unexpected Allure generation error: %s", exc)

# 🧠 Allure only displays these labels visually:
# This is not documented clearly, but it is hardcoded in Allure frontend.

# | Label name    | Where it appears |
# | ------------- | ---------------- |
# | `feature`     | Features tab     |
# | `story`       | Behaviors        |
# | `epic`        | Behaviors        |
# | `severity`    | Test card        |
# | `owner`       | Test card        |
# | `tag`         | Filters          |
# | `suite`       | Suites           |
# | `parentSuite` | Suites           |
# | `subSuite`    | Suites           |
# | `host`        | System           |
# | `thread`      | System           |
# | `framework`   | System           |
# | `language`    | System           |

# Everything else is silently ignored in UI.
# Even though it exists in JSON.
# That includes:
# ❌ env
# ❌ team
# ❌ service
# ❌ component
# ❌ domain

# Why they do NOT appear in Allure UI
# Because Allure UI only renders a fixed whitelist of labels.

# ✅ What you should do (recommended architecture)
# ✔ Use labels for:
# feature
# story
# severity
# owner
# tag

# ✔ Use environment.properties for:
# ENV
# SERVICE
# TEAM
# API_HOST
# BUILD
# CI_JOB
# SESSION_ID
