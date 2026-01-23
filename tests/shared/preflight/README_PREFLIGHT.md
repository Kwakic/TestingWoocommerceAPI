# Preflight & Diagnostic Test Suite

## Overview
The **Preflight Test Suite** performs *environmental, schema, and API readiness checks*  
before any main feature or regression tests are executed.

It helps ensure the entire QA framework is in a **valid, stable, and connected** state before testing.

---

## ✅ Purpose

Preflight tests **do not test business logic** — they validate:
- 🔑 Environment variables and credentials are configured.
- 🗄️ Database and API endpoints are reachable.
- 🧩 JSON schemas for main entities (`customers`, `orders`, `products`, `coupons`) are valid.
- 🌐 Core API responses return expected structures and sample data.

If any of these fail, the suite halts **before** main tests run — preventing false negatives and wasted CI minutes.

---

## 🧱 Execution Behavior

### 🧪 Local Runs

Developers can quickly verify environment and API readiness with:

```bash
pytest -m preflight -v
```

If a preflight test fails, pytest stops immediately before running any feature or regression tests.

### ⚙️ CI/CD Runs

**1. GitHub Actions** (or any CI system), preflight tests run first to validate the environment.

```yaml
jobs:
  preflight:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repo
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run preflight tests
        env:
          FAIL_ON_EMPTY_LIST: "true"
        run: pytest -m preflight -v --junitxml=reports/preflight-junit.xml
```
✅ Recommended for GitHub: use the env: block. It’s cleaner and easily visible in your Actions UI.   
✅ The **`preflight` job** validates environment and API readiness.  
✅ The **`full_suite` job** executes only if preflight passes.  
✅ Save `reports/preflight-junit.xml` as a workflow artifact for inspection.

**2. GitLab CI/CD (.gitlab-ci.yml)** (or any CI system), preflight tests run first to validate the environment.

```yaml
stages:
  - test

schema_tests:
  stage: test
  image: python:3.12
  variables:
    FAIL_ON_EMPTY_LIST: "true"  # 👈 Environment variable
  script:
    - pip install -r requirements.txt
    - pytest -v tests/preflight/ --junitxml=reports/preflight-junit.xml
```

**3. Jenkins (Declarative Pipeline)** (or any CI system), preflight tests run first to validate the environment.

```groovy
pipeline {
    agent any

    environment {
        FAIL_ON_EMPTY_LIST = "true"   // 👈 Environment variable for pytest
    }

    stages {
        stage('Install') {
            steps {
                sh 'pip install -r requirements.txt'
            }
        }

        stage('Schema Validation Tests') {
            steps {
                sh 'pytest -v tests/preflight/ --junitxml=reports/preflight-junit.xml'
            }
        }
    }
}
```

---

## ⚙️ CLI Flags and Configuration

### 1️⃣ Schema Tests — Handling Empty Lists

Some API endpoints may temporarily return empty lists (e.g., due to cleanup).  
To prevent preflight from failing unnecessarily, this behavior is **configurable**:

| Option | Description | Default |
|--------|--------------|----------|
| `--fail-on-empty-list` | CLI flag to fail schema tests on empty responses | `False` |
| `FAIL_ON_EMPTY_LIST` | Environment variable alternative (for CI) | `"false"` |

**Usage Examples:**

**Local:**
```bash
pytest -v tests/preflight/test_schema_validation_smoke.py --fail-on-empty-list
```

**CI/CD (.yaml):**
```yaml
env:
  FAIL_ON_EMPTY_LIST: "true"
```

### 2️⃣ Performance Tests — Dynamic Iteration Control

| Option | Description | Default |
|--------|--------------|----------|
| `--perf-iterations` | Number of runs per API endpoint | `5` |

**Local Example:**
```bash
pytest -m performance --perf-iterations=10
```

**CI/CD Example:**
```yaml
env:
  PERF_ITERATIONS: 10
```

---

## 🧩 Test Categories

| File                              | Description | Checks Performed |
|-----------------------------------|--------------|------------------|
| `test_healthcheck.py`             | **API Health Check** | Ensures WooCommerce or backend API is reachable and responsive |
| `test_schema_validation_smoke.py` | **Schema Validation Tests** | Validates JSON schemas for all major entities |
| `test_basic_response_times.py`    | **Performance Benchmark** | Measures and reports response times for key endpoints |

