# 🧾 Logging Guide — EcommerceAPI

This document explains the logging configuration used by the test suite, how to control verbosity and structure, and
recommended settings for local development and CI.

See `EcommerceAPItest/src/utilities/custom_logger.py` for the authoritative implementation.

---

🔎 Overview
--------
The framework exposes two complementary logging surfaces:

- **Console** (human)
  - Pytest's live-logging is the single console emitter during test runs.
  - Console formatting is readable and includes test context (nodeid, correlation_id) and optional emojis.
  - Messages are redacted (when enabled) before any handler sees them.

- **Structured JSONL file output** (optional, CI-friendly)
  - Opt-in: enabled by setting `ENABLE_STRUCTURED_LOGS=true`.
  - Produces one JSON object per line with rich metadata (timestamp, level, logger, message, nodeid, correlation_id, session/git/CI info, extras like method/endpoint/status/duration/payload/url).
  - Files are timestamped and pruned locally according to `KEEP_STRUCTURED_LOGS`.
  - Redaction is applied to structured output as well.
  - There are no human rotating “.log” files produced by the framework — structured JSONL is the only on-disk log artifact the logger may write.

---

## 🏗️ Logging Architecture

The logging system is intentionally split into two layers.

### `plugins/logging_plugin.py`

Responsible for integrating logging with the pytest lifecycle.

Responsibilities include:

- loading `.env`
- configuring runtime logging options
- installing the custom `LogRecord` factory
- attaching ContextVar metadata (nodeid, correlation_id, environment)
- configuring pytest console logging
- collecting Git / CI / session metadata
- emitting session lifecycle events
- restoring logging state after the test session

🔴 This module **does not implement logging**.

🟢 It orchestrates logging for a pytest execution.

---

### `src/utils/custom_logger.py`

Responsible for the logging implementation itself.

Responsibilities include:

- console formatting
- JSON formatter
- structured JSONL logging
- payload redaction
- emoji handling
- log routing
- structured log retention
- logging handlers
- runtime logging configuration

This module is framework-agnostic and can be reused outside pytest.

---

🎯 Design goals
------------
- Keep console output concise and useful for developers (pytest live-logging).
- Provide machine-readable artifacts for CI when explicitly requested.
- Avoid leaking secrets by applying redaction early (record factory) and in formatters.
- Avoid duplicate console output by relying on pytest live-logging rather than adding extra StreamHandlers during test runs.

---

## 🏛️ Logging Philosophy

The framework intentionally separates logging into two audiences:

### 1. Human logs (console)

The console is optimized for developers reading test output.

Human logs should answer:

- What test is running?
- What business action is happening?
- Did it succeed?
- If it failed, why?

Console output should remain concise and avoid implementation details that do not help diagnose a failing test.

Typical examples include:

- Session startup
- Framework configuration summary
- HTTP request summaries
- Business validation results
- Cleanup summary
- Final test outcome

---

### 2. Machine logs (structured JSONL)

Structured logs exist for automation rather than people.

When `ENABLE_STRUCTURED_LOGS=true`, the framework records detailed execution metadata, including request payloads (when enabled), timing information, CI metadata, Git metadata, and runtime context.

These logs are intended for:

- CI artifact analysis
- Post-mortem debugging
- Automated log processing
- Long-term observability

---

### Design Principle

The console should tell the story.

The structured logs should tell everything.


---

### Console Log Categories

| Category | Purpose                                              | Console |
|----------|------------------------------------------------------|:-------:|
| Framework | Session startup, configuration, environment          | ✅ |
| Business | Creating customers/products..., validations, cleanup | ✅ |
| Transport | HTTP request summaries and response timings          | ✅ |
| Diagnostics | Payloads, retries, helper internals                  | ⚙️ Structured logs / Debug Mode |

```
pytest
   │
   ▼
logging_plugin.py
   │
   ├── installs LogRecord factory
   ├── loads .env
   ├── attaches ContextVars
   ├── configures logging
   │
   ▼
custom_logger.py
   │
   ├── Console formatter
   ├── JSON formatter
   ├── Structured handler
   ├── Redaction
   ├── Routing
   │
   ▼
Console        JSONL
```


---

## 🔊 Logging Modes

The framework is designed around three logging modes.

### 1. Developer Mode (default)

Console output is concise and focused on the business workflow.

Typical output includes:

