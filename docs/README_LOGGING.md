# Logging Guide — EcommerceAPI

This document explains the logging configuration used by the test suite, how to control verbosity and structure, and recommended settings for local development and CI. See EcommerceAPItest/src/utilities/custom_logger.py for the authoritative implementation.

Overview
--------
The framework exposes two complementary logging surfaces:

- Console (human)
  - Pytest's live-logging is the single console emitter during test runs.
  - Console formatting is readable and includes test context (nodeid, correlation_id) and optional emojis.
  - Messages are redacted (when enabled) before any handler sees them.

- Structured JSONL file output (optional, CI-friendly)
  - Opt-in: enabled by setting `ENABLE_STRUCTURED_LOGS=true`.
  - Produces one JSON object per line with rich metadata (timestamp, level, logger, message, nodeid, correlation_id, session/git/CI info, extras like method/endpoint/status/duration/payload/url).
  - Files are timestamped and pruned locally according to `KEEP_STRUCTURED_LOGS`.
  - Redaction is applied to structured output as well.
  - There are no human rotating “.log” files produced by the framework — structured JSONL is the only on-disk log artifact the logger may write.

Design goals
------------
- Keep console output concise and useful for developers (pytest live-logging).
- Provide machine-readable artifacts for CI when explicitly requested.
- Avoid leaking secrets by applying redaction early (record factory) and in formatters.
- Avoid duplicate console output by relying on pytest live-logging rather than adding extra StreamHandlers during test runs.

Key environment variables
-------------------------
Set these in CI or a local `.env` file as needed.

Core toggles
- ENABLE_STRUCTURED_LOGS=false  
  - When `true` the framework writes a structured JSONL file for the run (opt-in).
- ENABLE_JSON_PRETTY=false  
  - When `true` pretty-prints structured JSON (larger files).
- LOG_DIR (optional)  
  - Base directory for structured files when enabled (defaults to `EcommerceAPItest/tests/api/logs`).
- KEEP_STRUCTURED_LOGS=3  
  - Number of structured JSONL files to keep (pruning applies only when structured logging is enabled).

Security / payloads
- REDACT_SENSITIVE_FIELDS=true  
  - Automatic redaction of known sensitive keys (default: enabled). Keep enabled in CI.
- LOG_PAYLOADS=false  
  - Controls whether request/response payloads are included in structured logs (masked when redaction enabled). Use with caution in CI.

Runtime API (programmatic toggles)
----------------------------------
- set_redaction(bool) / is_redaction_enabled()  
  - Toggle or query redaction at runtime.
- set_include_payloads(bool) / is_include_payloads()  
  - Toggle whether payloads are included in structured output.

Important behavior notes
------------------------
- Early redaction: conftest installs a LogRecord factory that calls the redactor on the fully rendered message before any handler sees it. This prevents transient exposures from format-time rendering.
- Structured JSONL is created only when `ENABLE_STRUCTURED_LOGS` is truthy.
- The JSON formatter attempts safe redaction and serialization; un-serializable extras fall back to string representations or a `<unserializable>` marker.
- Console handlers are not added by the logging initializer when pytest is present; pytest provides live logging. The module will only add a console StreamHandler outside pytest contexts.

Where structured logs are written
-------------------------------
- `{LOG_DIR or default}/<ENV>/test_debug_structured_<TIMESTAMP>.jsonl`  
  - Default base: `EcommerceAPItest/tests/api/logs/<ENV>/`
  - Files are timestamped and pruned by modification time; pruning keeps the newest `KEEP_STRUCTURED_LOGS`.

How to run locally
------------------
- Normal test run (recommended):
  - `pytest -q`  (pytest live-logging is the human surface)
- Extra console verbosity:
  - `pytest -q -o log_cli=true -o log_cli_level=DEBUG`
- Enable structured JSONL (example):
  - `ENABLE_STRUCTURED_LOGS=true pytest -q`
  - Inspect the produced JSONL at `LOG_DIR` for artifact export.

Troubleshooting
---------------
- No structured files despite `ENABLE_STRUCTURED_LOGS=true`:
  - Confirm `LOG_DIR` (or default) is writable by the process.
  - Check CI job env: your runner may override envs or mount different workspaces.
- Sensitive data appears in logs:
  - Ensure `REDACT_SENSITIVE_FIELDS=true` in the environment before pytest starts (conftest applies this early).
  - If you need deeper debugging and temporarily set redaction off, be careful to avoid uploading artifacts containing secrets.
- Duplicate console lines:
  - Ensure no extra StreamHandler is added elsewhere in tests or helpers. The framework avoids adding a console handler while pytest is active.

Quick handler-inspection helper
-------------------------------
Add a small debug test to list active handlers:

```python
def test_dump_handlers():
    import logging, pprint
    pprint.pprint(
        [(type(h).__name__, getattr(h, "name", None), getattr(h, "stream", None), h.level)
         for h in logging.getLogger().handlers]
    )
```

Best practices
--------------
- Keep `REDACT_SENSITIVE_FIELDS=true` in CI.
- Only enable `LOG_PAYLOADS=true` for targeted debugging runs and prefer to enable it for failed-run artifact collection only.
- Use `ENABLE_STRUCTURED_LOGS=true` in CI to retain machine-readable artifacts and upload them as build artifacts for post-mortem analysis.

Reference
---------
See `EcommerceAPItest/src/utilities/custom_logger.py` for the implementation details and the exact list of redacted keys and JSON extras.