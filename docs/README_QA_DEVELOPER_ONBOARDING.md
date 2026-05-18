# Developer Onboarding — TestEcommerceAPI

Quick guide to set up a developer environment, run tests locally, and contribute.

> Recommended canonical file: keep this as the single onboarding doc and remove duplicate DEV_SETUP.md.

---

## Prerequisites
- Python 3.9+ (3.11 recommended)
- pip, virtualenv
- Git
- Docker & Docker Compose (optional — for matrix runs)
- IDE: VS Code, PyCharm, or similar
- (Optional) curl, jq for CI troubleshooting

---

## Repo layout (short)
- `EcommerceAPI/` — shared, installable framework (package-level pyproject)
- `tests/` — per-service test suites (customers, orders…)
- `reports/` — Allure results & test artifacts
- `.github/`, `.gitlab/` — CI pipelines
- `pyproject.toml` (repo root) — tooling config (pytest, etc.)
- `EcommerceAPI/pyproject.toml` — packaging metadata & extras

We intentionally use two `pyproject.toml` files:
- Root for toolkit/test config.
- Package-level for packaging/install metadata.

---

## Quick Setup (copy/paste)

1) Clone & branch
```bash
git clone git@github.com:org/TestEcommerceAPI.git
cd TestEcommerceAPI
git checkout -b feat/your-change
```

2) Create & activate virtual environment
```bash
# Create venv
python -m venv .venv

# Activate:
# Windows (PowerShell)
. .venv/Scripts/Activate.ps1
# Windows (cmd)
.venv\Scripts\activate.bat
# macOS / Linux
source .venv/bin/activate
```

3) Upgrade packaging tools
```bash
pip install --upgrade pip setuptools wheel
```

4) Install the shared framework (editable) with dev extras
```bash
# From repo root (recommended)
# Activate local virtual environment
source .venv/Scripts/activate

# Upgrade packaging tooling
python -m pip install --upgrade pip setuptools wheel

# Install framework + dev dependencies
python -m pip install -e "./EcommerceAPI[dev]"
```
- This makes `import EcommerceAPI` resolve to your live source.
- Use the same install (`.[dev]`) in CI and Docker to avoid surprises.

Optional legacy approach (not recommended):
```bash
pip install -e EcommerceAPI
pip install -r requirements.txt
```

5) Verify importability
```bash
python -c "import EcommerceAPI; print(getattr(EcommerceAPI,'__file__','NOT IMPORTABLE'))"
```
Expected: path inside your repository (editable install).

---

## Configure environment variables
Copy and edit environment example:
```bash
cp .env.example .env
# edit .env (or set shell env vars)
```
Typical vars: `BASE_URL`, `CUSTOMERS_BASE_URL`, `ORDERS_BASE_URL`, `AUTH_USERNAME`, `AUTH_PASSWORD`, DB connection vars if needed.

> Do not commit secrets — use CI secrets for pipelines.

---

## Running tests (recommended commands)

- Show pytest config (turn off live logging to see pytest trace clearly):
```bash
pytest -o log_cli=false --trace-config
```

- See discovery:
```bash
pytest --collect-only -q tests/
```

- Run the whole suite (quiet):
```bash
pytest -q
```

- Run a single service folder:
```bash
pytest tests/customers -q
```

- Run a single file (verbose):
```bash
pytest tests/customers/api/test_get_customer.py -q -vv
```

- Run a single test function:
```bash
pytest tests/customers/api/test_create_customer.py::test_name -q -vv
```

---

## Troubleshooting: “0 tests collected”
1. Avoid filters while debugging (`-m`, `-k`, `-q`).
   Run `pytest --collect-only -q tests/`.
2. Confirm package importable (see step 5 above).
3. Check for environment-level filters:
   - Linux/macOS: `echo "$PYTEST_ADDOPTS"`
   - PowerShell: `echo $env:PYTEST_ADDOPTS`
