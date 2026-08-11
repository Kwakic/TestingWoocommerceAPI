# TestEcommerceAPI Architecture – Unified API Automation Suite

A unified, multi-team API automation platform for testing Customers, Orders, Coupons, Products, and other microservices in the Ecommerce ecosystem.

This README reflects the current repository layout and recent changes:
- Reporting moved to Allure (pytest writes Allure results; CI generates HTML).
- Plugins are modular and live under the shared framework package.
- CI uses segmented workflows (preflight, smoke, regression, etc.)
  combined with matrix execution (one job per microservice where applicable).
- Runtime Docker images are kept small and do not include Allure by default.

---

## 🗃️ Repository layout (important parts)

Top-level (trimmed):

```
.
├── EcommerceAPI/              # installable framework
│   └── plugins/
│       ├── config_pytest.py
│       ├── logging_plugin.py
│       ├── entity_metadata.py
│       ├── entities.py
│       ├── api/
│       │   ├── shared.py
│       │   ├── customers.py
│       │   ├── products.py
│       │   ├── orders.py
│       │   └── coupons.py
│
├── tests/                     # test suites (by entity)
├── docs/                      # framework + CI + guides
├── scripts/                   # setup + CI helpers
├── .github/workflows/         # CI pipelines
├── Makefile                   # orchestration
├── docker-compose.wp.yml
├── .env.example
├── .env                       # local only
├── pyproject.toml             # repo-level config
```

👉 For a full breakdown of the structure, responsibilities, and where to extend the framework:

📚 [Full Project Structure](./docs/project-structure/README_project_navigation.md)


---

# ⚙️ Execution Model (How tests actually run)

The framework is designed to be executed through a **controlled orchestration layer**, not by calling `pytest` directly.

👉 The canonical entrypoint is:

```bash
make run
```

## 🧩 What make run does

`make run` orchestrates the full lifecycle:

**1. 🐳 Spin up environment**
* Docker Compose starts WordPress + WooCommerce

**2. 🔑 Provision credentials**
* WooCommerce generates WC_KEY / WC_SECRET
* Credentials are injected into runtime environment

**3. ⚙️ Configure framework**
* Environment variables resolved
* API client configured dynamically

**4. 🧪 Execute tests**
* pytest runs with proper environment
* Allure results are generated

**5. 📦 Collect artifacts**
* Reports (Allure)
* Structured logs

**6. 🧹 Tear down (optional)**
* Containers stopped/cleaned

---

## ❗ Why NOT run pytest directly?

Running pytest manually bypasses:

* ❌ Environment provisioning
* ❌ Credential generation
* ❌ Proper configuration
* ❌ Docker isolation

---

### 🧠 Correct mental model

pytest is the execution engine, but it must run within a correctly
provisioned environment (Docker + credentials).

- Use `make run` for full orchestration
- Use `pytest` directly only when the environment is already prepared

This can lead to:

* authentication failures
* inconsistent environments
* misleading test results

---

## 🧠 Design Principle

👉 pytest is the execution engine,
👉 make run is the system orchestrator

```
make run
   ↓
Docker + setup
   ↓
pytest
   ↓
plugins
   ↓
fixtures (api/)
   ↓
helpers
   ↓
API / DB
```

---

## 🧠 Architecture Style

The framework follows a layered architecture:

- Orchestration layer (Makefile / Docker)
- Execution layer (pytest)
- Plugin layer (shared behavior)
- Fixture layer (entity-scoped setup)
- Helper layer (business logic)
- API/DB layer (system under test)


---

## 🧩 Shared framework package (EcommerceAPI)

- This folder is a pip-installable package: use `pip install -e './EcommerceAPI[dev]'` for local development.
- Only *shared* pytest plugins belong in `EcommerceAPI/plugins/`. They are global to all test suites.
- `EcommerceAPI/src/` contains universal utilities used by all microservices (logging, request helpers, env utils, etc.).

Key shared plugins:
- `logging_plugin.py` — logging setup, ContextVar injection, early redaction, structured JSONL output, and session metadata.
- `reporting.py` — Allure labels + attach structured JSONL logs on failed tests.
- `allure_autogen.py` — ensures results directory lifecycle and optionally generates Allure HTML at session finish if `AUTO_ALLURE_REPORT` is enabled.
- `api_fixtures.py`, `db_fixtures.py`, `entities.py`, `config_pytest.py` — other shared fixtures/config.

---

## How plugins are loaded

Top-level `conftest.py` uses:

```python
pytest_plugins = [
    "EcommerceAPI.plugins.logging_plugin",        # MUST load first
    "EcommerceAPI.plugins.config_pytest",
    "EcommerceAPI.plugins.reporting",
    "EcommerceAPI.plugins.allure_autogen", # manage Allure lifecycle
    "EcommerceAPI.plugins.entities",
    "EcommerceAPI.plugins.db_fixtures",
    "EcommerceAPI.plugins.api_fixtures",
    "EcommerceAPI.plugins.entity_metadata",
    # -----------------------
    # API Layer (split by domain) This layer provides entity-scoped pytest fixtures and acts as the bridge between pytest and the helper/API layers.
    # -----------------------
    "EcommerceAPI.plugins.api.shared_api",
    "EcommerceAPI.plugins.api.customers",
    "EcommerceAPI.plugins.api.products",
    "EcommerceAPI.plugins.api.orders",
    "EcommerceAPI.plugins.api.coupons",
]

```

