# Pytest Plugins Architecture (EcommerceAPI Test Framework)

This document describes the **pytest plugin-based architecture** used in the EcommerceAPI test framework.

It replaces the former large `conftest.py` with **modular, well-scoped plugins** while preserving identical runtime behavior.
Each plugin focuses on a single responsibility and is loaded explicitly via `pytest_plugins`.

> This README is intentionally **global**.  
> Individual plugins contain detailed docstrings and inline comments; duplicating that documentation here would add noise.

---

## Table of Contents

1. Overview
2. Why Plugins Instead of One Large conftest
3. Plugin Loading Model
4. Plugin Responsibilities
   - `_config.py`
   - `logging.py`
   - `reporting.py`
   - `allure_autogen.py`
   - `entities.py`
   - `api_fixtures.py`
   - `db_fixtures.py`
5. Fixture & Hook Visibility Rules
6. Multi‑Microservice Base URL Strategy
7. Ordering Guarantees
8. Maintenance Guidelines
9. Common Pitfalls & Troubleshooting

---

## 1. Overview

The EcommerceAPI test framework uses **pytest plugins** to modularize what was previously a very large `conftest.py`.

Each plugin:
- Is imported once by pytest
- Registers fixtures, hooks, and configuration
- Has **no implicit dependency on directory structure**
- Can be reused across multiple test suites or microservices

All plugins live under:

```
EcommerceAPI/plugins/
```

They are loaded by a **top-level conftest** using `pytest_plugins`.

---

## 2. Why Plugins Instead of One Large conftest

The original `conftest.py` handled:

- Environment loading
- Logging configuration
- Pytest hooks
- Entity discovery
- API clients
- Database utilities
- Resource cleanup
- Reporting

This made the file:
- Hard to navigate
- Easy to break accidentally
- Difficult to reason about ordering

Splitting into plugins provides:

✔ Clear separation of concerns  
✔ Explicit load order  
✔ Easier testing and debugging  
✔ Safer long‑term maintenance  

No runtime behavior was intentionally changed.

---

## 3. Plugin Loading Model

Plugins are loaded via the root `conftest.py`:

```python
pytest_plugins = [
    "EcommerceAPI.plugins.logging",        # MUST load first
    "EcommerceAPI.plugins._config",
    "EcommerceAPI.plugins.reporting",
    "EcommerceAPI.plugins.allure_autogen", # session-level Allure lifecycle
    "EcommerceAPI.plugins.entities",
    "EcommerceAPI.plugins.db_fixtures",
    "EcommerceAPI.plugins.api_fixtures",
]
```

Key points:

- **Order matters**
- Logging must load first (record factory + redaction)
- `_config` defines shared constants and CLI flags
- `reporting` enriches test-level results and attachments
- `allure_autogen` manages Allure results dir lifecycle and optional HTML generation
- Other plugins assume these are already available

Pytest guarantees each plugin is imported exactly once.

---

## 4. Plugin Responsibilities

### `_config.py` — Centralized Configuration

Purpose:
- Central home for **CLI options**
- Environment‑driven defaults
- Constants used by plugins at import time

Examples:
- `--fail-on-empty-list`
- `KEEP_STRUCTURED_LOGS`
- `KEEP_HTML_REPORTS`
- `LOG_DIR`
- `AUTO_ALLURE_REPORT` (env toggle used by the Allure plugin)

Why it exists:
- Plugins execute before fixtures
- These values must be available early
- Avoids hidden coupling via environment lookups

---

### `logging.py` — Logging & Context Injection

Purpose:
- Load `.env`
- Configure logging
- Install LogRecord factory
- Inject `nodeid` and `correlation_id`
- Enforce redaction and payload rules
- Silence noisy third‑party loggers

Key features:
- ContextVars‑based per‑test correlation
- Optional structured JSONL logs
- Early redaction (before any log record is emitted)
- Emoji‑aware console formatting
- Safe handler deduplication and temporary startup handler to ensure consistent startup formatting
- Attaches GLOBAL_METADATA (git / CI / session) for structured logs

Notes on change:
- The plugin performs early message redaction in the LogRecord factory to prevent sensitive data from reaching handlers.
- It also ensures structured logging toggles (env/CLI) are applied before handlers are created so downstream handlers observe consistent settings.

This plugin **must load first**.

---

### `reporting.py` — Reporting & Failure Debugging

Purpose:
- Test-level hooks to enrich reports
- Add Allure labels (team / env / service)
- Attach structured JSONL logs to Allure on FAILED tests only
- Keep reporting lightweight and failure-focused

Key features:
- Adds Allure labels (best-effort) using `allure.dynamic.*` so the UI can filter by team/service/env
- On test failure, attaches the most-recent structured JSONL log file (if present) as an Allure attachment
- Never breaks pytest runs when Allure or logging pieces are missing

Notes on change:
- The plugin now targets Allure for attachments instead of pytest-html. It runs in the test lifecycle phase where attachments are valid (call phase).
- It intentionally restricts attachments to failed tests to keep reports small and focused.

---

### `allure_autogen.py` — Allure results lifecycle & optional HTML generation

