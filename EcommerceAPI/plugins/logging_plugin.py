"""
Pytest logging plugin.

This plugin configures logging for pytest runs:
- Installs a LogRecord factory that enriches records with ContextVar-based fields
  (nodeid, test_name, correlation_id) and an `env` attribute.
- Performs early redaction of rendered messages.
- Coordinates console formatting (CustomFormatter) and optional structured JSONL output
  (configured via configure_logging).
- Collects session metadata (git/CI/session id) and exposes it via a fixture.
- Ensures clean teardown by restoring original LogRecord factory and closing handlers.

"""

from __future__ import annotations

import os
import sys
import uuid
import logging
from pathlib import Path
from typing import Optional

import pytest
from dotenv import load_dotenv

from EcommerceAPI.src.configs.config_loader import ENV
from EcommerceAPI.src.utils import log_context
from EcommerceAPI.src.utils.custom_logger import (
    is_redaction_enabled,
    redact_obj,
    set_redaction,
    set_include_payloads,
    configure_logging,
    attach_global_logging_metadata,
    LOG_FORMAT,
    LOG_DATEFMT,
    CustomFormatter,
)

from EcommerceAPI.src.utils.env_utils import env_bool
from EcommerceAPI.src.utils.team_discovery import extract_team_from_nodeid

# Use the single-session id from the framework config (single source of truth)
from EcommerceAPI.src.configs.runtime_config import SESSION_ID
from EcommerceAPI.src.configs.runtime_metadata import SESSION_METADATA

# --------------------------------------------------------------------------------------
# Logger for this module
# --------------------------------------------------------------------------------------
log = logging.getLogger(__name__)

# --------------------------------------------------------------------------------------
# Session metadata collection (git / CI info)
# --------------------------------------------------------------------------------------

# --------------------------------------------------------------------------------------
# LogRecord factory capture and override
# --------------------------------------------------------------------------------------
_ORIGINAL_RECORD_FACTORY = logging.getLogRecordFactory()


def _record_factory(*args, **kwargs):
    """
    Custom LogRecord factory used for the pytest run.

    - Delegates to the original factory
    - Injects ContextVar-based fields when present (test_nodeid, correlation_id)
    - Adds an `env` attribute to every record
    - Performs EARLY redaction of the fully formatted message (record.getMessage())
      to ensure sensitive data does not reach handlers.
    """
    record = _ORIGINAL_RECORD_FACTORY(*args, **kwargs)

    # nodeid / test_name: attempt to read ContextVar and set on record only when available
    try:
        nodeid = log_context.test_nodeid.get()
    except LookupError:
        nodeid = None
    if nodeid is not None:
        record.nodeid = nodeid
        # set derived test_name only when nodeid meaningful
        record.test_name = nodeid.split("::")[-1]

    # correlation_id: set only when ContextVar present
    try:
        corr = log_context.correlation_id.get()
    except LookupError:
        corr = None

    if corr is not None:
        record.correlation_id = corr

    # environment tag for convenience in handlers/formatters
    record.env = ENV

    # Only catch narrow exceptions from formatting/stringification.
    if is_redaction_enabled():
        try:
            raw_msg = record.getMessage()
            redacted = redact_obj(raw_msg)
            if not isinstance(redacted, str):
                redacted = str(redacted)
            # Replace the record message and clear args so formatters do not re-format it.
            record.msg = redacted
            record.args = ()
        except (TypeError, ValueError, AttributeError):
            # Best-effort: if redaction fails in expected ways, leave an original message intact.
            pass

    return record


# --------------------------------------------------------------------------------------
# Utility: locate .env by walking upward from pytest root
# --------------------------------------------------------------------------------------
def _locate_dotenv(start: Path) -> Optional[Path]:
    """
    Search upward from `start` for the first .env file and return its Path, or None.
    This helps make running pytest from different folders deterministic.
    """
    for p in [start] + list(start.parents):
        candidate = p / ".env"
        if candidate.is_file():
            return candidate
    return None


