"""
Unified Logging Module for API Test Framework
=============================================

This module configures two complementary logging targets:

1. Human-readable console output
   - Rich formatting (nodeid, env, emojis unless disabled)
   - Redaction of sensitive fields
   - No file-based .log output for human logs (console via pytest live-logging is the human surface)

2. Optional structured JSONL file logging (CI-friendly, opt-in)
   - One JSON object per line
   - Redaction of sensitive fields
   - Optional payload inclusion (env or runtime toggle)
   - Includes CI metadata (ci_provider, job_id), git metadata (branch, commit),
    session_id, test_name, status_code, duration_ms, url, env, etc.
   - If enabled, rotates old structured logs according to KEEP_STRUCTURED_LOGS (default: 3)

Environment variables
---------------------
REDACT_SENSITIVE_FIELDS   (default: on)
LOG_PAYLOADS              (default: off)
ENABLE_STRUCTURED_LOGS    (default: off)  # structured JSONL writing is opt-in
ENABLE_JSON_PRETTY        (pretty-print JSON logs)
DISABLE_LOG_EMOJIS        (disable emojis in console)
LOG_DIR                   (override logs directory)
KEEP_STRUCTURED_LOGS      (files to keep, default 3; applies only when structured logging is enabled)

Runtime toggles
---------------
set_redaction(bool)
set_include_payloads(bool)

Security
--------
Redaction occurs in:
  - Console formatter (CustomFormatter)
  - JSONFormatter (structured JSONL)

Redaction covers:
  - password, token, api_key, client_secret, bearer, private_key, etc.
  - quoted and unquoted patterns
  - "Authorization: Bearer <token>"

This module is safe-by-default and production-ready.

Highlights of fixes applied:
 - Formatters no longer treat ContextVar defaults ("-" / "unknown") as "missing".
   They accept the values produced by the LogRecord factory (which in turn
   reads ContextVars). This prevents accidental dropping of nodeid/correlation_id.
 - JSONFormatter always includes GLOBAL_METADATA entries, and preserves sentinel
   defaults unless you explicitly want to filter them later.
 - configure_logging remains idempotent and creates structured JSONL only when
   ENABLE_STRUCTURED_LOGS is set.
"""

import os
import sys
import re
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Iterable, Optional, Dict, TextIO

from EcommerceAPI.src.utilities import log_context
from EcommerceAPI.src.configs.config_loader import ENV
from EcommerceAPI.src.utilities.date_timestamp_utils import to_iso_utc
from EcommerceAPI.src.utilities.team_discovery import extract_team_from_nodeid

# Module logger — used for internal debug messages in this module.
log = logging.getLogger(__name__)

# ==============================================================================================
# Advertised exports for external consumers (conftest / CI glue)
# ==============================================================================================
# LAST_STRUCTURED_LOG: when configure_logging() creates a structured JSONL file, this is set to its path.
LAST_STRUCTURED_LOG: Optional[str] = None

# GLOBAL_METADATA: dictionary injected by conftest at startup containing env/session/git/CI info.
GLOBAL_METADATA: Dict[str, Any] = {}


def attach_global_logging_metadata(env: str, session_id: str, ci_info: dict, git_info: dict) -> None:
    """
    Attach global metadata that will be injected into every structured JSON log entry.

    Called once from conftest after configure_logging to populate metadata included in every structured log entry.

    This should be called once after configure_logging() so JSONFormatter includes these keys.
    Example keys added: env, session_id, ci_provider, ci_job_id, is_ci, git_commit, git_branch.
    """
    GLOBAL_METADATA.update({
        "env": env,
        "session_id": session_id,
        **ci_info,
        **git_info,
    })


# ----------------------------------------------------------------------
# Module environment toggles (import-time defaults, adjustable at runtime)
# ----------------------------------------------------------------------
_REDACT_ENABLED = os.getenv("REDACT_SENSITIVE_FIELDS", "1").lower() in ("1", "true", "yes", "on")
_INCLUDE_PAYLOADS = os.getenv("LOG_PAYLOADS", "").lower() in ("1", "true", "yes", "on")


