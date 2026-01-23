# TestEcommerceAPI – Unified API Automation Suite

A unified, multi-team API automation platform for testing Customers, Orders, Coupons, Products, and other microservices in the Ecommerce ecosystem.

This README reflects the current repository layout and recent changes:
- Reporting moved to Allure (pytest writes Allure results; CI generates HTML).
- Plugins are modular and live under the shared framework package.
- CI keeps matrix testing (one job per microservice) and installs Allure at job runtime.
- Runtime Docker images are kept small and do not include Allure by default.

---

## Repository layout (important parts)

Top-level (trimmed):

```
TestEcommerceAPI/
├── .github/workflows/ci.yaml
├── .gitlab/ci.yaml
├── EcommerceAPI/                 ← SHARED installable framework (package root)
│   ├── plugins/                  ← shared pytest plugins (only plugins here)
│   │   ├── __init__.py
│   │   ├── _config.py
│   │   ├── logging_plugin.py
│   │   ├── reporting.py
│   │   ├── allure_autogen.py     ← Allure lifecycle + optional auto-generation
│   │   ├── api_fixtures.py
│   │   ├── db_fixtures.py
│   │   └── entities.py
│   ├── src/                      ← reusable utilities, configs, helpers
│   ├── pyproject.toml
│   └── cli.py
├── reports/                      ← host-mounted test output (Allure + logs)
│   ├── allure-report/            ← generated HTML (CI/host)
│   ├── allure-results/           ← Allure raw results (json/xml/attachments)
│   └── logs/
│       └── <team>/<env>/...jsonl  ← structured JSONL logs per-team / env
├── tests/
│   ├── customers/
│   ├── orders/
│   ├── coupons/
│   ├── products/
│   └── shared/
├── docker-compose.matrix.yml
├── Dockerfile
├── conftest.py                    ← top-level pytest loader that sets pytest_plugins
└── pytest.ini
```

---

## Shared framework package (EcommerceAPI)

- This folder is a pip-installable package: use `pip install -e EcommerceAPI` for local development.
- Only *shared* pytest plugins belong in `EcommerceAPI/plugins/`. They are global to all test suites.
- `EcommerceAPI/src/` contains universal utilities used by all microservices (logging, request helpers, env utils, etc.).

Key shared plugins:
- `logging_plugin.py` — logging setup, ContextVar injection, early redaction, structured JSONL output, and session metadata.
- `reporting.py` — Allure labels + attach structured JSONL logs on failed tests.
- `allure_autogen.py` — ensures results directory lifecycle and optionally generates Allure HTML at session finish if `AUTO_ALLURE_REPORT` is enabled.
- `api_fixtures.py`, `db_fixtures.py`, `entities.py`, `_config.py` — other shared fixtures/config.

---

## How plugins are loaded

Top-level `conftest.py` uses:

```python
pytest_plugins = [
    "EcommerceAPI.plugins.logging",        # MUST load first
    "EcommerceAPI.plugins._config",
    "EcommerceAPI.plugins.reporting",
    "EcommerceAPI.plugins.allure_autogen", # manage Allure lifecycle
    "EcommerceAPI.plugins.entities",
    "EcommerceAPI.plugins.db_fixtures",
    "EcommerceAPI.plugins.api_fixtures",
]
```

Order matters: logging must load first so all log records are created with the custom factory and redaction rules.

---

## Running tests (local & CI)

General recommendations and examples.

- Run full test suite and produce Allure results:

  ```bash
  pytest tests --alluredir=reports/allure-results
  ```

- Run a single microservice (e.g. `customers`) and write results to per-service folder:

  ```bash
  pytest tests/customers --alluredir=reports/customers/allure-results
  ```

- CI & matrix jobs: each matrix job should run only one service and write results to `reports/<service>/allure-results`.

- To generate HTML (Allure):
  - CI: install Allure CLI in the job and run:
    ```bash
    allure generate reports/<service>/allure-results -o reports/<service>/allure-report --clean
    ```
    The `allure_autogen` plugin can also attempt generation automatically when `AUTO_ALLURE_REPORT=true` and `allure` is present.
  - Local: install Allure CLI (Homebrew or manual tarball) and run the command above.

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

## CI (GitHub Actions & GitLab)

- The project keeps matrix testing (one job per microservice). Benefits:
  - Parallel runs → faster feedback
  - Failure isolation per team/service

- Recommended CI behavior:
  - Install project dependencies (`pip install -e .[test]`).
  - Run pytest for the single service in the job with `--alluredir=reports/<service>/allure-results`.
  - If `AUTO_ALLURE_REPORT=true`, install Allure CLI in the job and generate HTML only if results exist.
  - Upload artifacts:
    - `reports/<service>/allure-report/**` (HTML)
    - `reports/<service>/allure-results/**` (raw results)
    - `EcommerceAPI/tests/api/logs/<service>/**/*.jsonl` (structured logs)

- Running a single-service pipeline:
  - GitHub: set the `SERVICE` env (or add `workflow_dispatch` input) to run only that service in discovery step.
  - GitLab: set the `SERVICE` CI variable to limit the child pipeline to the specified service.

---

## Environment & configuration

- Use `.env` for local convenience; do NOT commit secrets.
- CI: store secrets in your provider (GitHub Secrets / GitLab CI variables / cloud secret manager).
- `REQUIRE_ENV`:
  - Locally: keep `REQUIRE_ENV=false` (or unset).
  - CI: set `REQUIRE_ENV=true` to fail early on missing configuration.

- Key env vars used by plugins/CI:
  - `AUTO_ALLURE_REPORT` — set to `"true"` / `"1"` / `"yes"` to enable auto-generation of HTML (CI should install Allure).
  - `ENABLE_STRUCTURED_LOGS`, `ENABLE_JSON_PRETTY`, `KEEP_STRUCTURED_LOGS`, `LOG_DIR` — control structured logging behavior.

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
  - Ensure `EcommerceAPI.plugins.logging` loads first (conftest order) — it installs the LogRecord factory.

---

## Quick commands

- Install framework locally:
  ```bash
  pip install -e EcommerceAPI
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

## Final note

The framework is designed for multi-team scale: independent microservice test folders, shared plugins for consistent behavior, and CI matrix support for fast, isolated feedback. Keeping Allure generation optional and CI-installed (rather than baked into images) yields smaller images and more reproducible CI runs.

If you want, I can:
- Add a small `scripts/` helper (e.g., `scripts/generate_allure.sh`) to standardize local HTML generation.
- Add a short `workflow_dispatch` input to GitHub Actions for `SERVICE` to make single-service runs easier from the Actions UI.