# ======================================================================================
# PYTEST CLI OPTIONS REGISTRATION
# ======================================================================================
def pytest_addoption(parser):
    group = parser.getgroup("custom options")

    # Lightweight logging-related flags (mirror ENV toggles if desired)
    group.addoption(
        "--fail-on-empty-list",
        action="store_true",
        default=False,
        help="Fail schema validation tests when API list endpoints return empty lists.",
    )

    group.addoption(
        "--perf-iterations",
        action="store",
        default=5,
        type=int,
        help="Number of iterations per API endpoint for performance tests (default: 5).",
    )

    # Lightweight logging-related flags (mirror ENV toggles if desired)
    group.addoption(
        "--enable-structured-logs",
        action="store_true",
        default=False,
        help="Enable structured JSONL logging for this pytest run (overrides ENABLE_STRUCTURED_LOGS env).",
    )

    group.addoption(
        "--enable-json-pretty",
        action="store_true",
        default=False,
        help="Pretty-print JSONL structured logs (overrides ENABLE_JSON_PRETTY env).",
    )


# ======================================================================================
# PYTEST CONFIGURE — the canonical startup sequence (runs once at startup)
# ======================================================================================
@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    """
    Pytest configure hook executed at startup.

    Sequence:
      - Resolve pytest rootdir and load `.env` (if present). We do not override existing env vars
        by default (load_dotenv override=False) to avoid surprising callers who set CI envs.
      - Resolve CLI/env toggles (CLI takes precedence where applicable).
      - Apply redaction and payload toggles so factory/formatters observe them.
      - Install custom LogRecord factory.
      - Apply CustomFormatter to console StreamHandlers.
      - Call configure_logging() to add structured handlers if enabled.
      - Attach GLOBAL_METADATA for structured logs.
      - Optionally create an auto HTML report path.
    """
    # Resolve rootdir safely (fall back to cwd in odd contexts)
    try:
        rootdir = Path(config.rootpath)
    except AttributeError:
        rootdir = Path.cwd()

    # 1) Load .env by searching upward from pytest root — do not override existing env vars by default.
    env_path = _locate_dotenv(rootdir) or (rootdir / ".env")
    if env_path and env_path.is_file():
        try:
            load_dotenv(dotenv_path=str(env_path), override=False)
            log.debug("Loaded .env from: %s", env_path)
        except Exception as load_err:
            # Narrow failure: if dotenv fails unexpectedly, log debug but continue.
            log.debug(
                "Failed loading .env from %s: %s", env_path, load_err, exc_info=True
            )

    # 2) Resolve CLI/env toggles (CLI wins)
    opt = getattr(config, "option", None)

    enable_structured = bool(getattr(opt, "enable_structured_logs", False)) or env_bool(
        "ENABLE_STRUCTURED_LOGS", default=False
    )
    enable_json_pretty = bool(getattr(opt, "enable_json_pretty", False)) or env_bool(
        "ENABLE_JSON_PRETTY", default=False
    )
    log_payloads = bool(getattr(opt, "log_payloads", False)) or env_bool(
        "LOG_PAYLOADS", default=False
    )
    redact_sensitive = bool(getattr(opt, "redact_sensitive_fields", False)) or env_bool(
        "REDACT_SENSITIVE_FIELDS", default=True
    )

    # keep_structured_logs: prefer CLI, then env, then default 3
    keep_structured_cli = getattr(opt, "keep_structured_logs", None)
    if keep_structured_cli is not None:
        try:
            keep_structured_logs = int(keep_structured_cli)
        except (TypeError, ValueError):
            keep_structured_logs = 3
            log.warning(
                "Invalid CLI keep_structured_logs=%r, falling back to %s",
                keep_structured_cli,
                keep_structured_logs,
            )
    else:
        ks_env = os.getenv("KEEP_STRUCTURED_LOGS")
        try:
            keep_structured_logs = int(ks_env) if ks_env is not None else 3
        except (TypeError, ValueError):
            keep_structured_logs = 3
            log.warning(
                "Invalid KEEP_STRUCTURED_LOGS=%r in env, falling back to %s",
                ks_env,
                keep_structured_logs,
            )

    # Default LOG_DIR: use pytest root / reports / logs (can be overridden by LOG_DIR env)
    log_dir_cli = getattr(opt, "log_dir", None)
    # Default: use <pytest root>/reports/logs unless overridden by CLI or LOG_DIR env
    log_dir = log_dir_cli or os.getenv("LOG_DIR") or str(rootdir / "reports" / "logs")

    # PERF_ITERATIONS: allow PERF_ITERATIONS env var to override the default when the CLI flag wasn't provided.
    # Rationale: pytest_addoption registers --perf-iterations with a default; to allow .env/CI to change it without
    # requiring the user to pass the CLI flag, we update config.option only when the CLI argument is absent.
    try:
        # Only consider env override if the user didn't explicitly pass the CLI flag.
        # Use startswith to match both "--perf-iterations" and "--perf-iterations=<value>"
        argv_has_perf = any(arg.startswith("--perf-iterations") for arg in sys.argv)
        if not argv_has_perf:
            perf_env = os.getenv("PERF_ITERATIONS")
            if perf_env is not None:
                try:
                    config.option.perf_iterations = int(perf_env)
                    log.debug(
                        "Using PERF_ITERATIONS from env: %s",
                        config.option.perf_iterations,
                    )
                except (TypeError, ValueError):
                    log.warning(
                        "Invalid PERF_ITERATIONS=%r in env; keeping existing value %r",
                        perf_env,
                        getattr(config.option, "perf_iterations", None),
                    )
    except Exception as perf_err:
        # Defensive: do not break pytest startup for unexpected errors here (nothing here should abort pytest startup;
        # surface debug info.)
        log.debug(
            "Failed to apply PERF_ITERATIONS from env: %s", perf_err, exc_info=True
        )

    # 3) Apply redaction/payload toggles (so factory/formatters see consistent flags)
    set_redaction(bool(redact_sensitive))
    set_include_payloads(bool(log_payloads))

    # 4) Install record factory now that toggles are applied
    try:
        logging.setLogRecordFactory(_record_factory)
        # NOTE: do not emit the startup "Installed..." message until we attach a formatter/handler,
        # so that message is rendered with CustomFormatter (includes [ENV: ...], etc.).
    except TypeError as install_err:
        # Signature mismatch or other TypeError — surface as error-level for triage (narrow catch)
        log.exception(
            "Failed to install LogRecord factory (TypeError): %s", install_err
        )

    # 5) Suppress noisy third-party loggers (coarse-level)
    NOISY_LOGGERS = [
        "oauthlib",
        "urllib3",
        "requests_oauthlib",
        "faker",
        "sqlalchemy.engine",
        "sqlalchemy.pool",
        "sqlalchemy.dialects",
    ]
    for noisy in NOISY_LOGGERS:
        logging.getLogger(noisy).setLevel(logging.WARNING)

    # Small filter example to mute faker lines on console handlers
    class NoisyFilter(logging.Filter):
        def filter(self, record):
            return not record.name.startswith("faker")

    for handler in logging.getLogger().handlers:
        if isinstance(handler, logging.StreamHandler):
            handler.addFilter(NoisyFilter())

    # -------------------------
    # Prepare and apply formatter
    # -------------------------
    # Keep `formatter` available for reuse later (may be None if creation fails).
    formatter: Optional[logging.Formatter] = None
    try:
        # Create formatter and apply to current StreamHandlers.
        formatter = CustomFormatter(
            LOG_FORMAT,
            datefmt=LOG_DATEFMT,
            use_emojis=not bool(
                os.getenv("DISABLE_LOG_EMOJIS", "").lower()
                in ("1", "true", "yes", "on")
            ),
        )
        root_logger = logging.getLogger()
        for handler in list(root_logger.handlers):
            if isinstance(handler, logging.StreamHandler):
                handler.setFormatter(formatter)
    except (TypeError, ValueError, AttributeError) as fmt_err:
        # Best-effort; do not fail pytest startup if formatting changes fail
        log.debug(
            "Applying CustomFormatter to root handlers failed: %s",
            fmt_err,
            exc_info=True,
        )

    # 6) Internal noisy loggers: remove their StreamHandlers but keep propagation, lower level
    INTERNAL_NOISY = [
        "EcommerceAPI.src.clients.api_client",
        # extend as needed
    ]
    for name in INTERNAL_NOISY:
        lg = logging.getLogger(name)
        lg.handlers[:] = [
            h for h in lg.handlers if not isinstance(h, logging.StreamHandler)
        ]
        lg.propagate = True
        if lg.getEffectiveLevel() > logging.DEBUG:
            lg.setLevel(logging.DEBUG)

    # 7) Call configure_logging() (idempotent). configure_logging is responsible for creating structured files when
    # enabled. Ensure CLI-driven toggles are visible to configure_logging() which reads environment variables.
    # # This keeps configure_logging idempotent and avoids changing its signature.
    try:
        if enable_structured:
            os.environ["ENABLE_STRUCTURED_LOGS"] = "1"
        if enable_json_pretty:
            os.environ["ENABLE_JSON_PRETTY"] = "1"
        if log_dir:
            os.environ["LOG_DIR"] = str(log_dir)

        # propagate retention policy for structured logs
        os.environ["KEEP_STRUCTURED_LOGS"] = str(keep_structured_logs)

        configure_logging()
    except (OSError, RuntimeError, ValueError) as cfg_err:
        log.exception("configure_logging() failed during pytest startup: %s", cfg_err)

    # -------------------------------------------------------------------------
    # Re-apply CustomFormatter AFTER configure_logging()
    # -------------------------------------------------------------------------
    # Some handlers (or configure_logging) may have been added/modified by the previous call.
    # Re-applying the CustomFormatter here ensures the startup messages that follow are formatted
    # with the intended template (so they include [ENV: ...], nodeid blocks, etc.).
    try:
        # Reuse previously created formatter if available; else create one.
        if CustomFormatter and LOG_FORMAT:
            if formatter is None:
                formatter = CustomFormatter(
                    LOG_FORMAT,
                    datefmt=LOG_DATEFMT,
                    use_emojis=not bool(
                        os.getenv("DISABLE_LOG_EMOJIS", "").lower()
                        in ("1", "true", "yes", "on")
                    ),
                )
            root_logger = logging.getLogger()
            for handler in list(root_logger.handlers):
                if isinstance(handler, logging.StreamHandler):
                    # set formatter explicitly (defensive)
                    handler.setFormatter(formatter)
    except (TypeError, ValueError, AttributeError) as reapply_err:
        log.debug(
            "Re-applying CustomFormatter to root handlers failed: %s",
            reapply_err,
            exc_info=True,
        )

    # -------------------------------------------------------------------------
    # Ensure startup messages are formatted with CustomFormatter
    # -------------------------------------------------------------------------
    # Some handlers may be created or modified by pytest or configure_logging.
    # To guarantee the initial debug/info messages are formatted with our CustomFormatter (so they include [ENV: ...]),
    # attach a short-lived temporary StreamHandler using the same formatter. We'll remove it after the auto-html-report
    # logic below to avoid duplicate handlers.
    temp_startup_handler = None
    try:
        if CustomFormatter and LOG_FORMAT:
            # Prefer the previously created `formatter` when available; otherwise create a fresh one.
            if formatter is not None:
                startup_formatter = formatter
            else:
                startup_formatter = CustomFormatter(
                    LOG_FORMAT,
                    datefmt=LOG_DATEFMT,
                    use_emojis=not bool(
                        os.getenv("DISABLE_LOG_EMOJIS", "").lower()
                        in ("1", "true", "yes", "on")
                    ),
                )
            root_logger = logging.getLogger()
            temp_startup_handler = logging.StreamHandler(sys.stdout)
            temp_startup_handler.setFormatter(startup_formatter)
            temp_startup_handler.setLevel(logging.DEBUG)
            # Give the temp handler a stable name so unconfigure can find it
            temp_startup_handler.name = "ecommerce_temp_startup"
            # Add it temporarily so subsequent log.*() calls here use the intended format
            root_logger.addHandler(temp_startup_handler)
    except (TypeError, ValueError, OSError) as temp_err:
        log.debug(
            "Failed to attach temporary startup handler: %s", temp_err, exc_info=True
        )

    # Emit the "Installed custom LogRecord factory." startup message but only AFTER the factory is installed and a
    # formatter/handler are in place so it is formatted the same way as before (including nodeid and correlation id
    # sentinels).
    try:
        # NOTE: pass extra={"suppress_nodeid": True} so this startup message does not display
        # the nodeid block (which would otherwise be "[🧪 unknown]").
        log.info(
            "Custom LogRecord factory installed — enriches records with nodeid, test_name, "
            "correlation_id and env. session_id=%s",
            SESSION_ID,
            extra={"suppress_nodeid": True},
        )
    except (TypeError, ValueError, AttributeError) as emit_err:
        # Catch narrow, expected logging-related errors only.
        log.debug(
            "Failed emitting LogRecord factory install message: %s",
            emit_err,
            exc_info=True,
        )

    # 8) Attach GLOBAL_METADATA (git/CI/session) for structured logs; keep handling narrow for malformed metadata
    try:
        attach_global_logging_metadata(
            env=ENV,
            session_id=SESSION_METADATA["session_id"],
            ci_info={
                "ci_provider": SESSION_METADATA["ci"]["provider"],
                "ci_job_id": SESSION_METADATA["ci"]["job_id"],
                "is_ci": SESSION_METADATA["ci"]["is_ci"],
            },
            git_info={
                "git_commit": SESSION_METADATA["git"]["commit"],
                "git_branch": SESSION_METADATA["git"]["branch"],
            },
        )
        # Suppress nodeid for this session-level message too
        log.info(
            "GLOBAL_METADATA attached: %s",
            SESSION_METADATA,
            extra={"suppress_nodeid": True},
        )
    except (KeyError, TypeError, ValueError) as meta_err:
        log.debug(
            "Failed to attach GLOBAL_METADATA due to malformed SESSION_METADATA: %s",
            meta_err,
            exc_info=True,
        )

    # Remove the temporary startup handler now that we've emitted the startup lines.
    # NOTE!!! If you remove the block below, it will generate logs twice!!!
    try:
        if temp_startup_handler is not None:
            logging.getLogger().removeHandler(temp_startup_handler)
    except (ValueError, RuntimeError) as rem_temp_err:
        # don't fail pytest startup if removing fails; log a narrow exception
        log.debug(
            "Failed to remove temporary startup handler: %s",
            rem_temp_err,
            exc_info=True,
        )