def set_redaction(enabled: bool) -> None:
    """Enable or disable automatic redaction at runtime."""
    global _REDACT_ENABLED
    _REDACT_ENABLED = bool(enabled)


def is_redaction_enabled() -> bool:
    """Return whether automatic redaction is currently enabled."""
    return bool(_REDACT_ENABLED)


def set_include_payloads(enabled: bool) -> None:
    """Control whether structured logs include request/response payloads."""
    global _INCLUDE_PAYLOADS
    _INCLUDE_PAYLOADS = bool(enabled)


def is_include_payloads() -> bool:
    """Return whether payload inclusion in structured logs is enabled."""
    return bool(_INCLUDE_PAYLOADS)


# ----------------------------------------------------------------------
# Sensible default sensitive keys (extend if your app has more secrets)
# ----------------------------------------------------------------------
DEFAULT_SENSITIVE_KEYS = {
    "password",
    "user_pass",
    "secret",
    "token",
    "token_secret",
    "api_key",
    "apikey",
    "pwd",
    "authorization",
    "bearer",
    "access_token",
    "client_secret",
    "private_key",
}


# ----------------------------------------------------------------------
# Recursive redaction helper
# ----------------------------------------------------------------------
def redact_obj(obj: Any, sensitive_keys: Optional[Iterable[str]] = None) -> Any:
    """
    Recursively redact sensitive values in dict/list/tuple and redact strings via regex.

    Behavior summary:
    - If redaction is disabled via is_redaction_enabled(), returns obj unchanged.
    - If obj is a dict -> returns a new dict with sensitive keys masked ('***').
    - If obj is a list/tuple -> returns a new sequence with elements redacted.
    - If obj is a str -> performs regex-based redaction for common shapes.
    - Otherwise returns obj unchanged.
    - Only narrow exceptions are caught (TypeError, ValueError, AttributeError) to avoid masking bugs.
    """
    if not is_redaction_enabled():
        return obj

    if sensitive_keys is None:
        sensitive_keys = DEFAULT_SENSITIVE_KEYS

    # sensitive_keys = sensitive_keys or DEFAULT_SENSITIVE_KEYS (the same as above)

    try:
        # Dict: redact keys and recurse on values
        if isinstance(obj, dict):
            out = {}
            for k, v in obj.items():
                try:
                    if isinstance(k, str) and k.lower() in sensitive_keys:
                        out[k] = "***"
                    else:
                        out[k] = redact_obj(v, sensitive_keys)
                except (TypeError, ValueError, AttributeError):
                    # Best-effort fallback: stringify then redact
                    try:
                        out[k] = redact_obj(str(v), sensitive_keys)
                    except (TypeError, ValueError):
                        out[k] = "***"
            return out

        # List / tuple
        if isinstance(obj, (list, tuple)):
            seq = []
            for v in obj:
                try:
                    seq.append(redact_obj(v, sensitive_keys))
                except (TypeError, ValueError, AttributeError):
                    try:
                        seq.append(redact_obj(str(v), sensitive_keys))
                    except (TypeError, ValueError):
                        seq.append("***")
            return seq if isinstance(obj, list) else tuple(seq)

        # String: regex-based redaction
        if isinstance(obj, str):
            s = obj
            lower = s.lower()
            # Fast path: if none of the keys appear in the lower-cased string, skip regex.
            if not any(k in lower for k in sensitive_keys):
                return s

            keys_re = "|".join(re.escape(k) for k in sensitive_keys)
            # Pattern: "key": "value" OR 'key': 'value'
            s = re.sub(
                rf'(?i)(["\']?)\b({keys_re})\1\s*[:=]\s*(["\'])(.*?)\3',
                lambda m: f'{m.group(1)}{m.group(2)}{m.group(1)}: {m.group(3)}***{m.group(3)}',
                s,
            )
            # Pattern: key = value (unquoted)
            s = re.sub(
                rf'(?i)\b({keys_re})\b\s*[:=]\s*([^\s,"\']+)',
                lambda m: f"{m.group(1)}=***",
                s,
            )
            # Pattern: Authorization: Bearer <token>
            s = re.sub(r'(?i)(authorization\s*:\s*bearer\s+)[^\s,]+', r'\1***', s)
            return s

        # Non-container, non-string types -> return as-is
        return obj
    except (TypeError, ValueError, AttributeError):
        # Fallback to string-level redaction if expected errors occur
        try:
            return redact_obj(str(obj), sensitive_keys)
        except (TypeError, ValueError):
            return "***"


