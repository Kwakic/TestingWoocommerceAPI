# Framework Overview — TestEcommerceAPI 🚀

A short, high-level introduction for new contributors, product/QA teams, and cross-team readers.
Covers purpose, quick-start steps, key conventions, and where to find deeper docs (see README_ARCHITECTURE.md for architecture details).

---

## Purpose — what this repo is for
- Provide a reusable, team-friendly API test framework for the EcommerceAPI (WooCommerce) ecosystem.
- Run fast preflight checks and full regression suites per microservice (customers, orders, products, coupons).
- Produce machine- and human-friendly outputs: structured JSONL logs for ingestion and Allure results/HTML for test reporting.
- Make it easy to run tests locally, in containers, and in CI (GitHub Actions / GitLab).

Who should read this
- New engineers joining the test team
- Product/QA stakeholders wanting to understand test coverage & reports
- Cross-functional teams integrating with the API who want to run or extend tests

---

## Quick start (1–2 minute checklist)
1. Clone and create a branch:
   ```bash
   git clone git@github.com:org/TestEcommerceAPI.git
   cd TestEcommerceAPI
   git checkout -b feat/my-change
   ```
2. Create & activate venv:
   - macOS / Linux:
     ```bash
     python -m venv .venv
     source .venv/bin/activate
     ```
   - Windows (PowerShell):
     ```powershell
     python -m venv .venv
     . .venv/Scripts/Activate.ps1
     ```
3. Install editable package + dev extras:
   ```bash
   pip install --upgrade pip setuptools wheel
   pip install -e './EcommerceAPI[dev]'
   ```
4. Run a single test:
   ```bash
   pytest tests/customers/api/test_create_customer_negative.py::test_create_single_customer_with_email_and_password_only -q -vv
   ```
5. Run matrix locally with Docker:
   ```bash
   docker compose -f docker-compose.matrix.yml build
   docker compose -f docker-compose.matrix.yml --profile customers up --abort-on-container-exit --remove-orphans
   ```

For full developer setup and step-by-step onboarding, see: `DEVELOPER_ONBOARDING.md`.

---

## Key conventions & patterns

- Repo layout
  - `EcommerceAPI/` — framework package and package-level `pyproject.toml`.
  - `tests/` — per-microservice test suites (e.g. `tests/customers/`, `tests/orders/`).
  - `reports/` — Allure results, generated HTML, structured logs.
  - `.github/`, `.gitlab/` — CI pipeline configs.

- Packaging & install
  - Two `pyproject.toml` files (root: tool configs; package-level: packaging + extras).
  - Use editable install for development: `pip install -e './EcommerceAPI[dev]'`.

- Test discovery & structure
  - Root-level pytest config controls discovery (`[tool.pytest.ini_options]`).
  - Tests follow naming: `test_*.py`, `Test*` classes, `test_*` functions.
  - Markers used: `preflight`, `schema`, `api`, `smoke`, `regression`, `integration`, `performance`.
  - Schema validation runs per-test (via `APIClient` and helper assertions) — not just in preflight.

- Helpers & fixtures
  - `APIClient` — central HTTP client with retries, OAuth1, schema validation, and structured logging hooks.
  - Helper classes (e.g., `CustomersHelper`) encapsulate API operations and domain assertions.
  - Factory fixtures like `create_valid_customer` validate responses by default and register created resources for teardown.

- Logging & reporting
  - Human logs: `custom_logger.CustomFormatter` (console); live pytest logging is used for human view.
  - Structured logs: per-team JSONL files under `reports/...` when `ENABLE_STRUCTURED_LOGS` is enabled.
  - Allure integration: tests write `--alluredir=reports/<service>/allure-results`; CI installs Allure CLI to generate HTML.

- CI & matrix testing
  - GitHub Actions: dynamic matrix of services (discover step outputs JSON array used with matrix.strategy).
  - GitLab CI: discover job creates `matrix.yml` artifact with one child job per service.
  - Use `AUTO_ALLURE_REPORT` to control whether HTML is generated in CI.

---

## Where to find deeper docs

- Developer onboarding and CLI commands:
  - `DEVELOPER_ONBOARDING.md` — full developer setup & troubleshooting
- Architecture and internals:
  - `README_ARCHITECTURE.md` — design overview and component responsibilities
- Schema & validation:
  - `SCHEMA_VALIDATION_GUIDE.md` — how schemas are used, where they live, and how to add new schemas
- Environment & CI:
  - `README_ENV_AND_CI.md` — Allure, .env, Docker and CI best practices
- Contribution & workflows:
  - `CONTRIBUTING.md` — PR guidelines, test expectations, and branch workflow
- Logging & diagnostics:
  - `EcommerceAPI/src/utilities/custom_logger.py`, `EcommerceAPI/plugins/logging_plugin.py`
- Tests & fixtures examples:
  - `tests/shared/api_fixtures.py` — common fixtures (api_client, factory fixtures)
  - `tests/customers/helpers/customers_helper.py` — sample helper showing patterns

---

## Common questions & tips

- “Why two pyproject files?”
  Keeps packaging metadata close to the package while keeping repo-level tool configs (pytest/linters) at root.

- “Why editable install?”
  Makes `EcommerceAPI` importable without mangling `PYTHONPATH` and reflects live changes during development.

- “Where are test failures reported?”
  - Human: pytest console and Allure HTML (CI uploads artifacts).
  - Machine: structured JSONL logs under `reports/` (when enabled).

- “How to debug warnings & import-order issues?”
  - Run pytest without `--disable-warnings` (override addopts) and consider lazy imports for plugin modules. See `EcommerceAPI/plugins/logging_plugin.py` and `_config.py` for patterns.

---

## How to contribute improvements
- Small changes: branch → commit → PR against `main` (or `develop`) and ensure relevant tests pass locally.
- Add tests for any functional change. For docs or config changes, include reproduction steps.
- Use `CONTRIBUTING.md` for PR template and expectations.

---

## Contacts & support
- For framework-level decisions, open an issue titled `framework: ...` and tag the test leads.
- For flaky tests or CI failures, include:
  - failing job logs
  - pytest command used
  - environment (OS, Python, pytest version)
  - Any recent related PRs

---

This document is the high-level landing page for contributors and stakeholders. For architecture details see `README_ARCHITECTURE.md`.
