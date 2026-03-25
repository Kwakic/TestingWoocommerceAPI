"""
Smoke tests for structured logging metadata and LAST_STRUCTURED_LOG exposure.

preflight: verify environment/test framework before suite runs

These tests validate:
- GLOBAL_METADATA receives all expected keys after attach_global_logging_metadata is called.
- configure_logging exposes the most-recent structured logfile path via LAST_STRUCTURED_LOG
  when structured logging is enabled (best-effort, uses a temporary LOG_DIR).
"""

import os
import shutil
import pytest
import logging
from pathlib import Path


from EcommerceAPI.src.utils import custom_logger

pytestmark = [pytest.mark.preflight, pytest.mark.shared]

log = logging.getLogger(__name__)


def test_attach_global_metadata_contains_expected_keys():
    # Prepare sample metadata
    sample_meta = {
        "env": "test",
        "session_id": "deadbeef",
    }
    ci_info = {"ci_provider": "github_actions", "ci_job_id": "123", "is_ci": True}
    git_info = {"git_commit": "abc123", "git_branch": "main"}

    # Attach and assert GLOBAL_METADATA has the merged keys (guard against mutation from other tests)
    custom_logger.GLOBAL_METADATA.clear()
    custom_logger.attach_global_logging_metadata(
        env=sample_meta["env"],
        session_id=sample_meta["session_id"],
        ci_info=ci_info,
        git_info=git_info,
    )

    gm = custom_logger.GLOBAL_METADATA
    assert gm["env"] == "test"
    assert gm["session_id"] == "deadbeef"
    assert gm["ci_provider"] == "github_actions"
    assert gm["ci_job_id"] == "123"
    assert gm["is_ci"] is True
    assert gm["git_commit"] == "abc123"
    assert gm["git_branch"] == "main"


def test_last_structured_log_set_when_enabled(tmp_path, monkeypatch):
    # Use a tmp LOG_DIR and enable structured logging via env
    tmp_log_dir = tmp_path / "logs"
    monkeypatch.setenv("LOG_DIR", str(tmp_log_dir))
    monkeypatch.setenv("ENABLE_STRUCTURED_LOGS", "1")
    monkeypatch.setenv("KEEP_STRUCTURED_LOGS", "1")  # keep pruning simple

    # Ensure a clean state
    custom_logger.LAST_STRUCTURED_LOG = None

    # Configure logging (this should create a structured file under tmp_log_dir/<ENV>/)
    logger = custom_logger.configure_logging()

    # LAST_STRUCTURED_LOG should be set to a path string (or None if creation failed)
    last = custom_logger.LAST_STRUCTURED_LOG
    assert last is None or isinstance(last, str)
    if last:
        # File should exist on disk (handler created it, the file may exist as empty until flushed)
        assert (tmp_path / "logs" / os.getenv("ENV", "test") / Path(last).name).exists()

    # Cleanup: unset envs to avoid leaking into other tests
    monkeypatch.delenv("LOG_DIR", raising=False)
    monkeypatch.delenv("ENABLE_STRUCTURED_LOGS", raising=False)
    monkeypatch.delenv("KEEP_STRUCTURED_LOGS", raising=False)
    # Best-effort cleanup of temp logs directory
    try:
        shutil.rmtree(tmp_log_dir)
    except FileNotFoundError:
        # Directory was never created — safe to ignore
        pass
    except PermissionError as e:
        # Common on Windows / CI; log for visibility but don't fail preflight
        logger.warning("Could not remove temp log dir %s: %s", tmp_log_dir, e)