# ----------------------------------------------------------------------
# Human log format uses nodeid_block and env_block computed by CustomFormatter
# ----------------------------------------------------------------------

LOG_FORMAT = (
    "[%(asctime)s] [%(levelname)-8s] "
    "%(nodeid_block)s%(correlation_block)s%(env_block)s%(message)s"
)

# LOG_FORMAT = "[%(asctime)s] [%(levelname)-8s] %(nodeid_block)s%(env_block)s%(message)s"
# LOG_FORMAT = "[%(asctime)s] [%(levelname)-8s] [🧪 %(nodeid)s] [🔗 %(correlation_id)s] %(message)s"
LOG_DATEFMT = "%H:%M:%S"


# ----------------------------------------------------------------------
# 🖌 Custom human formatter (respects explicit LogRecord attributes; builds nodeid & env blocks)
# ----------------------------------------------------------------------
class CustomFormatter(logging.Formatter):
    """
    Console formatter with nodeid/env/correlation blocks and optional emoji stripping.

    Human-friendly formatter.
    - Adds nodeid_block, correlation_block, and env_block to the record for use in LOG_FORMAT.
    - Respects record.suppress_nodeid.
    - Performs message redaction when enabled.
    - Optionally strips emojis when DISABLE_LOG_EMOJIS is set.
    """

    SENSITIVE_KEYS = DEFAULT_SENSITIVE_KEYS

    def __init__(self, fmt=None, datefmt=None, style='%', use_emojis=True):
        super().__init__(fmt, datefmt, style)
        env_disable = os.getenv("DISABLE_LOG_EMOJIS", "").lower() in ("1", "true", "yes", "on")
        self.use_emojis = use_emojis and not env_disable

    @staticmethod
    def remove_emojis(msg: str) -> str:
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"
            "\U0001F300-\U0001F5FF"
            "\U0001F680-\U0001F6FF"
            "\U0001F1E0-\U0001F1FF"
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+",
            flags=re.UNICODE
        )
        return emoji_pattern.sub("", msg)

    def format(self, record):
        """
        Build nodeid_block, correlation_block, and env_block for human display.

        Rules:
        - Preserve record-provided values (including "unknown" or "-").
        - Only fall back to ContextVars when the attribute is missing.
        - Hide correlation block when correlation_id is missing or sentinel ("-").
        """

        # ------------------------------------------------------------
        # nodeid_block (suppressible)
        # ------------------------------------------------------------
        if getattr(record, "suppress_nodeid", False):
            record.nodeid_block = ""
        else:
            existing_nodeid = getattr(record, "nodeid", None)
            if existing_nodeid not in (None, "", "unknown"):
                nodeid_val = existing_nodeid
            else:
                nodeid_val = None
                nodeid_var = getattr(log_context, "test_nodeid", None)
                if nodeid_var is not None:
                    try:
                        nodeid_val = nodeid_var.get()
                    except LookupError:
                        nodeid_val = None

            record.nodeid_block = f"[🧪 {nodeid_val}] " if nodeid_val else ""

        # ------------------------------------------------------------
        # env_block (always safe to show when present)
        # ------------------------------------------------------------
        env_val = getattr(record, "env", None)
        record.env_block = f"[ENV: {env_val}] " if env_val else ""

        # ------------------------------------------------------------
        # correlation_id fallback (populate record.correlation_id)
        # ------------------------------------------------------------
        existing_corr = getattr(record, "correlation_id", None)
        if existing_corr not in (None, ""):
            # keep record-provided value (including "-")
            pass
        else:
            corr_var = getattr(log_context, "correlation_id", None)
            if corr_var is None:
                record.correlation_id = None
            else:
                try:
                    record.correlation_id = corr_var.get()
                except LookupError:
                    record.correlation_id = None

        # ------------------------------------------------------------
        # correlation_block (human display only)
        # ------------------------------------------------------------
        corr_val = getattr(record, "correlation_id", None)
        if corr_val not in (None, "", "-"):
            record.correlation_block = f"[🔗 {corr_val}] "
        else:
            record.correlation_block = ""

        # ------------------------------------------------------------
        # Message redaction + optional emoji stripping
        # ------------------------------------------------------------
        if is_redaction_enabled():
            try:
                raw = record.getMessage()
                redacted = redact_obj(raw, self.SENSITIVE_KEYS)
                if not isinstance(redacted, str):
                    redacted = str(redacted)
                if not self.use_emojis:
                    redacted = self.remove_emojis(redacted)
                record.msg = redacted
                record.args = ()
            except (TypeError, ValueError, AttributeError):
                pass  # leave the original message intact

        return super().format(record)