# ----------------------------
# Pytest teardown / unconfigure
# ----------------------------
@pytest.hookimpl(tryfirst=True)
def pytest_unconfigure(config):
    """
    Restore logging state modified during pytest_configure to avoid leaking handles or
    altering the shared logging behavior after pytest completes.

    - Restore the original LogRecord factory.
    - Remove any temporary startup handler that might remain.
    - Close and remove any structured JSONL handlers we added.
    """
    # Restore original LogRecord factory (narrow catch)
    try:
        logging.setLogRecordFactory(_ORIGINAL_RECORD_FACTORY)
    except Exception as restore_err:
        # Unexpected but non-fatal; surface for triage.
        log.debug(
            "Failed to restore original LogRecord factory: %s",
            restore_err,
            exc_info=True,
        )

    root = logging.getLogger()

    # Defensive: remove any leftover temporary startup handler created during configure
    try:
        for h in list(root.handlers):
            if getattr(h, "name", "") == "ecommerce_temp_startup":
                try:
                    root.removeHandler(h)
                except Exception as remove_temp_err:
                    log.debug(
                        "Failed removing temporary startup handler %s: %s",
                        h,
                        remove_temp_err,
                        exc_info=True,
                    )
    except Exception as scan_err:
        log.debug(
            "Error while scanning handlers for temp startup removal: %s",
            scan_err,
            exc_info=True,
        )

    # Close and remove structured JSONL handlers we added during configure_logging
    for handler in list(root.handlers):
        if getattr(handler, "name", None) == "EcommerceAPI_structured_team_jsonl":
            try:
                handler.close()
            except Exception as close_err:
                log.debug(
                    "Failed closing structured handler %s: %s",
                    handler,
                    close_err,
                    exc_info=True,
                )
            try:
                root.removeHandler(handler)
            except Exception as remove_err:
                log.debug(
                    "Failed removing structured handler %s: %s",
                    handler,
                    remove_err,
                    exc_info=True,
                )


