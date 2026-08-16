# 🚀 Developer Onboarding — TestEcommerceAPI

Quick guide to set up a developer environment, run tests locally, and contribute.

> Recommended canonical file: keep this as the single onboarding doc and remove duplicate DEV_SETUP.md.

---

## 📋Prerequisites
- Python 3.13+
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

## 🚀 Quick Setup — One-Command Setup

Make sure **Docker Desktop** is running first.

Then clone the repository and bootstrap the complete test environment:

```bash
git clone https://github.com/Kwakic/TestingWoocommerceAPI.git && cd TestingWoocommerceAPI && make run
```

👉 **That's it — no manual Python or virtual-environment setup is required.**

---

### 🚀 How `make run` Works

`make run` is the single-command bootstrap for the complete local test
environment.

On the first run, it automatically:

- 📁 Creates `.env` from `.env.example` when needed
- 🐍 Creates the project-local `.venv` if it does not exist
- 🔍 Verifies that the Python interpreter used by `.venv` is **Python 3.13+**
- 📦 Installs `EcommerceAPI[dev]` into the project-local `.venv`
- 🐳 Starts the Docker infrastructure
- 🌐 Installs WordPress
- 🛒 Installs WooCommerce
- 🔑 Generates WooCommerce REST API credentials
- ⚙️ Configures the local test environment
- 🧪 Runs the test suite

---

### 🔁 Re-running `make run`

`make run` is designed to be idempotent. When run again in the same project
environment, it:

- ♻️ Reuses the existing `.venv` when it is valid
- 🐳 Reuses the existing Docker environment
- ⏭️ Skips already-installed components where applicable
- 🚫 Avoids creating duplicate data
- 💾 Preserves the existing database
- 🔑 Regenerates WooCommerce REST API credentials only when a fresh
  WordPress installation is created
- 🧪 Runs the test suite again using the project-local `.venv`
- 🔄 Refreshes credentials when a fresh WordPress installation requires them

> **💡 No manual virtual-environment activation is required.**
>
> `make run` invokes the project's `.venv` directly. Manual activation is only
> needed if you want to run `python`, `pytest`, or other Python commands
> directly from your terminal.

If an existing `.venv` was created with an unsupported Python version, `make run`
fails with an explicit version error rather than silently continuing.

---

### 🧑‍💻 Manual virtual-environment activation — optional

You only need to activate `.venv` if you want to run `python`, `pytest`, or
other Python commands directly from your shell rather than through `make`.

**Git Bash on Windows:**

```bash
source .venv/Scripts/activate
```

**PowerShell:**

```powershell
.\.venv\Scripts\Activate.ps1
```

**Windows Command Prompt:**

```cmd
.venv\Scripts\activate.bat
```

**macOS / Linux:**

```bash
source .venv/bin/activate
```

After activation, direct commands such as:

```bash
python --version
pytest -q
```

use the project-local environment.

### 🛠️ Manual setup — framework development only

Manual setup is useful when you need to configure the Python environment before
running Make targets, or when working on the framework itself.

Create the environment with Python 3.13+:

```bash
python -m venv .venv
```

Activate it using the command for your shell shown above, then install the
framework and development dependencies:

```bash
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e "./EcommerceAPI[dev]"
```

Verify the editable installation:

```bash
python -c "import EcommerceAPI; print(getattr(EcommerceAPI, '__file__', 'NOT IMPORTABLE'))"
```

Expected: a path inside your repository.

> ⚠️ **Do not use a Python `sys.path` hack as a substitute for installing the
> framework.** Use the editable installation shown above.

## 🌎 Environment Configuration

For local development, simply run:

```bash
make run
```

The bootstrap process automatically:

- creates `.env` from `.env.example` (if needed)
- starts Docker
- installs WordPress
- installs WooCommerce
- generates REST API credentials
- writes `WC_KEY` and `WC_SECRET` into `.env`
- creates (or reuses) a project-local `.venv` and installs the framework + dev dependencies into it

Developers should not manually edit endpoint URLs.

Environment selection is controlled by:

```
API_ENV
```

Entity configuration files resolve the correct API endpoint dynamically.

For details see:

docs/framework/README_ENVIRONMENT_CONFIG_GUIDE.md


---

## 🧭 Local Development Environment

For normal local development, pytest runs on the host against the
Dockerized WordPress + WooCommerce environment.

The local Docker environment uses:

```text
API_ENV=test
```

With `API_ENV=test:`

* pytest runs on the host
* WordPress + WooCommerce run in Docker
* the framework resolves the API endpoint for the Dockerized environment

This is the recommended setup for local framework development.

Use `make run `to provision the complete local Docker environment. It:

