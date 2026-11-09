"""
Integrate the framework's logging system into the pytest lifecycle.

This plugin is responsible for configuring logging before any tests run
and cleaning everything up when the test session finishes.

Responsibilities:
- Load logging-related configuration.
- Install the custom LogRecord factory.
- Configure console and structured JSON logging.
- Populate logging ContextVars for each test.
- Collect session metadata (environment, Git, CI).
- Restore Python's logging state during pytest shutdown.

This module acts as the bridge between pytest and the logging engine.

Architecture:

        pytest
           │
           ▼
    logging_plugin.py
           │
           ▼
     custom_logger.py
           │
           ▼
    Console / JSONL logs

The logging implementation lives in custom_logger.py.
This plugin only coordinates when and how that implementation is used.

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

from EcommerceAPI.src.configs.runtime_config import get_config

from EcommerceAPI.src.utils import log_context
from EcommerceAPI.src.utils.custom_logger import (
    is_redaction_enabled,
    redact_obj,
    set_redaction,
    set_include_payloads,
    configure_logging,
    prune_structured_logs,
    write_run_manifest,
    attach_global_logging_metadata,
    LOG_FORMAT,
    LOG_DATEFMT,
    CustomFormatter,
)

from EcommerceAPI.src.utils.env_utils import env_bool
from EcommerceAPI.src.utils.entity_discovery import extract_entity_from_nodeid

# Use the single-session id from the framework config (single source of truth)
from EcommerceAPI.src.configs.runtime_config import SESSION_ID
from EcommerceAPI.src.configs.runtime_metadata import SESSION_METADATA

# --------------------------------------------------------------------------------------
# Logger for this module
# --------------------------------------------------------------------------------------
log = logging.getLogger(__name__)

RUN_ID = os.getenv("E2E_RUN_ID") or SESSION_ID
PROCESS_ID = os.getenv("PYTEST_XDIST_WORKER") or "master"
IS_XDIST_WORKER = bool(os.getenv("PYTEST_XDIST_WORKER"))
STRUCTURED_LOGS_ENABLED = False
_RUN_ID_WORKERINPUT_KEY = "ecommerce_run_id"
_CORRELATION_PROPERTY_KEY = "ecommerce_correlation_id"
_WORKER_PROPERTY_KEY = "ecommerce_worker_id"
_RUN_PROPERTY_KEY = "ecommerce_run_id"

# --------------------------------------------------------------------------------------
# Preserve Python's original LogRecord factory
# --------------------------------------------------------------------------------------
_ORIGINAL_RECORD_FACTORY = logging.getLogRecordFactory()


def _record_factory(*args, **kwargs):
    """
    Create enriched log records for every logging call.

    Python normally creates a LogRecord whenever code calls
    logger.info(), logger.error(), and similar methods.

    This custom factory extends those records with additional
    framework information, including:

    - current test nodeid
    - test name
    - correlation ID
    - active environment

    It also performs early redaction of sensitive information
    before any logging handler receives the message.

    Every log message generated during a pytest session passes
    through this function.
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

    try:
        worker_id = log_context.worker_id.get()
    except LookupError:
        worker_id = None
    record.run_id = RUN_ID
    record.process_id = PROCESS_ID
    record.worker_id = worker_id or PROCESS_ID

    # environment tag for convenience in handlers/formatters
    record.env = get_config(reload=True).ENV

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
# Locate the project's .env file (walking upward from pytest root)
# --------------------------------------------------------------------------------------
def _locate_dotenv(start: Path) -> Optional[Path]:
    """
    Locate the nearest .env file.

    Starting from the pytest root directory, the framework walks
    up the directory tree until it finds a .env file.

    This allows pytest to be executed from different folders
    without changing configuration behaviour.
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
        default=None,
        type=int,
        help=(
            "Global number of measured requests for performance tests. "
            "When omitted, each entity uses its profile default."
        ),
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
        help=(
            "Compatibility flag; structured event logs remain compact JSONL "
            "for reliable ingestion."
        ),
    )

    group.addoption(
        "--keep-structured-runs",
        action="store",
        type=int,
        default=None,
        metavar="COUNT",
        help=(
            "Number of complete structured-log runs to retain globally "
            "(overrides KEEP_STRUCTURED_RUNS; default: 1)."
        ),
    )


# ======================================================================================
# Configure logging before test collection starts (runs once at startup)
# ======================================================================================
@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    """
    Configure the framework's logging system before any tests run.

    This hook is executed once at the beginning of every pytest
    session.

    It prepares the complete logging environment by:

    1. Loading environment configuration.
    2. Applying logging options.
    3. Installing the custom LogRecord factory.
    4. Configuring console logging.
    5. Enabling structured JSON logging when requested.
    6. Registering session metadata.

    After this hook finishes, every test uses the same logging
    configuration.
    """
    global RUN_ID, PROCESS_ID, IS_XDIST_WORKER, STRUCTURED_LOGS_ENABLED

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

    workerinput = getattr(config, "workerinput", None) or {}
    worker_env_id = os.getenv("PYTEST_XDIST_WORKER")
    IS_XDIST_WORKER = bool(worker_env_id or workerinput)
    PROCESS_ID = worker_env_id or workerinput.get("workerid") or "master"
    RUN_ID = (
        workerinput.get(_RUN_ID_WORKERINPUT_KEY)
        or (os.getenv("E2E_RUN_ID") if IS_XDIST_WORKER else None)
        or uuid.uuid4().hex
    )
    os.environ["E2E_RUN_ID"] = RUN_ID
    log_context.worker_id.set(PROCESS_ID)
    SESSION_METADATA.update(
        {
            "run_id": RUN_ID,
            "process_id": PROCESS_ID,
            "worker_id": PROCESS_ID,
        }
    )

    # 2) Resolve CLI/env toggles (CLI wins)
    opt = getattr(config, "option", None)

    enable_structured = bool(getattr(opt, "enable_structured_logs", False)) or env_bool(
        "ENABLE_STRUCTURED_LOGS", default=False
    )
    STRUCTURED_LOGS_ENABLED = enable_structured
    enable_json_pretty = bool(getattr(opt, "enable_json_pretty", False)) or env_bool(
        "ENABLE_JSON_PRETTY", default=False
    )
    log_payloads = bool(getattr(opt, "log_payloads", False)) or env_bool(
        "LOG_PAYLOADS", default=False
    )
    redact_sensitive = bool(getattr(opt, "redact_sensitive_fields", False)) or env_bool(
        "REDACT_SENSITIVE_FIELDS", default=True
    )

    # Retain complete runs globally. CLI wins over the environment setting.
    keep_structured_runs_cli = getattr(opt, "keep_structured_runs", None)
    if keep_structured_runs_cli is not None:
        try:
            keep_structured_runs = int(keep_structured_runs_cli)
        except (TypeError, ValueError):
            keep_structured_runs = 1
            log.warning(
                "Invalid CLI keep_structured_runs=%r, falling back to %s",
                keep_structured_runs_cli,
                keep_structured_runs,
            )
    else:
        ks_env = os.getenv("KEEP_STRUCTURED_RUNS")
        try:
            keep_structured_runs = int(ks_env) if ks_env is not None else 1
        except (TypeError, ValueError):
            keep_structured_runs = 1
            log.warning(
                "Invalid KEEP_STRUCTURED_RUNS=%r in env, falling back to %s",
                ks_env,
                keep_structured_runs,
            )

    if keep_structured_runs < 1:
        log.warning(
            "KEEP_STRUCTURED_RUNS must be at least 1; using 1 instead of %s",
            keep_structured_runs,
        )
        keep_structured_runs = 1

    # Warn about the removed environment name so a developer can update a
    # local .env file without silently wondering why the old value is ignored.
    if os.getenv("KEEP_STRUCTURED_LOGS") is not None:
        log.warning(
            "KEEP_STRUCTURED_LOGS is no longer used; set KEEP_STRUCTURED_RUNS. "
            "The default is 1 complete run."
        )

    # Default LOG_DIR: use pytest root / reports / logs (can be overridden by LOG_DIR env)
    log_dir_cli = getattr(opt, "log_dir", None)
    # Default: use <pytest root>/reports/logs unless overridden by CLI or LOG_DIR env
    log_dir = log_dir_cli or os.getenv("LOG_DIR") or str(rootdir / "reports" / "logs")

    # PERF_ITERATIONS is a global override. If the CLI flag is omitted, use the
    # environment value when present; otherwise each entity keeps its profile
    # default.
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
        os.environ["KEEP_STRUCTURED_RUNS"] = str(keep_structured_runs)

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
        # a test node ID; no individual test is active during configuration.
        log.info(
            "Custom LogRecord factory installed — enriches records with nodeid, test_name, "
            "correlation_id, run_id and worker identity. "
            "session_id=%s run_id=%s process_id=%s",
            SESSION_ID,
            RUN_ID,
            PROCESS_ID,
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
            env=get_config(reload=True).ENV,
            session_id=SESSION_METADATA["session_id"],
            run_id=RUN_ID,
            process_id=PROCESS_ID,
            worker_id=PROCESS_ID,
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

    # Remove the temporary startup handler once framework initialization is complete.Keeping it would duplicate
    # console output because the root logger already owns the permanent handlers.
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


@pytest.hookimpl(tryfirst=True)
def pytest_sessionstart(session):
    """Apply the framework formatter before plugins emit session-level logs.

    Pytest creates its live console handler for ``pytest_sessionstart`` using
    ``log_cli_format`` from pytest.ini. That format references test-only fields
    (nodeid and correlation_id), which are unavailable for run-level messages
    such as the configuration banner. Apply CustomFormatter while pytest's live
    handler is active so session messages render safely and match test logs.
    """
    pytest_logging = session.config.pluginmanager.get_plugin("logging-plugin")
    live_handler = getattr(pytest_logging, "log_cli_handler", None)
    if live_handler is None:
        return

    live_handler.setFormatter(
        CustomFormatter(
            LOG_FORMAT,
            datefmt=LOG_DATEFMT,
            use_emojis=not os.getenv("DISABLE_LOG_EMOJIS", "").lower()
            in ("1", "true", "yes", "on"),
        )
    )


@pytest.hookimpl(optionalhook=True)
def pytest_configure_node(node):
    """Pass the controller's run ID into each xdist worker process."""
    workerinput = getattr(node, "workerinput", None)
    if isinstance(workerinput, dict):
        workerinput[_RUN_ID_WORKERINPUT_KEY] = RUN_ID


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    """Prune old structured logs once, from the controller after workers finish."""
    if IS_XDIST_WORKER or not STRUCTURED_LOGS_ENABLED:
        return

    try:
        log_dir = Path(
            os.getenv("LOG_DIR") or Path(session.config.rootpath) / "reports" / "logs"
        )
        keep = int(os.getenv("KEEP_STRUCTURED_RUNS", "1"))
        write_run_manifest(
            log_dir,
            run_id=RUN_ID,
            process_id=PROCESS_ID,
            exit_status=int(exitstatus),
        )
        prune_structured_logs(log_dir, keep=keep, current_run_id=RUN_ID)
    except (OSError, TypeError, ValueError) as prune_err:
        log.warning(
            "Could not apply structured-log retention for run %s: %s",
            RUN_ID,
            prune_err,
            exc_info=True,
        )


