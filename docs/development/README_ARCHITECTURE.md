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
│       │   ├── shared_api.py
│       │   ├── shared_graphql.py
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

For the API layer, REST and GraphQL use separate protocol clients while
sharing the same low-level HTTP transport:

```text
REST
  ↓
APIClient
  ↓
HttpClient

GraphQL
  ↓
GraphQLClient
  ↓
HttpClient
```

This keeps protocol-specific behavior separate without duplicating the HTTP
transport implementation.


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
    # -----------------------
    # Core Framework Plugins
    # -----------------------
    "EcommerceAPI.plugins.logging_plugin",  # MUST load first!!!
    "EcommerceAPI.plugins.config_pytest",
    "EcommerceAPI.plugins.reporting",
    "EcommerceAPI.plugins.allure_autogen",
    # -----------------------
    # Core Dependency Layer
    # -----------------------
    "EcommerceAPI.plugins.entities",  # <-- defines shared_api_resources
    "EcommerceAPI.plugins.db_fixtures",
    "EcommerceAPI.plugins.api_fixtures",  # <-- uses shared_api_resources
    # -----------------------
    # API Layer (split by domain)
    # -----------------------
    "EcommerceAPI.plugins.api.shared_api",
    "EcommerceAPI.plugins.api.shared_graphql",
    "EcommerceAPI.plugins.api.customers",
    "EcommerceAPI.plugins.api.products",
    "EcommerceAPI.plugins.api.orders",
    "EcommerceAPI.plugins.api.coupons",
]


```

Order matters: logging must load first so all log records are created with the custom factory and redaction rules.

---

### 🧩 API Plugin Layer — REST and GraphQL

The `EcommerceAPI/plugins/api/` directory contains shared pytest plugins for
the API-facing test infrastructure.

There are two shared protocol-level plugins:

```text
EcommerceAPI/plugins/api/
├── shared_api.py
└── shared_graphql.py
```

They have different responsibilities:

```text
shared_api.py
    ↓
Shared REST infrastructure

shared_graphql.py
    ↓
Shared GraphQL infrastructure
```

`shared_graphql.py` provides the shared GraphQL test infrastructure, including
the `graphql_client` fixture and the configuration/authentication wiring
needed by GraphQL tests.

It does **not** contain Product, Customer, Order, or Coupon GraphQL business
behavior.

Entity-specific plugins remain separate:

```text
EcommerceAPI/plugins/api/
├── shared_api.py       ← shared REST infrastructure
├── shared_graphql.py   ← shared GraphQL infrastructure
├── customers.py       ← Customer API fixtures/helpers
├── products.py         ← Product API fixtures/helpers
├── orders.py           ← Order API fixtures/helpers
└── coupons.py          ← Coupon API fixtures/helpers
```

Entity-specific GraphQL behavior remains in the corresponding test domain:

```text
tests/products/graphql/
tests/customers/graphql/
tests/orders/graphql/
tests/coupons/graphql/
```

Framework-level GraphQL contract tests remain under:

```text
tests/shared/contracts/graphql/
```

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

Run Product GraphQL tests directly when the environment is already prepared:

```bash
pytest tests/products/graphql/ -v
```

Run shared GraphQL contract tests:

```bash
pytest tests/shared/contracts/graphql/ -v
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

GraphQL follows the same segmented CI model. It is a test protocol, not a new
CI tier by itself.

GraphQL tests are selected by pytest markers and therefore run through the
existing CI suite workflows and reusable test runner:

```text
GraphQL test
    ↓
pytest markers
    ↓
existing CI suite
    ↓
reusable test runner
```

For example, framework-level GraphQL contract tests belong to the `contract`
suite, while entity-level GraphQL tests are classified according to the type
of behavior they verify.

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

### GraphQL configuration

GraphQL follows the same environment-aware approach, but uses its own
framework configuration because `/graphql` is a GraphQL endpoint rather than
an entity-specific REST endpoint.

```text
API_ENV
   ↓
config_graphql.py
   ↓
get_graphql_host()
   ↓
GraphQLClient
```

GraphQL authentication is separate from the REST authentication pipeline.

Local authenticated GraphQL mutations use WordPress Application Passwords:

```text
WP_ADMIN_USER
WP_ADMIN_APP_PASSWORD
        ↓
     BasicAuth
        ↓
 GraphQLClient
```

The Docker WordPress service uses:

```yaml
WP_ENVIRONMENT_TYPE: local
```

because the local Docker stack serves WordPress over plain HTTP. This enables
WordPress Application Password authentication in the local environment.

The GraphQL environment therefore has two separate concerns:

```text
Endpoint
  API_ENV → config_graphql.py → GraphQLClient

Authentication
  WP_ADMIN_USER + WP_ADMIN_APP_PASSWORD
             → BasicAuth → GraphQLClient
```


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

If the new microservice exposes GraphQL, follow the same domain structure:

```text
tests/<new_service>/
├── api/                         ← REST behavior
├── graphql/                     ← GraphQL behavior
└── ...
```

Do not create a new GraphQL fixture implementation for each entity. Reuse the
shared `graphql_client` fixture from `EcommerceAPI/plugins/api/shared_graphql.py`.

Framework-level GraphQL contract tests belong under:

```text
tests/shared/contracts/graphql/
```

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
## 🔗 REST and GraphQL — Architecture Summary

REST and GraphQL use the same low-level HTTP transport but have separate
protocol clients:

```text
                         API TESTS
                            │
               ┌────────────┴────────────┐
               │                         │
             REST                     GraphQL
               │                         │
           APIClient                GraphQLClient
               │                         │
               └────────────┬────────────┘
                            │
                        HttpClient
                            │
                     requests.Session
```

The main responsibilities are:

| Component | Responsibility |
|---|---|
| `shared_api.py` | Shared REST pytest infrastructure |
| `shared_graphql.py` | Shared GraphQL pytest infrastructure |
| `APIClient` | REST request orchestration |
| `GraphQLClient` | GraphQL request orchestration |
| `HttpClient` | Low-level HTTP transport |
| Entity plugins | Entity-specific fixtures/helpers |
| Entity tests | Business behavior and assertions |
| `tests/shared/contracts/` | Framework/API contract checks |

GraphQL does not replace or alter the existing REST authentication pipeline.
REST continues to use WooCommerce authentication, while authenticated
GraphQL mutations use WordPress Application Passwords through Basic Auth.

---

## Final note

The framework is designed for multi-team scale: independent microservice test folders, shared plugins for consistent behavior, and CI matrix support for fast, isolated feedback. Keeping Allure generation optional and CI-installed (rather than baked into images) yields smaller images and more reproducible CI runs.

If you want, I can:
- Add a small `scripts/` helper (e.g., `scripts/generate_allure.sh`) to standardize local HTML generation.
- Add a short `workflow_dispatch` input to GitHub Actions for `SERVICE` to make single-service runs easier from the Actions UI.