Order matters: logging must load first so all log records are created with the custom factory and redaction rules.



### 🧩 API Fixture Layer (plugins/api/)

This layer provides **entity-scoped pytest fixtures** and is responsible for:

- Creating domain-specific test data (e.g. `create_valid_customer`)
- Providing helpers (`customers_helper`, `products_helper`)
- Abstracting API interactions from test code

It acts as the bridge between:

pytest → fixtures → helpers → API client

This design ensures:
- Tests remain clean and declarative
- Business logic stays in helpers
- API details are fully encapsulated



---

## 🧪 Running tests (advanced / internal)

⚠️ This is **not the recommended way** to run the framework.

👉 Use `make run` unless you explicitly need low-level control.

---

### 🔧 When to use this

Direct `pytest` execution is useful for:

- debugging a specific test
- developing locally with an already running environment
- CI internal steps (inside jobs)

---

### 🧪 Examples

Run full test suite:

```bash
pytest tests --alluredir=reports/allure-results
```

Run a single microservice:


```
pytest tests/customers --alluredir=reports/customers/allure-results
```

---

### ❗ Requirements

This assumes:

* environment is already running (Docker)
* credentials are already valid
* configuration is already resolved

Otherwise results will be unreliable.

---

# 🧠 Why this matters

Right now your doc says:

> “Here’s how to run tests”

But in reality:

