"""
Centralized framework configuration contract.

This module is the SINGLE source of truth for all framework behavior flags.

Responsibilities:
- Read environment variables
- Normalize values (bool / int / paths)
- Apply defaults
- Enforce consistency
- Emit startup configuration banner
- Provide immutable runtime config object

Plugins MUST NOT call os.getenv directly.

They must depend on:
    - get_config()
    - or the `framework_config` pytest fixture

Why this exists:
- env vars are strings
- defaults must be consistent
- CI must behave predictably
- debugging must be observable
- config must be loggable once

Design principles:
- frozen dataclass
- resolved once per session
- explicit categories
- safe for pytest-xdist
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import os
import logging
import pytest
from dataclasses import asdict

from EcommerceAPI.src.utilities.env_utils import env_bool

# ============================================================================
# Get SESSION_ID
# ============================================================================
SESSION_ID: str = os.getenv("SESSION_ID") or os.urandom(4).hex()


# ============================================================================
# 🧱 Framework Configuration Dataclass
# ============================================================================

@dataclass(frozen=True)
class FrameworkConfig:
    """
    Immutable resolved framework configuration.

    This object represents the FINAL truth for how the framework behaves.
    """
    # ------------------------------------------------------------------
    # Runtime / execution environment
    # ------------------------------------------------------------------
    ENV: str

    # ------------------------------------------------------------------
    # Discovery / entity system
    # ------------------------------------------------------------------
    STRICT_ENTITY_DISCOVERY: bool

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------
    ENABLE_STRUCTURED_LOGS: bool
    ENABLE_JSON_PRETTY: bool
    LOG_PAYLOADS: bool
    REDACT_SENSITIVE_FIELDS: bool
    DISABLE_LOG_EMOJIS: bool

    KEEP_STRUCTURED_LOGS: int
    LOG_DIR: Path

    # ------------------------------------------------------------------
    # Schema / test behavior
    # ------------------------------------------------------------------
    FAIL_ON_EMPTY_LIST: bool
    PERF_ITERATIONS: int

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------
    AUTO_ALLURE_REPORT: bool

    # ------------------------------------------------------------------
    # CI / safety
    # ------------------------------------------------------------------
    REQUIRE_ENV: bool


def _config_to_safe_dict(cfg: FrameworkConfig) -> dict:
    """
    Convert FrameworkConfig into a JSON-safe dictionary.
    We can use it for Allure report attachment

    - Paths → strings
    - No secrets included (by design)
    """
    data = asdict(cfg)

    # normalize Path objects
    for k, v in data.items():
        if isinstance(v, Path):
            data[k] = str(v)

    return data


# ============================================================================
# 🔄 Internal config cache
# ============================================================================

_config_cache: Optional[FrameworkConfig] = None


# ============================================================================
# 🔧 Load config from environment
# ============================================================================

def _load_config_from_env() -> FrameworkConfig:
    """
    Resolve environment variables into a typed FrameworkConfig object.

    This is the ONLY place where os.getenv is allowed.
    """

    return FrameworkConfig(
        # -------------------------
        # Runtime
        # -------------------------
        ENV=os.getenv("ENV", "test"),

        # -------------------------
        # Discovery
        # -------------------------
        STRICT_ENTITY_DISCOVERY=env_bool("STRICT_ENTITY_DISCOVERY", False),

        # -------------------------
        # Logging
        # -------------------------
        ENABLE_STRUCTURED_LOGS=env_bool("ENABLE_STRUCTURED_LOGS", True),
        ENABLE_JSON_PRETTY=env_bool("ENABLE_JSON_PRETTY", False),
        LOG_PAYLOADS=env_bool("LOG_PAYLOADS", False),
        REDACT_SENSITIVE_FIELDS=env_bool("REDACT_SENSITIVE_FIELDS", True),
        DISABLE_LOG_EMOJIS=env_bool("DISABLE_LOG_EMOJIS", False),

        KEEP_STRUCTURED_LOGS=int(os.getenv("KEEP_STRUCTURED_LOGS", "3")),
        LOG_DIR=Path(os.getenv("LOG_DIR", "reports/logs")),

        # -------------------------
        # Schema / behavior
        # -------------------------
        FAIL_ON_EMPTY_LIST=env_bool("FAIL_ON_EMPTY_LIST", False),
        PERF_ITERATIONS=int(os.getenv("PERF_ITERATIONS", "5")),

        # -------------------------
        # Reporting
        # -------------------------
        AUTO_ALLURE_REPORT=env_bool("AUTO_ALLURE_REPORT", True),

        # -------------------------
        # CI safety
        # -------------------------
        REQUIRE_ENV=env_bool("REQUIRE_ENV", False),
    )


# ============================================================================
# 🔐 Public accessors
# ============================================================================

def get_config(reload: bool = False) -> FrameworkConfig:
    """
    Return the resolved FrameworkConfig.

    Cached by default.

    Use reload=True ONLY in tests that monkeypatch env vars.
    """
    global _config_cache

    if reload or _config_cache is None:
        _config_cache = _load_config_from_env()

    return _config_cache


def reload_config() -> None:
    """Clear cached configuration (used in tests only)."""
    global _config_cache
    _config_cache = None


# ============================================================================
# 🧪 Pytest fixtures
# ============================================================================

@pytest.fixture(scope="session")
def framework_config(pytestconfig) -> FrameworkConfig:
    """
    Session-scoped framework configuration.

    Plugins and tests should depend on this fixture
    instead of reading environment variables.
    """
    cfg = get_config(reload=True)

    # CLI precedence example
    if pytestconfig.getoption("--fail-on-empty-list"):
        cfg = FrameworkConfig(
            **{**cfg.__dict__, "FAIL_ON_EMPTY_LIST": True}
        )

    return cfg


@pytest.fixture(scope="session")
def fail_on_empty_list(framework_config: FrameworkConfig) -> bool:
    """
    Whether schema list endpoints should fail on empty responses.
    """
    return framework_config.FAIL_ON_EMPTY_LIST


# ============================================================================
# 📢 Startup banner (logged once)
# ============================================================================

def pytest_sessionstart(session):
    """
    Emit a single authoritative configuration snapshot at startup.
    """
    log = logging.getLogger("EcommerceAPI.config")
    cfg = get_config()

    # Session banner
    log.info("================= SESSION START ====================")
    log.info("Session ID : %s", SESSION_ID)
    # log.info("===================================================")

    log.info("================= FRAMEWORK CONFIG =================")
    log.info("STRICT_ENTITY_DISCOVERY : %s", cfg.STRICT_ENTITY_DISCOVERY)
    log.info("FAIL_ON_EMPTY_LIST      : %s", cfg.FAIL_ON_EMPTY_LIST)
    log.info("PERF_ITERATIONS         : %s", cfg.PERF_ITERATIONS)
    log.info("AUTO_ALLURE_REPORT      : %s", cfg.AUTO_ALLURE_REPORT)
    log.info("REQUIRE_ENV             : %s", cfg.REQUIRE_ENV)

    log.info("STRUCTURED_LOGS         : %s", cfg.ENABLE_STRUCTURED_LOGS)
    log.info("JSON_PRETTY             : %s", cfg.ENABLE_JSON_PRETTY)
    log.info("LOG_PAYLOADS            : %s", cfg.LOG_PAYLOADS)
    log.info("REDACT_SENSITIVE_FIELDS : %s", cfg.REDACT_SENSITIVE_FIELDS)
    log.info("DISABLE_LOG_EMOJIS      : %s", cfg.DISABLE_LOG_EMOJIS)

    log.info("LOG_DIR                 : %s", cfg.LOG_DIR)
    log.info("KEEP_STRUCTURED_LOGS    : %s", cfg.KEEP_STRUCTURED_LOGS)