---

## 🧠 Test Markers and Ordering

All preflight tests are tagged with `@pytest.mark.preflight`.

This allows you to:
- Run only preflight tests:
  ```bash
  pytest -m preflight
  ```
- Ensure they **run first** in CI (by job dependency or explicit stage ordering).

**Example CI ordering logic:**
```yaml
jobs:
  preflight:
    runs: pytest -m preflight
  main_suite:
    needs: preflight
```

---

## ✅ How to see skipped endpoints and reasons

Preflight tests will skip endpoints when lists are empty by default (unless `--fail-on-empty-list` / `FAIL_ON_EMPTY_LIST` is set). Skips are explicit and visible in pytest output and reports.

- Quick command that shows skipped reasons in the summary:
  ```bash
  pytest -m preflight -q -r s
  ```
  - `-r s` instructs pytest to print skipped reasons in the short test summary.
  - Example output line:
    ```
    tests/preflight/test_schema_validation_smoke.py::test_schema_validation[products] SKIPPED (products returned 0 items — skipping preflight schema check)
    ```

- To see live logging while running (helpful when debugging):
  ```bash
  pytest -m preflight -s -q -r s
  ```

- JUnit XML (CI):
  - When you run `pytest --junitxml=reports/preflight-junit.xml`, skipped tests are recorded in the XML. CI tools will report skipped counts and you can inspect the XML for skip reasons.

### Optional: Fail the pipeline if any preflight tests are skipped
If you want CI to treat skipped preflight tests as a condition for failure (strict gating), you can add a small check step after pytest that parses the JUnit XML and fails if `<skipped>` > 0.

Example GitHub Actions step (after pytest):

```yaml
- name: Fail on skipped preflight
  if: always()
  run: |
    python - <<'PY'
    import xml.etree.ElementTree as ET
    tree = ET.parse('reports/preflight-junit.xml')
    root = tree.getroot()
    skipped = sum(int(tc.get('skipped', '0')) for tc in root.findall('.//testsuite'))
    # Alternate: check <skipped> tags depending on junit output shape
    if skipped > 0:
        print(f"Found {skipped} skipped tests in preflight; failing job per policy.")
        raise SystemExit(1)
    else:
        print("No skipped preflight tests found.")
    PY
```

---

## 🧱 Architecture Overview

```
EcommerceAPItest/
├── configs/              # Environment configs
├── src/                  # Utilities, DAOs, helpers, schemas
├── tests/
│   ├── conftest.py       # Global fixtures and CLI options (--fail-on-empty-list, --perf-iterations)
│   ├── preflight/
│   │   ├── test_healthcheck.py
│   │   ├── test_schema_validation_smoke.py
│   ├── api/
│   │   ├── performance/
│   │   │   ├── test_basic_response_times.py
│   │   │   ├── reports/
│   │   ├── customers/
│   │   ├── products/
│   │   ├── orders/
│   │   ├── coupons/
│   └── ...
├── pytest.ini
└── .env
```

---

## 🔧 Operational Notes

- The test suite uses a `truncate_preview` utility to keep failure messages bounded in size. See `EcommerceAPItest/src/utilities/truncate_logging_utils.py`.
- RequestUtility wraps JSON schema validation errors in `SchemaValidationError`. Preflight tests catch both `jsonschema.ValidationError` and `SchemaValidationError` and report concise diagnostics.
- Preflight tests are read-only by design — they should not create, update, or delete production data.

---

## 📄 Summary Table

| Stage | Purpose | Trigger | Outcome |
| ----- | ------- | ------- | ------- |
| Preflight | Validate environment, DB, API readiness | Runs first (local + CI) | Blocks full suite if fails |
| Full Suite | Execute feature and regression tests | Runs only if preflight passes | Produces test results & artifacts |

---

## ✅ Quick Checklist for Contributors
- Ensure required environment variables are set before running tests.
- Run preflight locally to validate your dev environment:
```bash
pytest -m preflight -s -q -r s
```
- In CI, ensure `preflight` runs before the full suite and that `FAIL_ON_EMPTY_LIST` is set if you want stricter schema checks.
- Add new global CLI flags to `conftest.py` and document them in this README.

---