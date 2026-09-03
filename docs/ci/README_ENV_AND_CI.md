# 🚀 Environment & CI Runbook

> **Operational guide for local development and Continuous Integration.**

This document explains how to **run**, **debug**, and **operate** the framework during everyday development and CI execution.

Typical topics include:

- 🧪 Local development workflow
- 🔐 `.env` usage
- 📊 Allure reporting
- 🐳 Docker execution
- ⚙️ GitHub Actions / CI configuration
- 🛠️ Operational troubleshooting

---

> 💡 **Looking for the configuration architecture?**
>
> This document intentionally focuses on **operations**, not framework internals.
>
> For the complete configuration architecture, environment resolution and runtime design, see:
>
> - `docs/framework/README_ENVIRONMENT_CONFIG_GUIDE.md`
> - `docs/framework/README_CONFIG_CONTRACT.md`
---

## Local development

### .env
- Copy the example and **do not commit** your real secrets:
  - macOS / Linux / Git Bash:
    ```bash
    cp .env.example .env
    # edit .env
    ```
  - Windows (PowerShell):
    ```powershell
    Copy-Item .env.example .env
    # edit .env in your editor
    ```
- The logging plugin walks upward from the pytest root and uses python-dotenv to load `.env` (with `override=False`), so existing shell env vars are preserved.

---

## 🛠 Typical Development Workflow

A typical development session looks like this:

```text
git pull
    ↓
make run
    ↓
Implement changes
    ↓
pytest
    ↓
Review Allure report
    ↓
Commit
    ↓
Push
    ↓
GitHub Actions
```

---

The same workflow is used by all entity teams
(customers, products, orders and coupons).

### 🎭 Playwright browser setup

Playwright is included as a development dependency of the framework.

When `make run` executes the `install` target, it:

1. Installs the Python development dependencies from `pyproject.toml`.
2. Installs the Playwright browser binaries required for UI tests.

Therefore, a fresh local environment is fully prepared for both
API and UI testing through the existing:

```bash
make run
```

---


### 🦾 Automatic `.env` creation and Playwright setup

For local development, `make run` automatically creates `.env`
from `.env.example` the first time it is executed.

During the bootstrap process, WooCommerce automatically generates
a fresh pair of REST API credentials for the newly provisioned
WordPress installation. These credentials are then merged into
`.env` by `write_env_credentials.sh`.

The same `make run` bootstrap also installs the project's Python
development dependencies and Playwright browser binaries.

**Playwright browser installation:** The Playwright Python package
is declared in `pyproject.toml` as a development dependency.
The required browser binaries are installed automatically by the
Makefile, so developers do not need to run `playwright install`
manually.

Authentication credentials are updated as part of bootstrap:

- `WC_KEY`
- `WC_SECRET`
- `WP_ADMIN_USER`
- `WP_ADMIN_APP_PASSWORD`

All other developer-specific settings remain unchanged.

---

### ⚙️ Endpoint configuration

Unlike previous framework versions, the framework no longer stores
API endpoint URLs inside `.env`.

Instead, the active endpoint is resolved dynamically from
`API_ENV` using the entity configuration files
(`config_customers.py`, `config_products.py`, etc.).

This separation provides several advantages:

- 🔐 Authentication and infrastructure remain independent
- 🌍 Switching environments only requires changing `API_ENV`
- 🐳 Docker, local development and CI use the same configuration model
- 🧩 Entity teams own their endpoint mappings without modifying `.env`

GitHub Actions follows the same architecture. Instead of writing
a repository `.env` file, the bootstrap process generates fresh
WooCommerce credentials and exports them directly into the workflow
environment.

> 📖 For the complete environment architecture and endpoint resolution
> process, see:
>
> `docs/framework/README_ENVIRONMENT_CONFIG_GUIDE.md`

---

### GraphQL endpoint configuration

GraphQL follows the same environment-selection principle as REST, but uses
dedicated GraphQL configuration.

```text
API_ENV
   ↓
config_graphql.py
   ↓
graphql_client fixture
   ↓
GraphQLClient
```

The GraphQL endpoint is infrastructure configuration and must not be
hardcoded inside individual GraphQL tests.