# ======================================================================================
# Discover teams dynamically
# ======================================================================================
@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(session, config, items):
    """
    Discover teams dynamically from collected test nodeids.

    Effects:
      - Attaches `item.team`
      - Populates `session.teams`
    """
    teams = set()

    for item in items:
        team = extract_team_from_nodeid(item.nodeid)
        item.team = team
        if team:
            teams.add(team)

    session.teams = teams


# ======================================================================================
# Per-test ContextVar lifecycle population (single, safe hook)
# ======================================================================================
@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_protocol(item):
    """
    Ensure ContextVars are set as early as possible for the whole test lifecycle so
    the record factory and formatters can see nodeid/correlation_id for any logs emitted
    during setup/call/teardown.

    We set tokens here and reset them after the protocol completes.

    Notes on exception handling:
      - Reading a ContextVar may raise LookupError when it's not set for this context;
        we catch LookupError only.
      - Resetting a ContextVar with an invalid token raises ValueError; we catch ValueError
        only and log a debug message so failures are visible for triage.
      - We avoid broad except Exception: blocks to reduce masking real errors.
    """
    # Defensive: re-apply CustomFormatter to StreamHandlers at test start.
    # This helps when pytest or other plugins add/replace handlers after pytest_configure.
    try:
        if CustomFormatter and LOG_FORMAT:
            _formatter = CustomFormatter(
                LOG_FORMAT,
                datefmt=LOG_DATEFMT,
                use_emojis=not os.getenv("DISABLE_LOG_EMOJIS", "").lower()
                in ("1", "true", "yes", "on"),
            )
            _root = logging.getLogger()
            for _h in list(_root.handlers):
                if isinstance(_h, logging.StreamHandler):
                    _h.setFormatter(_formatter)
    except (TypeError, ValueError, AttributeError) as runtime_fmt_err:
        log.debug(
            "Re-applying CustomFormatter at runtest_protocol failed: %s",
            runtime_fmt_err,
            exc_info=True,
        )

    # Set nodeid and correlation_id early (do NOT synthesize defaults here)
    nodeid_token = log_context.test_nodeid.set(item.nodeid)
    corr_token = log_context.correlation_id.set(str(uuid.uuid4())[:8])

    # Optional suppressed debug (avoid recursion into formatter)
    try:
        corr_val = log_context.correlation_id.get()
    except LookupError:
        corr_val = None
    # logging itself shouldn't raise; allow any unexpected logging errors to surface
    log.debug(
        "pytest_runtest_protocol set correlation_id=%s nodeid=%s",
        corr_val or "-",
        item.nodeid,
        extra={"suppress_nodeid": True},
    )

    try:
        yield
    finally:
        # Reset tokens after the full test protocol completes; catch only the documented ValueError
        try:
            log_context.correlation_id.reset(corr_token)
        except ValueError as ve:
            log.debug(
                "Failed to reset correlation_id ContextVar (ValueError): %s",
                ve,
                exc_info=True,
            )

        try:
            log_context.test_nodeid.reset(nodeid_token)
        except ValueError as ve:
            log.debug(
                "Failed to reset test_nodeid ContextVar (ValueError): %s",
                ve,
                exc_info=True,
            )