Purpose:
- Manage Allure results directory lifecycle
  - Ensure results directory exists at session start
  - Clean previous run artifacts while preserving directory
- Optionally auto-generate Allure HTML report at session end when enabled
  - Controlled by `AUTO_ALLURE_REPORT` env var (truthy values: `"1"`, `"true"`, `"yes"`)
- Resolve `--alluredir` option, `ALLURE_RESULTS_DIR` env, and a sensible default (`./reports/allure-results`)

Key features and safety:
- Best‑effort behavior: never abort pytest startup or teardown because of Allure problems
- Resolves the `allure` CLI via `shutil.which` before attempting generation and logs helpful errors
- Generates per-service reports when CI/CI-matrix writes results into `reports/<service>/allure-results`
- Works well with both matrix CI (per-service folders) and single-run CI (one results folder)

Usage note:
- CI jobs are recommended to install Allure CLI at job runtime (job-level install) and set `AUTO_ALLURE_REPORT=true`.
- The plugin will skip HTML generation when results are missing or Allure CLI is not available.

---

### `entities.py` — Entity Discovery & Resource Tracking

Purpose:
- Discover API helpers and DAOs dynamically
- Bundle helpers, DAOs, and delete methods
- Track created resources
- Perform conditional teardown

Key concepts:
- `EntityBundle`
- `EntitiesRegistry`
- Convention‑based discovery
- Best‑effort cleanup (never crashes test runs)

Fixtures:
- `shared_api_resources`
- `shared_api_resources_obj`
- `all_resources`

This plugin contains **no test logic** — only orchestration.

---

### `api_fixtures.py` — API‑Level Test Fixtures

Purpose:
- Expose high‑level test fixtures built on entities
- Provide happy‑path and raw API access

Examples:
- `request_utility`
- `create_valid_customer`
- `raw_customer_api`

Design principles:
- Fail fast on misconfiguration
- Do not hide real API failures
- Assume infrastructure is wired correctly

---

### `db_fixtures.py` — Database Utilities

Purpose:
- Provide database access for validation
- Keep DB logic isolated from API logic

Fixtures:
- `db` (session‑scoped DBUtility)

The DB layer is optional — tests that don’t need it don’t pay for it.

---

## 5. Fixture & Hook Visibility Rules

Important pytest rules that apply to this architecture:

- Fixtures are resolved **by name**
- Plugins do **not** define directory scope
- Directory‑level `conftest.py` files override or supplement plugins

Example:

```python
def request_utility(api_base_url):
    ...
```

➡ pytest **must** find `api_base_url` in the test’s collection tree.

---

## 6. Multi‑Microservice Base URL Strategy

Each microservice owns its own base URL.

Pattern:

```
tests/api/customers/conftest.py
tests/api/orders/conftest.py
tests/shared/preflight/conftest.py
```

Each defines:

```python
@pytest.fixture(scope="session")
def api_base_url() -> str:
    ...
```

Why this works:
- Framework remains service‑agnostic
- Tests are explicit about which service they hit
- No hidden global URLs
- Safe to run mixed services in one session

This is **intentional and correct**.

---

## 7. Ordering Guarantees

The framework relies on strict ordering:

1. `.env` loading
2. Logging toggles (redaction, payloads)
3. LogRecord factory installation
4. Logging configuration
5. Plugin fixtures
6. Test execution
7. Conditional teardown (Allure HTML generation runs during session finish)

Breaking this order can cause:
- Leaked secrets
- Missing correlation IDs
- Duplicate handlers
- Inconsistent logs

Do not change plugin order casually.

---

## 8. Maintenance Guidelines

- Never refactor behavior while splitting plugins
- Keep plugins small and single‑purpose
- Prefer failing fast over swallowing errors
- Avoid adding implicit imports between plugins
- Document *why*, not *what*, in docstrings
- Keep CLI flags in `_config.py`
- Keep discovery logic isolated in `entities.py`
- Keep Allure generation optional and non-fatal — rely on `AUTO_ALLURE_REPORT` and job-level Allure installs

---

## 9. Common Pitfalls & Troubleshooting

**Fixture not found**
- Check directory‑level conftest visibility
- Ensure the fixture name matches exactly

**Duplicate logs**
- Ensure logging plugin loads first
- Do not add StreamHandlers in tests

**Cleanup not running**
- Resource was never registered
- Delete method missing for entity

**Structured logs missing**
- ENABLE_STRUCTURED_LOGS not set
- CLI flag not passed
- LOG_DIR not writable

**No Allure HTML report generated**
- Ensure `AUTO_ALLURE_REPORT` is set (`"true"`, `"1"`, or `"yes"`)
- CI jobs should install the Allure CLI at runtime (recommended)
- Confirm `--alluredir` or `ALLURE_RESULTS_DIR` points to the folder with results
- The plugin will skip generation without failing the run if Allure binary is missing or results are empty

---

## Final Note

This plugin architecture is intentionally conservative.

It favors:
- Explicit wiring
- Predictable failure modes
- Debuggability over cleverness

If something breaks, it should break **loudly and early**.

That is by design.