* creates .env if needed
* starts Docker
* provisions WordPress and WooCommerce
* generates WooCommerce API credentials
* updates WC_KEY and WC_SECRET
* runs the test suite

>Important: .env contains environment-specific credentials anddatabase settings. Do not reuse credentials or database configurationfrom one environment against another.

For environment resolution details, see:

[Environment & Config Guide](./docs/framework/README_ENVIRONMENT_CONFIG_GUIDE.md)





---


## 💡 IDE setup (avoid two different environments)

`make run` / `make install` create and use a single project-local `.venv` at
the repo root. Point your IDE at that **same** interpreter, or it can end up
running a different Python than your terminal — same packages installed in
one, missing in the other, with no obvious reason why.

- **PyCharm:** *Settings → Project → Python Interpreter → Add → Existing
  environment* → select `.venv/Scripts/python.exe` (Windows) or
  `.venv/bin/python` (macOS/Linux)
- **VS Code:** Command Palette → *Python: Select Interpreter* → choose the
  one listed under `.venv`

If you ever see an IDE error like `No module named 'requests'` while the
same import works fine from your terminal, this mismatch is almost always
the cause — check which interpreter the IDE is actually using before
suspecting a missing dependency.

---

## ⚡ Running tests (recommended commands)

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

### ⚛️ GraphQL tests

GraphQL tests use the same Dockerized WordPress/WooCommerce environment
as the rest of the API test suite.

Run the Product GraphQL suite with:

```bash
pytest tests/products/graphql/ -v
```

Run GraphQL contract tests with:

```bash
pytest -m "graphql and contract" -v
```
For GraphQL architecture, authentication and test development, see:

[GraphQL Testing Guide](./docs/development/README_GRAPHQL_TESTING_GUIDE.md)

---

## 🩺Troubleshooting: “0 tests collected”
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

## 🐳 Running with Docker

For most developers, the Makefile provides the recommended interface.

### Start the local environment

```bash
make run
```

This command automatically:

- Creates `.env` (if required)
- Starts Docker
- Provisions WordPress
- Installs WooCommerce
- Generates REST API credentials
- Creates (or reuses) `.venv` and installs the Python framework into it
- Prepares the local test environment


> **⚠️ Running multiple local environments**
>
> `make run` is idempotent when used with the same project environment, so `make down` is **not required before every `make run`**.
>
> However, the Docker environment uses fixed host ports. If you have another TestEcommerceAPI checkout running on the same machine (for example, a development checkout and a separate clean/public checkout), stop the other environment first:
>
> ```bash
> make down
> ```
>
> Then run `make run` from the environment you want to use.
>
> This prevents port conflicts and ensures that Docker commands are operating on the intended project environment.



### Execute the test suite

```bash
make test
```

### Stop the environment

```bash
make down
```

---

### Advanced Docker usage

Direct Docker Compose commands remain available for advanced
development, debugging, or CI troubleshooting.

For example:

```bash
docker compose -f docker-compose.matrix.yml build

docker compose -f docker-compose.matrix.yml \
    --profile customers up \
    --abort-on-container-exit \
    --remove-orphans
```

These commands are primarily intended for framework development and
pipeline debugging rather than day-to-day testing.

---

## CI notes (summary)
- GitHub Actions and GitLab dynamic pipelines should install dev extras:
```bash
python -m pip install -e './EcommerceAPI[dev]'
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

------------------------------------------------------------------
# 🧪 Shared Test Suites (Framework-Level Tests)

The framework also contains shared tests that validate infrastructure,
security, and environment behavior before running entity-specific tests.

Directory structure:

```
tests/shared/
    preflight/
        test_logging_globals.py
    security/
        test_authentication_matrix.py
        test_authentication_success.py
    contracts/
           rest/
              test_api_connectivity.py
              test_response_format.py
           graphql/
              test_graphql_connectivity.py
              test_product_mutation_schema.py
```


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

Contract tests
-----------------
Validate the API contracts exposed by the framework.

Contract tests are organized by API protocol:

```
tests/shared/contracts/
├── rest/
│   ├── error_schema.py
│   ├── test_response_format.py
│   └── test_api_connectivity.py
└── graphql/
    ├── test_graphql_connectivity.py
    └── test_product_mutation_schema.py
```

REST contract tests validate the HTTP/REST response contract, including
response format, connectivity, and error structure.

GraphQL contract tests validate the GraphQL transport and schema contract,
including endpoint connectivity and the schema required by GraphQL operations.

Contract tests are framework-level tests. They do not belong to a specific
business entity and are executed separately from entity-specific API tests.

When adding a new API protocol, its contract tests should be placed under
the corresponding protocol directory.

------------------------------------------------------------------
