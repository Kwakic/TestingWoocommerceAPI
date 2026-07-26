"""
Centralized framework runtime configuration.

It owns runtime configuration.

This module is the SINGLE source of truth for all framework behavior flags.

Responsibilities:
- Read environment variables
- Normalize values (bool / int / paths)
- Apply defaults
- Enforce consistency
- Provide immutable runtime config object
- Provide a stable SESSION_ID

⚠️ IMPORTANT
This module is pytest-agnostic.
Do NOT import pytest here.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional
import os

from EcommerceAPI.src.utils.env_utils import env_bool

# ============================================================================
# Session identifier (single source of truth)
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

    # Runtime
    ENV: str
    MACHINE: str

    # Authentication
    AUTH_TYPE: str

    # Discovery
    STRICT_ENTITY_DISCOVERY: bool

    # Logging
    ENABLE_STRUCTURED_LOGS: bool
    ENABLE_JSON_PRETTY: bool
    LOG_PAYLOADS: bool
    REDACT_SENSITIVE_FIELDS: bool
    DISABLE_LOG_EMOJIS: bool
    KEEP_STRUCTURED_LOGS: int
    LOG_DIR: Path

    # Schema / behavior
    FAIL_ON_EMPTY_LIST: bool
    PERF_ITERATIONS: int

    # Reporting
    AUTO_ALLURE_REPORT: bool

    # CI / safety
    REQUIRE_ENV: bool


def config_to_safe_dict(cfg: FrameworkConfig) -> dict:
    """
    Convert FrameworkConfig into a JSON-safe dictionary.

    - Paths → strings
    - No secrets included (by design)
    """
    data = asdict(cfg)
    for k, v in data.items():
        if isinstance(v, Path):
            data[k] = str(v)
    return data


# ============================================================================
# 🔄 Configuration cache
# ============================================================================
# The framework reads environment variables only once at startup and stores
# the resolved configuration here.
#
# Every subsequent call to get_config() returns the cached configuration
# instead of reading the operating system environment again.
#
# This guarantees that every component in the framework uses exactly the
# same configuration throughout the entire test session.
# ============================================================================
# ============================================================================
_config_cache: Optional[FrameworkConfig] = None


# ============================================================================
# 🔧 Load config from environment
# ============================================================================
def _load_config_from_env() -> FrameworkConfig:
    """
    Create the framework configuration from the current environment.

    This is the only place in the framework that reads environment variables
    directly.

    Every configuration value (environment, logging options, authentication,
    reporting, etc.) is collected here and converted into a strongly typed
    FrameworkConfig object.

    The resulting object becomes the single source of truth for the rest of
    the framework.
    """

    ACTIVE_ENV = os.getenv("API_ENV") or os.getenv("ENV", "test")

    return FrameworkConfig(
        ENV=ACTIVE_ENV,
        MACHINE=os.getenv("MACHINE", "machine1").lower(),
        # Authentication method used by APIClient. Supported: oauth1 | oauth2 | jwt | basic
        AUTH_TYPE=os.getenv("AUTH_TYPE", "oauth1").lower(),
        STRICT_ENTITY_DISCOVERY=env_bool("STRICT_ENTITY_DISCOVERY", False),
        ENABLE_STRUCTURED_LOGS=env_bool("ENABLE_STRUCTURED_LOGS", True),
        ENABLE_JSON_PRETTY=env_bool("ENABLE_JSON_PRETTY", False),
        LOG_PAYLOADS=env_bool("LOG_PAYLOADS", False),
        REDACT_SENSITIVE_FIELDS=env_bool("REDACT_SENSITIVE_FIELDS", True),
        DISABLE_LOG_EMOJIS=env_bool("DISABLE_LOG_EMOJIS", False),
        KEEP_STRUCTURED_LOGS=int(os.getenv("KEEP_STRUCTURED_LOGS", "3")),
        LOG_DIR=Path(os.getenv("LOG_DIR", "reports/logs")),
        FAIL_ON_EMPTY_LIST=env_bool("FAIL_ON_EMPTY_LIST", False),
        PERF_ITERATIONS=int(os.getenv("PERF_ITERATIONS", "5")),
        AUTO_ALLURE_REPORT=env_bool("AUTO_ALLURE_REPORT", True),
        REQUIRE_ENV=env_bool("REQUIRE_ENV", False),
    )


# ============================================================================
# 🔐 Public accessors
# ============================================================================
def get_config(reload: bool = False) -> FrameworkConfig:
    """
    Return the resolved FrameworkConfig.

    Cached by default.
    """
    global _config_cache
    if reload or _config_cache is None:
        _config_cache = _load_config_from_env()
    return _config_cache


def reload_config() -> None:
    """Clear cached configuration (tests only)."""
    global _config_cache
    _config_cache = None