> “Here’s how to bypass the system safely (if you know what you're doing)”

That’s a **big difference in architecture maturity**.

---

## Docker & docker-compose (matrix helper)

- The repository includes a Dockerfile for a test image. By design the runtime image does **not** include Allure CLI (keeps the image small).
- CI installs Allure at job runtime (recommended). Locally you can:
  - Generate HTML on the host after copying results from `./reports`.
  - Build a dev image that includes Allure if you need in-container HTML generation.

- `docker-compose.matrix.yml` is a helper to run per-service containers (profiles). Best practice:
  - Mount `./tests` and `./reports` to the container.
  - Set `AUTO_ALLURE_REPORT` in the container env if you want the container to attempt generation (only works if `allure` is available in the container).
  - Example: run only customers profile locally:
    ```bash
    docker compose -f docker-compose.matrix.yml --profile customers up --abort-on-container-exit --remove-orphans
    ```

---

### 🪟 Windows (Git Bash) Compatibility

When using **Git Bash** on Windows, Unix-style paths passed to Docker
Compose commands may be rewritten automatically by the shell.

For example:

```text
/var/www/html
```

may become:

```text
C:/Program Files/Git/var/www/html
```

This causes WP-CLI to fail with an error similar to:

```text
Error: This does not seem to be a WordPress installation.
```

To prevent this, the framework disables Git Bash path conversion by
setting:

```text
MSYS_NO_PATHCONV=1
```

before executing Docker Compose commands that invoke WP-CLI.

> **Note**
>
> This behavior is specific to Git Bash on Windows.
> Linux, macOS and GitHub Actions are not affected.


---

## 🛠️ CI/CD Architecture

The framework uses **segmented GitHub Actions workflows**, not a single monolithic pipeline.

Each workflow answers a specific question:

- preflight → can the framework run?
- smoke → are critical flows working?
- contract → did the schema change?
- integration → API ↔ DB consistency
- regression → full coverage
- performance → latency + SLA
- security → auth & permissions

This design provides:

- Faster feedback
- Clear failure ownership
- Independent execution
- Better reporting (Allure per suite)

---

## 🚀 CI Platform

The framework is designed for **GitHub Actions**.

Previous references to GitLab CI are legacy and no longer supported.

Key integrations:
- GitHub Actions (execution)
- GitHub Pages (Allure reports)
---

## 🌍 Environment & Configuration

The framework intentionally separates **environment selection** from
**authentication**.

### Local development

- `.env` is used for local convenience only.
- Never commit secrets to the repository.
- During `make run`, WooCommerce automatically generates a fresh pair of
  REST API credentials (`WC_KEY` / `WC_SECRET`), which are merged into
  the local `.env`.

### Continuous Integration

GitHub Actions does not use the repository `.env` file.

Instead, each workflow provisions a fresh WooCommerce environment,
generates new REST API credentials, and injects them directly into the
workflow environment.

### Runtime configuration

The framework resolves the active API endpoint dynamically using:

```text
API_ENV
    ↓
config_<entity>.py
    ↓
API_HOSTS
    ↓
APIClient
```

This means:

- `.env` stores authentication credentials only.
- `API_ENV` selects the active environment.
- Entity configuration files own endpoint mappings.
- The same configuration model is used for local development, Docker,
  and GitHub Actions.

For a complete explanation of the configuration architecture, see:

👉 `docs/framework/README_ENVIRONMENT_CONFIG_GUIDE.md`

This document is the canonical reference for environment selection,
endpoint resolution and runtime configuration.

---

# 🧩 Failure Handling & Data Integrity Layers

The framework enforces reliability and correctness through **three complementary layers**:

| Layer | Responsibility |
|------|----------------|
| 🚪 Env Gate (`api_client` fixture) | Validate environment once (fail fast before any test runs) |
| 🔁 APIClient | Retry transient issues (5xx, 429) |
| 📦 Pagination | Ensure **data integrity + fail-fast correctness** |

---

## 🚪 1. Environment Gate (Session-Level)

- Runs **once per pytest session**
- Calls `system_status`
- Aborts execution using `pytest.exit()` if:
  - credentials are missing
  - authentication fails (401)
  - API is unreachable

👉 Prevents:
- noisy test runs
- repeated failures
- infinite pagination loops caused by invalid environment

---

## 🔁 2. APIClient (Retry Layer)

Handles **transient failures only**:

- Retries:
  - `429` (rate limiting)
  - `5xx` (server errors)
  - connection issues

- Does **NOT**:
  - raise on 4xx
  - enforce business correctness

👉 Responsibility:
"Try again if it *might* succeed."

---

## 📦 3. Pagination (Data Integrity Layer)

Pagination is responsible for **correctness of aggregated data**, not transport.

### Key guarantees:

- 🚨 Fail-fast on deterministic errors (all 4xx except 429)
- 🛑 Abort pagination if a page fails after retries
- ❌ Never silently skip pages
- 📊 Never return partial datasets

### Why this exists:

The environment gate only validates **once at session start**.

Failures can still occur:
- mid-test
- per-endpoint (permissions)
- due to bad parameters

👉 Pagination enforces correctness **at the point of data aggregation**

---

## 🧠 Design Principle

Each layer handles a different failure moment:

| When | Who handles it |
|------|----------------|
| Before tests start | 🚪 Env Gate |
| During request (transient) | 🔁 APIClient |
| During data aggregation | 📦 Pagination |

This avoids:
- duplicated logic
- hidden failures
- inconsistent datasets

---

## Reports & logs layout

Examples (host `./reports/`):

```
reports/
├── customers/
│   ├── allure-results/      ← raw Allure jsons & attachments
│   └── allure-report/       ← generated HTML (index.html)
└── logs/
    └── customers/
        └── test/
            └── test_debug_structured_YYYYMMDD_HHMMSS.jsonl
```

- The logging plugin writes structured JSONL logs to `LOG_DIR` (default: `EcommerceAPI/tests/api/logs`).
- `reporting.py` will attach the latest structured JSONL file to failed tests in Allure (if present).

---

## Adding a new microservice (team)

1. Create `tests/<new_service>/` and follow the established layout:
   - `conftest.py`, `configs/`, `constants/`, `helpers/`, `api/`, `schemas/`, etc.
2. No change needed to shared plugins—discovery and CI will pick up the folder automatically.
3. For local Docker/matrix runs add the profile name if you want to run via `docker-compose` (optional).

---

## Troubleshooting checklist

- No Allure HTML:
  - Did pytest write to `--alluredir`? Is the results folder non-empty?
  - Is `AUTO_ALLURE_REPORT` truthy and is `allure` installed in the environment attempting generation?
- Structured logs missing:
  - Is `ENABLE_STRUCTURED_LOGS=true`? Is `LOG_DIR` writable?
- Duplicate or missing logging fields:
  - Ensure `EcommerceAPI.plugins.logging_plugin` loads first (conftest order) — it installs the LogRecord factory.

---

## Quick commands

- Install framework locally:
  ```bash
  pip install -e './EcommerceAPI[dev]'
  ```

- Run customers tests and write Allure results:
  ```bash
  pytest tests/customers --alluredir=reports/customers/allure-results
  ```

- Generate HTML from results (local/CI where Allure CLI is present):
  ```bash
  allure generate reports/customers/allure-results -o reports/customers/allure-report --clean
  ```

- Run a single-service container locally (docker-compose matrix):
  ```bash
  docker compose -f docker-compose.matrix.yml --profile customers up --abort-on-container-exit --remove-orphans
  ```

---
## 🔐 Golden Rules (NOT violate these)

1. Plugins must not import from tests/ at runtime
(TYPE_CHECKING hack is OK — you already do this correctly)
2. Fixtures own lifecycle & path (happy vs raw)
3. Helpers do NOT manage fixtures
4. Tests do NOT import helpers
5. Rollback must be trivial (git revert one file)

---
## Final note

The framework is designed for multi-team scale: independent microservice test folders, shared plugins for consistent behavior, and CI matrix support for fast, isolated feedback. Keeping Allure generation optional and CI-installed (rather than baked into images) yields smaller images and more reproducible CI runs.

If you want, I can:
- Add a small `scripts/` helper (e.g., `scripts/generate_allure.sh`) to standardize local HTML generation.
- Add a short `workflow_dispatch` input to GitHub Actions for `SERVICE` to make single-service runs easier from the Actions UI.