GraphQL authentication is also separate from WooCommerce REST
authentication:

```text
REST
WC_KEY + WC_SECRET
       ↓
     OAuth1
       ↓
WooCommerce REST API
```

```text
GraphQL
WP_ADMIN_USER + WP_ADMIN_APP_PASSWORD
       ↓
    BasicAuth
       ↓
    WPGraphQL
```

The local bootstrap provisions the WordPress credentials required for
authenticated GraphQL operations and preserves them in `.env` alongside
the REST credentials.

GitHub Actions does not use the repository `.env` file. The CI environment
is provisioned during the workflow and the required credentials are
exported directly into the workflow environment.

> 📖 For the complete GraphQL endpoint and authentication flow, see:
>
> `docs/development/README_GRAPHQL_TESTING_GUIDE.md`

---


### Run pytest (Allure results)
- Run full suite and write Allure results (repo root):
```bash
pytest tests --alluredir=./reports/allure-results
```
- Run a single microservice:
```bash
pytest tests/customers --alluredir=./reports/customers/allure-results
```
- If you run tests inside containers, the `SERVICE` env var (or Docker `ARG`) will also limit the scope.

### Generate Allure HTML locally
- Allure CLI is not bundled in the test Docker image. Install it locally if you want HTML:
  - macOS (Homebrew):
    ```bash
    brew install allure
    ```
  - Linux (manual):
    ```bash
    ALLURE_VER=2.29.0
    curl -fsSL "https://github.com/allure-framework/allure2/releases/download/${ALLURE_VER}/allure-${ALLURE_VER}.tgz" \
      | tar -xz -C /opt
    sudo ln -s /opt/allure-${ALLURE_VER}/bin/allure /usr/local/bin/allure
    ```
- Or use the helper script included in this repo:
  ```bash
  # generate HTML from results (default: reports/allure-results)
  ./scripts/generate_allure.sh reports/customers/allure-results
  ```

---

## Helper: scripts/generate_allure.sh (recommended)
Create `scripts/generate_allure.sh` (executable). It downloads a temporary Allure binary if none is found and generates the HTML report.

Usage:
```bash
chmod +x scripts/generate_allure.sh
./scripts/generate_allure.sh reports/customers/allure-results
```

(If you want, I can add this script to the repo — say the word and I’ll produce the file content.)

---

## Docker notes (developer image)

- The runtime image intentionally does **not** include Allure CLI (keeps image small). CI installs Allure during the job runtime when HTML is required.
- Default behavior:
  - Results written to `reports/allure-results` or `reports/<service>/allure-results` when `SERVICE` is set.
  - If `AUTO_ALLURE_REPORT=true` and `allure` exists on PATH, the image will attempt to generate HTML after pytest finishes.
- Run examples:
  - Run everything:
    ```bash
    docker run --rm my-ecommerce-tests
    ```
  - Run one service:
    ```bash
    docker run --rm -e SERVICE=customers my-ecommerce-tests
    ```
  - Run without auto HTML generation:
    ```bash
    docker run --rm -e AUTO_ALLURE_REPORT=false my-ecommerce-tests
    ```

> Tip: when running locally and your image lacks Allure, set `AUTO_ALLURE_REPORT=false` and use the helper script on host to generate HTML.

---

## CI / Production best practices

- Never commit `.env` with real secrets. Use CI provider secret stores:
  - GitHub Actions: *Repository → Settings → Secrets → Actions*
  - GitLab CI: *Project → Settings → CI/CD → Variables* (use protected/masked for sensitive values)

Recommended CI habits:
1. Use a matrix of jobs (one per microservice) to get fast, isolated feedback.
2. Install Allure CLI in the job runtime (per-job installation) — do not bake it into the runtime Docker image.
3. Use `--alluredir` to write results to a predictable location (per-service folder for matrix jobs).
4. Generate and publish reports even on failed test runs to preserve trend consistency.

### GitHub Actions — workflow_dispatch example
Add `workflow_dispatch` with an optional `SERVICE` input so you can run one service manually from the Actions UI:

```yaml
on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]
  workflow_dispatch:
    inputs:
      SERVICE:
        description: 'Optional single service to run (e.g. customers)'
        required: false
        default: ''
```