4. Disable third-party plugins if you suspect interference:
```bash
pytest --collect-only -q tests/ -p no:allure_pytest -p no:faker -p no:pytest_metadata
```
5. Look for collection hooks (`pytest_collection_modifyitems`) or `collect_ignore` in `conftest.py` or plugins.
6. Use verbose collect to surface errors:
```bash
pytest --collect-only -vv tests/
```

---

## Run tests in Docker (matrix)
- Build test image:
```bash
docker compose -f docker-compose.matrix.yml build
```
- Run a single profile locally:
```bash
docker compose -f docker-compose.matrix.yml --profile customers up --abort-on-container-exit --remove-orphans
```
Notes:
- `./tests` is mounted read-only inside the container; `./reports` collects outputs.
- Dockerfile installs the package editable during the build stage using `.[dev]`.
- Allure CLI is **not** included in the image (CI installs it when generating HTML).

---

## CI notes (summary)
- GitHub Actions and GitLab dynamic pipelines should install dev extras:
```bash
pip install -e './EcommerceAPI[dev]'
```
- GitHub matrix discovery should output a JSON array of quoted service names (e.g. `["customers","orders"]`) to feed the matrix.
- GitLab discover job dynamically creates `matrix.yml` at runtime; that artifact is referenced by the trigger.

---

## Adding tests & fixtures
- Add tests in the appropriate service directory:
```
tests/<service>/api/test_new_feature.py
```
- Name files `test_*.py`, classes `Test*`, functions `test_*`.
- Reuse fixtures in `tests/<service>/conftest.py` or shared fixtures in `tests/shared/` or framework plugins (`EcommerceAPI/plugins/`).
- If adding a new marker, document it under `[tool.pytest.ini_options].markers` in root `pyproject.toml`.

---

## Making changes & PRs
1. Create a branch:
```bash
git checkout -b feat/short-description
```
2. Run the tests relevant to your change.
3. Commit small, focused changes:
```bash
git add .
git commit -m "fix: short explanation"
git push origin feat/short-description
```
4. Open a PR against `main` (or `develop`) and include:
- What changed and why
- How to run tests locally
- Any CI/Docker impact

---

## Helpful commands & debugging
- Show config & plugins:
```bash
pytest -o log_cli=false --trace-config
```
- List discovered tests:
```bash
pytest --collect-only -q tests/
```
- Run a failing test with full tracebacks:
```bash
pytest tests/customers/api/test_create_customer.py -q -vv
```

---

## Tips & best practices
- Keep extras consistent: use `dev` in `EcommerceAPI/pyproject.toml`.
- Prefer editable install to `pythonpath` entries in pytest config.
- Keep a single repo-level pytest config for discovery consistency.
- Use `.dockerignore` to reduce Docker build context (`.venv/`, `reports/`, `build/`, etc.).

---

If you want, I can:
- Add a `bootstrap.sh` or `Makefile` that automates steps 2–5,
- Open a small PR that (a) updates Dockerfile and CI to `.[dev]`, and (b) removes the duplicate `DEV_SETUP.md`.
Which would you prefer?

------------------------------------------------------------------
# 🧪 Shared Test Suites (Framework-Level Tests)

The framework also contains shared tests that validate infrastructure,
security, and environment behavior before running entity-specific tests.

Directory structure:

tests/shared/

    preflight/
        test_api_connectivity.py
        test_response_format.py
        test_logging_globals.py

    security/
        test_authentication_matrix.py
        test_authentication_success.py

    performance/
        test_basic_response_times.py

Purpose of each category:

Preflight tests
---------------
Verify the test environment and framework configuration before executing
the full test suite.

Examples:
- API connectivity
- logging configuration
- response format validation

Security tests
--------------
Validate authentication and access control behavior.

Example matrix:

4 entities
× 4 HTTP methods
× 3 invalid credential cases
= 48 security tests

Performance tests
-----------------
Provide lightweight baseline response time checks to detect regressions
in API responsiveness.

------------------------------------------------------------------
