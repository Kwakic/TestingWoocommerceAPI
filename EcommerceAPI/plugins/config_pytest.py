"""
Pytest integration for framework configuration.

Responsibilities:
- Provide pytest fixtures
- Apply CLI overrides
- Emit startup configuration banner

⚠️ This file is a pytest plugin.
It MUST be loaded via pytest_plugins.
It MUST NOT be imported manually.
"""

from __future__ import annotations

import logging
import pytest

from EcommerceAPI.src.configs.runtime_config import (
    SESSION_ID,
    FrameworkConfig,
    get_config,
)


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

    # CLI precedence
    if pytestconfig.getoption("--fail-on-empty-list"):
        cfg = FrameworkConfig(
            **{**cfg.__dict__, "FAIL_ON_EMPTY_LIST": True}
        )

    return cfg


@pytest.fixture(scope="session")
def fail_on_empty_list(framework_config: FrameworkConfig) -> bool:
    """Whether schema list endpoints should fail on empty responses."""
    return framework_config.FAIL_ON_EMPTY_LIST


# ============================================================================
# 📢 Startup banner (LOGGED ONCE, GUARANTEED)
# ============================================================================

def pytest_sessionstart(session):
    """
    Emit a single authoritative configuration snapshot at startup.
    """
    log = logging.getLogger("EcommerceAPI.config")
    cfg = get_config()

    log.info("================= SESSION START ====================")
    log.info("Session ID : %s", SESSION_ID, extra={
            "suppress_nodeid": True,
            "suppress_correlation": True,
        })

    log.info("================= FRAMEWORK CONFIG =================")
    log.info("AUTH_TYPE               : %s", cfg.AUTH_TYPE)
    log.info("STRICT_ENTITY_DISCOVERY : %s", cfg.STRICT_ENTITY_DISCOVERY, extra={
            "suppress_nodeid": True,
            "suppress_correlation": True,
        })
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
