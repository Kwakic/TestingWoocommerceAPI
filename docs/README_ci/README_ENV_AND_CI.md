# Environment & CI Notes — local & CI runbook 🧭

## Operational guide ("How do I run this?")

This document explains local `.env` usage, Allure reporting, Docker test image behavior, and CI best practices (GitHub Actions / GitLab). It also includes small helper snippets and tips to make running and debugging easier.

> Summary: keep secrets in CI, use editable installs for local dev, write Allure results with `--alluredir`, and generate HTML in CI or via the helper script locally.

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

## REQUIRE_ENV strict mode

- Local: leave `REQUIRE_ENV=false` (or unset) for developer convenience. The logging plugin loads `.env` permissively.
- CI: set `REQUIRE_ENV=true` to fail fast when required config is missing.

Example:
```bash
# locally (dev)
export REQUIRE_ENV=false
pytest ...

# CI (recommended)
export REQUIRE_ENV=true
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

### Recommended enterprise reporting flow

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