# ----------------------------------------------------------------------
# JSON Formatter for structured logs (includes env and session_id if set)
# ----------------------------------------------------------------------
class JSONFormatter(logging.Formatter):
    """
    - Structured JSON formatter that emits one JSON object per line.
    - Respects is_include_payloads() to optionally omit huge payload bodies.
    - Uses narrow exception handling for serialization fallbacks.

    Includes known extras: method, endpoint, status, duration, event, payload, env, session_id.
    Skips nodeid/correlation_id when they are sentinel defaults to avoid noise.

    Error handling:
      - Be explicit about exceptions when converting timestamp and when attempting json.dumps on values.
      - For JSON serialization of additional fields, catch TypeError/ValueError (the common cases) and fall back to
        str(val).
    """

    def __init__(self, pretty: bool = False, sensitive_keys: Optional[Iterable[str]] = None):
        super().__init__()
        self.pretty = pretty
        self.sensitive_keys = sensitive_keys or DEFAULT_SENSITIVE_KEYS

    def _redact_for_json(self, val: Any) -> Any:
        """
        Return a json-serializable redacted value (best-effort).
        - If redaction disabled -> try to return val if serializable else str(val).
        - If redaction enabled -> redact then ensure serializability; fall back to strings or
          '<unserializable>' placeholder.
        """
        if not is_redaction_enabled():
            try:
                json.dumps(val)
                return val
            except (TypeError, ValueError):
                try:
                    return str(val)
                except (TypeError, ValueError, AttributeError):
                    return "<unserializable>"

        # Redaction path: redact first, then ensure serializability with safe fallbacks to a string representation.
        try:
            redacted = redact_obj(val, self.sensitive_keys)
            try:
                json.dumps(redacted)
                return redacted
            except (TypeError, ValueError):
                # Try stringifying the redacted object and re-redacting it.
                try:
                    redacted_str = redact_obj(str(redacted), self.sensitive_keys)
                    # If the re-redacted string is still JSON-serializable, return it; else return its str.
                    try:
                        json.dumps(redacted_str)
                        return redacted_str
                    except (TypeError, ValueError):
                        return str(redacted_str)
                except (TypeError, ValueError, AttributeError):
                    try:
                        return str(redacted)
                    except (TypeError, ValueError, AttributeError):
                        return "<unserializable>"
        except (TypeError, ValueError, AttributeError):
            # Final fallback: attempt to redact stringified original value
            try:
                return redact_obj(str(val), self.sensitive_keys)
            except (TypeError, ValueError, AttributeError):
                return "<unserializable>"

    def format(self, record: logging.LogRecord) -> str:
        """
        Format a LogRecord into a JSON string.

        - Uses to_iso_utc for stable, microsecond-stripped UTC timestamps with 'Z'.
        - Injects GLOBAL_METADATA (CI/git/session) into every record.
        - Includes nodeid/correlation_id only when meaningful to avoid noise.
        - Redacts extras and falls back to safe string forms on serialization errors.
        """
        # timestamp (robust to odd underlying values)
        try:
            record_time = to_iso_utc(datetime.fromtimestamp(record.created, timezone.utc))
        except (OverflowError, OSError, ValueError):
            # Fallback that still produces a stable UTC string with 'Z'
            # Use timezone-aware now instead of deprecated datetime.utcnow()
            record_time = to_iso_utc(datetime.now(timezone.utc))

        # Main message (redacted and normalized)
        raw_message = record.getMessage()
        message = self._redact_for_json(raw_message)
        if not isinstance(message, str):
            message = str(message)

        # Base object
        obj: Dict[str, Any] = {
            "timestamp": record_time,
            "level": record.levelname,
            "logger": record.name,
            "message": message,
        }

        # Inject global metadata (ci/git/session/env etc.)
        if GLOBAL_METADATA:
            # Do not overwrite core keys if GLOBAL_METADATA contains them unintentionally.
            for k, v in GLOBAL_METADATA.items():
                if k not in obj:  # prevent overwriting reserved keys
                    obj[k] = v

        # include nodeid/correlation_id only when present (do not treat "unknown" specially)
        nodeid_val = getattr(record, "nodeid", None)
        if nodeid_val not in (None, ""):
            obj["nodeid"] = nodeid_val

        corr_val = getattr(record, "correlation_id", None)
        if corr_val is not None:
            obj["correlation_id"] = corr_val

        # Extras: include known extras; omit payload when payloads are disabled
        extras_keys = (
            "method",
            "endpoint",
            "status",
            "duration",
            "duration_ms",
            "event",
            "payload",
            "env",
            "session_id",
            "url",
            "test_name",
        )
        for key in extras_keys:
            if key == "payload" and not is_include_payloads():
                continue
            if hasattr(record, key):
                val = getattr(record, key)
                try:
                    obj[key] = self._redact_for_json(val)
                except (TypeError, ValueError, AttributeError):
                    # fallback to safe stringification; narrow catches only
                    try:
                        obj[key] = str(val)
                    except (TypeError, ValueError, AttributeError, UnicodeEncodeError):
                        obj[key] = "<unserializable>"

        # Include exception info if present (narrow exceptions only)
        if record.exc_info:
            try:
                obj["exc_info"] = self.formatException(record.exc_info)
            except (TypeError, ValueError, AttributeError) as e:
                # Formatting failed in an expected way — include a placeholder and a short debug note.
                obj["exc_info"] = "<exc_format_error>"
                log.debug("JSONFormatter: failed formatting exc_info: %s", e)

        # Serialize to JSON (preserve Unicode)
        return json.dumps(obj, indent=2, ensure_ascii=False) if self.pretty else json.dumps(obj, ensure_ascii=False)