# -------------------------------------------------------------------------
# Pytest teardown / unconfigure.Restore Python logging after pytest exits
# -------------------------------------------------------------------------
@pytest.hookimpl(tryfirst=True)
def pytest_unconfigure(config):
    """
    Restore Python's original logging configuration.

    The plugin modifies Python's logging system while pytest
    is running.

    This hook restores the original state so subsequent Python
    code is unaffected.

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
    Assign each collected test to its owning team.

    The team is derived automatically from the test's nodeid.

    The information is later used by structured logging,
    reporting and CI summaries.

    Effects:
      - Attaches `item.team`
      - Populates `session.teams`
    """
    teams = set()

    for item in items:
        team = extract_entity_from_nodeid(item.nodeid)
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
    Prepare logging context for a single test.

    Before pytest starts executing a test, this hook stores
    information about that test in ContextVars.

    Those values are automatically attached to every log
    message generated during the test, making it possible
    to identify:

    - which test produced the log
    - the correlation ID
    - the active nodeid

    The ContextVars are cleared again when the test finishes.
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
    Return metadata describing the current pytest session.

    The returned dictionary contains information such as:

    - session ID
    - Git commit
    - Git branch
    - CI provider

    Useful for reporting and diagnostics.
    """
    return SESSION_METADATA


# ============================================================================================
# Preserve per-test context in reports and write structured test-result logging
# ============================================================================================
@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    """Carry correlation and worker IDs with reports sent from xdist workers."""
    outcome = yield
    report = outcome.get_result()

    try:
        correlation_id = log_context.correlation_id.get()
    except LookupError:
        correlation_id = None

    report_properties = list(getattr(report, "user_properties", ()) or ())
    reserved_keys = {
        _CORRELATION_PROPERTY_KEY,
        _WORKER_PROPERTY_KEY,
        _RUN_PROPERTY_KEY,
    }
    report_properties = [
        prop
        for prop in report_properties
        if not (isinstance(prop, tuple) and prop and prop[0] in reserved_keys)
    ]
    if correlation_id:
        report_properties.append((_CORRELATION_PROPERTY_KEY, correlation_id))
    report_properties.append((_WORKER_PROPERTY_KEY, PROCESS_ID))
    report_properties.append((_RUN_PROPERTY_KEY, RUN_ID))
    report.user_properties = report_properties


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_logreport(report):
    """
    Write the final structured log entry for each executed test.

    When the test call phase finishes, the plugin records:

    - outcome
    - execution time
    - event type

    This creates one structured summary record per executed test.

    Implementation note:
    Avoid passing fields that already belong to Python's
    LogRecord object, because the custom LogRecord factory
    adds those automatically.
    """
    # In parallel runs the worker has the full live context. The controller
    # writes the one authoritative result event after receiving the report.
    if IS_XDIST_WORKER or report.when != "call":
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

    report_properties = dict(getattr(report, "user_properties", ()) or ())
    report_nodeid = getattr(report, "nodeid", None)
    report_correlation_id = report_properties.get(_CORRELATION_PROPERTY_KEY)
    report_worker_id = (
        getattr(report, "worker_id", None)
        or report_properties.get(_WORKER_PROPERTY_KEY)
        or PROCESS_ID
    )

    # Build extra using only safe keys that do not overlap LogRecord attributes.
    extra = {
        "event": "test_result",
        "outcome": getattr(report, "outcome", None),
    }
    if duration_ms is not None:
        extra["duration_ms"] = duration_ms

    nodeid_token = log_context.test_nodeid.set(report_nodeid)
    correlation_token = log_context.correlation_id.set(report_correlation_id)
    worker_token = log_context.worker_id.set(report_worker_id)
    try:
        if report.passed:
            logging.getLogger().info("✅ Test passed", extra=extra)
        elif report.failed:
            logging.getLogger().error("❌ Test failed", extra=extra)
        else:
            logging.getLogger().warning("⏭ Test skipped", extra=extra)
    finally:
        log_context.worker_id.reset(worker_token)
        log_context.correlation_id.reset(correlation_token)
        log_context.test_nodeid.reset(nodeid_token)