# ======================================================================================
# Fixture - Expose session metadata fixture to tests
# ======================================================================================
@pytest.fixture(scope="session")
def session_metadata():
    """
    Return a dictionary with session metadata (git commit, branch, CI provider, session id).
    This fixture is session-scoped and intended for tests or reporting utils that need environment metadata.
    """
    return SESSION_METADATA


# ============================================================================================
# Write Structured JSON test-result logging (call phase)
# ============================================================================================
@pytest.hookimpl(tryfirst=True)
def pytest_runtest_logreport(report):
    """
    Called for each test report phase. For the 'call' phase:
      - compute a robust duration_ms and attach it to the report object (when possible)
      - emit one structured log record with event=test_result, outcome and duration_ms
    Notes:
      - Avoid passing keys in `extra` that collide with LogRecord attributes (e.g. 'test_name', 'nodeid',
        'correlation_id', 'env', etc.) — logging.makeRecord will raise KeyError if you do.
      - The LogRecord factory already populates record.nodeid and record.test_name for formatters to use.
    """
    if report.when != "call":
        return

    # Safely compute duration in milliseconds
    try:
        dur = getattr(report, "duration", None)
        duration_ms = round(float(dur) * 1000, 2) if dur is not None else None
    except (TypeError, ValueError, AttributeError):
        duration_ms = None

    # Attach to the report object for downstream consumers/plugins that may inspect it.
    try:
        report.duration_ms = duration_ms
    except (AttributeError, TypeError):
        pass

    # Build extra using only safe keys that do not overlap LogRecord attributes.
    # We intentionally do NOT include "test_name" or "nodeid" here because those are added by record factory.
    extra = {
        "event": "test_result",
        "outcome": getattr(report, "outcome", None),
    }
    if duration_ms is not None:
        extra["duration_ms"] = duration_ms

    logging.getLogger().info("✨ Test completed", extra=extra)