# ==============================================================================================
# Structured logging: per-team JSONL routing
# ==============================================================================================
class TeamRoutingJSONLHandler(logging.Handler):
    """
    Structured JSONL logging handler that routes log records into per-team files.

    Design:
      - Team is derived dynamically from record.nodeid
      - One JSONL file per team per pytest run
      - No hardcoded teams
      - Parallel-safe (file-per-team)

    File layout:
      reports/
        <team>/
          logs/
            test/
              test_debug_structured_<timestamp>.jsonl

    Notes:
      - Streams are opened lazily to avoid creating empty files when structured logging is disabled.
      - LAST_STRUCTURED_LOG is set lazily when the first stream for a team is created.
      - Handler.close() closes all open streams so long-running processes don't leak file handles.
    """

    def __init__(self, base_dir: Path, formatter: logging.Formatter):
        super().__init__()
        self.base_dir = base_dir
        self.formatter = formatter
        self._streams: Dict[str, TextIO] = {}
        self._timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        self._keep = int(os.getenv("KEEP_STRUCTURED_LOGS", "3"))

    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a record to the per-team JSONL file.

        Error handling:
          - Expected errors (I/O and formatting) are handled explicitly so structured logging
            never breaks test execution.
          - Unexpected exceptions are caught at the end, logged to module logger and handled via
            Handler.handleError to preserve the library contract (do not raise from emit).
        """
        team = None
        try:
            nodeid = getattr(record, "nodeid", None)
            if not nodeid:
                return

            team = extract_team_from_nodeid(nodeid)
            if not team:
                return

            stream = self._get_stream(team)
            stream.write(self.format(record) + "\n")
            stream.flush()
        except (OSError, IOError) as e:
            # I/O errors are the most commonly expected failure (disk full, permission, transient NFS).
            # Do not raise; log and let logging's handleError produce diagnostics.
            log.debug("Structured JSONL I/O error for team '%s': %s", team, e, exc_info=True)
            self.handleError(record)
        except (TypeError, ValueError) as e:
            # Formatting/serialization errors while producing the line — handle gracefully.
            log.debug("Structured JSONL formatting error for team '%s': %s", team, e, exc_info=True)
            self.handleError(record)
        except Exception as e:
            # Last-resort catch: we still must not interrupt test execution, but surface details to the module logger.
            log.exception("Unexpected error in TeamRoutingJSONLHandler.emit (team=%s): %s", team, e)
            self.handleError(record)

    def _get_stream(self, team: str) -> TextIO:
        """
        Lazily create and cache one file stream per team.

        File layout:
          reports/
            logs/
              <team>/
                logs/
                  <ENV>/  # dynamic environment (test/dev/staging/prod)
                    test_debug_structured_<timestamp>.jsonl

        When a stream is first created we also populate LAST_STRUCTURED_LOG with the path
        of the created file (useful for CI or test harness that wants to know the file location).

        Enforces KEEP_STRUCTURED_LOGS per team + environment.
        """
        global LAST_STRUCTURED_LOG

        if team not in self._streams:
            logs_dir = (
                    self.base_dir
                    # / "logs"
                    / team
                    # / "logs"
                    / ENV  # ✅ dynamic environment folder
            )

            # Ensure directory exists
            logs_dir.mkdir(parents=True, exist_ok=True)

            # ------------------------------------------------------------------
            # Retention: prune older structured logs (per team + per ENV)
            # ------------------------------------------------------------------
            keep = int(os.getenv("KEEP_STRUCTURED_LOGS", "3"))
            try:
                existing = sorted(
                    logs_dir.glob("test_debug_structured_*.jsonl"),
                    key=lambda p: p.stat().st_mtime,
                    reverse=True,
                )
                for old in existing[keep:]:
                    try:
                        old.unlink()
                    except (OSError, PermissionError) as e:
                        log.debug(
                            "Failed to remove old structured log %s: %s",
                            old, e, exc_info=True
                        )
            except OSError as e:
                log.debug(
                    "Could not prune structured logs in %s: %s",
                    logs_dir, e, exc_info=True
                )
            # ------------------------------------------------------------------

            path = logs_dir / f"test_debug_structured_{self._timestamp}.jsonl"

            try:
                self._streams[team] = path.open("a", encoding="utf-8")
                # Expose the first-created structured log path for tooling/CI consumers.
                LAST_STRUCTURED_LOG = str(path.resolve())
            except (OSError, IOError) as e:
                log.debug(
                    "Failed to open structured log file %s: %s",
                    path, e, exc_info=True
                )
                raise

        return self._streams[team]

    def close(self) -> None:
        """
        Close all open streams and clear the cache. This prevents leaking file handles in long-lived processes.
        """
        for name, stream in list(self._streams.items()):
            try:
                stream.close()
            except Exception as e:
                # Closing should not interrupt shutdown; just log debug info.
                log.debug("Error closing stream for %s: %s", name, e, exc_info=True)
        self._streams.clear()
        super().close()


# ======================================================================================
# Helper: resolve the project root (try common repo markers, fallback to parents)
# ======================================================================================
def _resolve_project_root() -> Path:
    """
    Attempt to locate the repository/project root by searching upward for repo markers:
    - .git
    - pyproject_root.toml
    - setup.cfg
    - README.md

    If none found, fall back to a reasonably high parent (parents[3]) or Path.cwd().
    This prevents basing paths under the EcommerceAPI package directory.
    """
    p = Path(__file__).resolve()
    for parent in p.parents:
        if ((parent / ".git").exists() or (parent / "pyproject_root.toml").exists() or (parent / "setup.cfg").exists() or
                (parent / "README.md").exists()):
            return parent
    # fallback: try to move up 3 levels (typical layout: <repo>/EcommerceAPI/src/utilities/...)
    try:
        return p.parents[3]
    except IndexError:
        return Path.cwd()


# ==============================================================================================
#  Main logging setup
# ==============================================================================================
def configure_logging() -> logging.Logger:
    """
    Configure structured JSON logging and console formatting.

    Behavior:
    - Structured JSONL logging is enabled only when ENABLE_STRUCTURED_LOGS is truthy.
    - Structured logs are routed PER-TEAM by TeamRoutingJSONLHandler.
    - This function NEVER creates env- or team-specific directories.
      Directory layout is owned exclusively by the handler.
    - Function is idempotent and pytest-reuse safe.
    - Console logging remains unchanged and human-readable.

    Note: per-team JSON files are created lazily when the handler first writes for a team.
    LAST_STRUCTURED_LOG is set at that time.
    """
    global LAST_STRUCTURED_LOG

    # ------------------------------------------------------------------
    # Re-apply env-driven toggles to runtime flags
    # ------------------------------------------------------------------
    re_redact = os.getenv("REDACT_SENSITIVE_FIELDS")
    if re_redact is not None:
        set_redaction(re_redact.lower() in ("1", "true", "yes", "on"))

    re_payloads = os.getenv("LOG_PAYLOADS")
    if re_payloads is not None:
        set_include_payloads(re_payloads.lower() in ("1", "true", "yes", "on"))

    # ------------------------------------------------------------------
    # Detect CI environment
    # ------------------------------------------------------------------
    is_ci = bool(
        os.getenv("GITHUB_ACTIONS")
        or os.getenv("GITLAB_CI")
        or os.getenv("JENKINS_HOME")
    )

    # ------------------------------------------------------------------
    # Feature flags
    # ------------------------------------------------------------------
    disable_emojis_env = os.getenv("DISABLE_LOG_EMOJIS", "").lower() in ("1", "true", "yes", "on")
    enable_structured = os.getenv("ENABLE_STRUCTURED_LOGS", "").lower() in ("1", "true", "yes", "on")
    enable_pretty = os.getenv("ENABLE_JSON_PRETTY", "").lower() in ("1", "true", "yes", "on")

    use_emojis = (not is_ci) and (not disable_emojis_env)

    # ------------------------------------------------------------------
    # Prepare formatters
    # ------------------------------------------------------------------
    human_formatter = CustomFormatter(
        LOG_FORMAT,
        datefmt=LOG_DATEFMT,
        use_emojis=use_emojis,
    )
    json_formatter = JSONFormatter(pretty=enable_pretty)

    # ------------------------------------------------------------------
    # Root logger
    # ------------------------------------------------------------------
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # ==================================================================
    # Structured JSONL logging (PER-TEAM routing only)
    # ==================================================================
    if enable_structured:
        # Base directory MUST be the reports root.
        # The handler is solely responsible for subdirectories.
        override = os.getenv("LOG_DIR")
        if override and override.strip():
            base_dir = Path(override).resolve()
        else:
            project_root = _resolve_project_root()
            base_dir = project_root / "reports"

        handler_name = "EcommerceAPI_structured_team_jsonl"

        # Remove any stale handler (pytest process reuse safe)
        root.handlers = [
            h for h in root.handlers
            if getattr(h, "name", None) != handler_name
        ]

        handler = TeamRoutingJSONLHandler(
            base_dir=base_dir,
            formatter=json_formatter,
        )
        handler.setLevel(logging.DEBUG)
        handler.name = handler_name
        root.addHandler(handler)

        # Backward-compat placeholder (intentionally unset here)
        # Actual files are created lazily by the handler per team.
        LAST_STRUCTURED_LOG = None
    else:
        LAST_STRUCTURED_LOG = None

    # ==================================================================
    # Console logging (only outside pytest; pytest handles live logging)
    # ==================================================================
    if "pytest" not in sys.modules:
        if not any(
            isinstance(h, logging.StreamHandler)
            and getattr(h, "name", None) == "human_console"
            for h in root.handlers
        ):
            console = logging.StreamHandler(sys.stdout)
            console.setFormatter(human_formatter)
            console.setLevel(logging.INFO)
            console.name = "human_console"
            root.addHandler(console)

    # Capture stdlib warnings via logging
    logging.captureWarnings(True)

    return root