- session startup
- framework configuration
- API request summaries
- business validations
- cleanup summary

---

### 2. Debug Mode

Used while developing the framework.

In addition to Developer Mode it may include:

- helper decisions
- validator internals
- retry information
- payload previews
- troubleshooting diagnostics

---

### 3. CI Mode

Uses the same readable console output as Developer Mode while additionally producing structured JSONL logs.

This mode is intended for:

- build artifacts
- post-mortem debugging
- machine-readable diagnostics


---

⚙️ Key environment variables
-------------------------
Set these in CI or a local `.env` file as needed.

### Core toggles
- `ENABLE_STRUCTURED_LOGS=false`
  - When `true` the framework writes a structured JSONL file for the run (opt-in).
- `ENABLE_JSON_PRETTY=false`
  - When `true` pretty-prints structured JSON (larger files).
- `LOG_DIR `(optional)
  - Base directory for structured files when enabled (defaults to `EcommerceAPItest/tests/api/logs`).
- `KEEP_STRUCTURED_LOGS=3`
  - Number of structured JSONL files to keep (pruning applies only when structured logging is enabled).

### Security / payloads
- `REDACT_SENSITIVE_FIELDS=true`
  - Automatic redaction of known sensitive keys (default: enabled). Keep enabled in CI.
- `LOG_PAYLOADS=false`
  - Controls whether request/response payloads are included in structured logs (masked when redaction enabled). Use with caution in CI.

---

⏳ Runtime API (programmatic toggles)
----------------------------------
- `set_redaction(bool) `/ `is_redaction_enabled()`
  - Toggle or query redaction at runtime.
- `set_include_payloads (bool)` / `is_include_payloads()`
  - Toggle whether payloads are included in structured output.

---

⚠️ Important behavior notes
------------------------
- Early redaction: conftest installs a `LogRecord` factory that calls the redactor on the fully rendered message before any handler sees it. This prevents transient exposures from format-time rendering.
- Structured JSONL is created only when `ENABLE_STRUCTURED_LOGS` is truthy.
- The JSON formatter attempts safe redaction and serialization; un-serializable extras fall back to string representations or a `<unserializable>` marker.
- Console handlers are not added by the logging initializer when pytest is present; pytest provides live logging. The module will only add a console StreamHandler outside pytest contexts.

---

📌 Where structured logs are written
-------------------------------
- `{LOG_DIR or default}/<ENV>/test_debug_structured_<TIMESTAMP>.jsonl`
  - Default base: `EcommerceAPItest/reports/logs/<entity>/`
  - Files are timestamped and pruned by modification time; pruning keeps the newest `KEEP_STRUCTURED_LOGS`.

---

🤔 How to run locally
------------------
- Normal test run (recommended):
  - `pytest -q`  (pytest live-logging is the human surface)
- Extra console verbosity:
  - `pytest -q -o log_cli=true -o log_cli_level=DEBUG`
- Enable structured JSONL (example):
  - `ENABLE_STRUCTURED_LOGS=true pytest -q`
  - Inspect the produced JSONL at `LOG_DIR` for artifact export.

---

🛠️ Troubleshooting
---------------
- No structured files despite `ENABLE_STRUCTURED_LOGS=true`:
  - Confirm `LOG_DIR` (or default) is writable by the process.
  - Check CI job env: your runner may override envs or mount different workspaces.
- Sensitive data appears in logs:
  - Ensure `REDACT_SENSITIVE_FIELDS=true` in the environment before pytest starts (conftest applies this early).
  - If you need deeper debugging and temporarily set redaction off, be careful to avoid uploading artifacts containing secrets.
- Duplicate console lines:
  - Ensure no extra StreamHandler is added elsewhere in tests or helpers. The framework avoids adding a console handler while pytest is active.
---

🕵 Quick handler-inspection helper
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
---

🎯 Best practices
--------------
- Keep `REDACT_SENSITIVE_FIELDS=true` in CI.
- Only enable `LOG_PAYLOADS=true` for targeted debugging runs and prefer to enable it for failed-run artifact collection only.
- Use `ENABLE_STRUCTURED_LOGS=true` in CI to retain machine-readable artifacts and upload them as build artifacts for post-mortem analysis.

---

📚 Reference
---------
See `EcommerceAPItest/src/utilities/custom_logger.py` for the implementation details and the exact list of redacted keys and JSON extras.