### Install Allure in a workflow & upload artifacts
Example steps (insert into your job):
```yaml
- name: Install Allure CLI
  if: env.AUTO_ALLURE_REPORT == 'true'
  run: |
    ALLURE_VER="2.29.0"
    curl -fsSL "https://github.com/allure-framework/allure2/releases/download/${ALLURE_VER}/allure-${ALLURE_VER}.tgz" | tar -xz
    sudo mv "allure-${ALLURE_VER}" /opt/allure-${ALLURE_VER}
    sudo ln -sf /opt/allure-${ALLURE_VER}/bin/allure /usr/bin/allure
    allure --version

- name: Generate Allure HTML (if results exist)
  if: env.AUTO_ALLURE_REPORT == 'true'
  run: |
    RESULTS=reports/${{ matrix.service }}/allure-results
    if [ -d "$RESULTS" ] && [ "$(ls -A $RESULTS)" ]; then
      allure generate "$RESULTS" -o reports/${{ matrix.service }}/allure-report --clean || true
    else
      echo "No Allure results for ${{ matrix.service }}; skipping."
    fi

- name: Upload Allure results & report
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: allure-${{ matrix.service }}
    path: |
      reports/${{ matrix.service }}/allure-results/**
      reports/${{ matrix.service }}/allure-report/**
```

This ensures results and HTML are downloadable from the Actions UI even if the job fails.

### GitLab CI — child job artifacts
When dynamically generating child jobs, ensure each generated job includes `artifacts` so CI stores results/report:

```yaml
artifacts:
  when: always
  paths:
    - reports/$s/allure-results/**
    - reports/$s/allure-report/**
```

---


## Persistent Allure History (GitHub Pages)

This project publishes Allure reports to GitHub Pages with persistent history/trend support.

The CI pipeline performs the following flow:

1. Restore previous Allure `history/`
2. Generate a fresh report
3. Publish report to `gh-pages`
4. Preserve trend data across executions

This enables:

- 📈 Pass/fail trends
- ⏱ Duration evolution
- 🔁 Retry history
- ⚠️ Flaky test visibility
- 📊 Historical execution analytics

Live report:

```text
https://kwakic.github.io/TestingWoocommerceAPI/
```

The report job is configured with:

```yaml
if: always()
```

This ensures reports are still generated and deployed even when tests fail, preserving historical trend accuracy.

### GitHub Pages history preservation

The deployment step uses:

```yaml
keep_files: true
```

This prevents previous Allure history/trend files from being deleted during deployment.

### Restore previous Allure history

Before generating a new report, CI restores:

```text
gh-pages/history
```

into:

```text
reports/allure-results/history
```

This is required for Allure trend graphs and historical charts to function correctly across multiple executions.

### Recommended reporting flow

```text
pytest
  ↓
generate allure-results
  ↓
restore previous history
  ↓
generate new report
  ↓
deploy to gh-pages
  ↓
preserve trends for next execution
```

Generate and publish reports even on failed test runs to preserve trend consistency and historical analytics.


---

## Troubleshooting checklist

- "No Allure results / no HTML":
  - Confirm pytest ran with `--alluredir` and the results directory is non-empty.
  - Confirm `AUTO_ALLURE_REPORT` is set to `"true"` (CI) if you expect auto-generation.
  - If running in container, ensure `LOG_DIR` and `reports/` are writable.

- "Structured logs missing":
  - Ensure `ENABLE_STRUCTURED_LOGS=true`
  - Confirm `LOG_DIR` is writable and plugin creates files there (JSONL)

- "0 tests collected":
  - Run: `pytest --collect-only -q tests/`
  - Confirm package importable: `python -c "import EcommerceAPI; print(getattr(EcommerceAPI,'__file__','NOT IMPORTABLE'))"`
  - Disable plugins for debugging:
    ```bash
    pytest --collect-only -q tests/ -p no:allure_pytest -p no:faker -p no:pytest_metadata
    ```

---
## ⚠️ Note:
### Never use in CI:

```
latest
latest-stable
nightly
edge
```

Because:

* CI becomes nondeterministic
* builds randomly break
* historical runs become unreproducible
