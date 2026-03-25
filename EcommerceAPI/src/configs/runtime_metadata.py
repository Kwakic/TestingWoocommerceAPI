"""
Runtime session metadata (shared, plugin-agnostic).

Single source of truth for:
- session identity
- git metadata
- CI metadata

Safe to import from:
- plugins
- utils
- reporting layers
"""

from __future__ import annotations

import os
import subprocess
from typing import Dict, Any

from EcommerceAPI.src.configs.runtime_config import SESSION_ID


def _run_git(cmd):
    try:
        return subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode().strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def collect_session_metadata() -> Dict[str, Any]:
    """
    Best-effort collection of session metadata.

    This function MUST:
    - never raise
    - never depend on pytest
    - be safe at import time
    """

    # ✅ Git branch: Prefer CI environment variable over git command
    git_branch = (
        os.getenv("CI_COMMIT_REF_NAME")  # GitLab
        or os.getenv("GITHUB_REF_NAME")  # GitHub Actions
        or os.getenv("GIT_BRANCH")  # Jenkins
        or _run_git(["git", "rev-parse", "--abbrev-ref", "HEAD"])  # Local fallback
    )

    # ✅ Git commit: Prefer CI environment variable over git command
    git_commit = (
        os.getenv("CI_COMMIT_SHORT_SHA")  # GitLab
        or os.getenv("GITHUB_SHA", "")[:7]  # GitHub Actions (short)
        or _run_git(["git", "rev-parse", "--short", "HEAD"])  # Local fallback
    )

    git = {
        "commit": git_commit,
        "branch": git_branch,
    }
    # git = {
    #     "commit": _run_git(["git", "rev-parse", "--short", "HEAD"]),
    #     "branch": _run_git(["git", "rev-parse", "--abbrev-ref", "HEAD"]),
    # }

    ci = {
        "is_ci": False,
        "provider": None,
        "job_id": None,
        "job_url": os.getenv("CI_JOB_URL"),
        "pipeline_url": os.getenv("CI_PIPELINE_URL"),
    }

    if os.getenv("GITHUB_ACTIONS"):
        ci.update(
            {
                "is_ci": True,
                "provider": "github_actions",
                "job_id": os.getenv("GITHUB_RUN_ID"),
            }
        )
    elif os.getenv("GITLAB_CI"):
        ci.update(
            {
                "is_ci": True,
                "provider": "gitlab",
                "job_id": os.getenv("CI_JOB_ID"),
            }
        )
    elif os.getenv("JENKINS_HOME"):
        ci.update(
            {
                "is_ci": True,
                "provider": "jenkins",
                "job_id": os.getenv("BUILD_ID"),
            }
        )

    return {
        "session_id": SESSION_ID,
        "git": git,
        "ci": ci,
    }


# Compute ONCE per process
SESSION_METADATA = collect_session_metadata()
