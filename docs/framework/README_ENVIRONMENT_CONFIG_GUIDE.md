# 🧭 Environment & Configuration Guide

>Teach developers how the configuration system works.

### "How does configuration work?"

**Practical guide for developers, QA, and CI users.**
For authoritative rules, see `CONFIG_CONTRACT.md`.

---

## 1️⃣ What This Guide Is (and Is Not)

### ✅ This guide explains:

- How to set environment variables
- How configuration is resolved
- How to debug config issues
- How CI should supply values

### ❌ This guide does not define rules or ownership.

---

## 2️⃣ Where Configuration Comes From

Configuration always follows this path:

```
.env / CI / shell
        │
        ▼
runtime_config.py
        │
        ▼
config_loader.py
        │
        ├── APIClient
        ├── Logging
        ├── Plugins
        └── Tests
```

**You do not access configuration programmatically via helper functions.**

---

## 📑 Configuration Responsibilities

`runtime_config.py`
    Owns framework runtime configuration.

`config_loader.py`
    Resolves entity configuration.

`config_<entity>.py`
    Stores public API endpoint mappings.

`.env`
    Stores secrets and environment-specific values.

`runtime_metadata.py`
    Stores runtime session information.

`log_context.py`
    Stores per-test logging context.

`config_graphql.py`
    Stores the GraphQL endpoint configuration used by the shared `graphql_client` fixture.
    GraphQL has a single endpoint rather than one endpoint per REST entity, its configuration is
maintained separately from `config_<entity>.py`.
---

## 3️⃣ Programmatic Access (Correct Way)

### ❌ What you should NOT do anymore

These patterns are **invalid** and **intentionally unsupported**:

- `get_config()`
- `get_config(reload=True)`
- `from config_pytest import STRICT_ENTITY_DISCOVERY`

> **There is no public config accessor API.**

### ✅ Correct access pattern

- **Plugins** import resolved constants directly from `runtime_config.py`
- **Tests** rely on fixtures and plugin behavior

**Example (plugin code):**

Plugins should use the framework configuration APIs or helper functions
provided by the framework rather than reading environment variables
directly.

Tests should rely on fixtures and plugin behaviour rather than accessing
configuration themselves.

**There is no reload.**
**There is no mutation.**
**Configuration is frozen at startup.**

---

## 4️⃣ How to Inspect Configuration (Debugging)

### Recommended ways

#### A. Startup banner (authoritative)

At pytest startup, the framework logs:

```
================= FRAMEWORK CONFIG =================
FAIL_ON_EMPTY_LIST      : False
PERF_ITERATIONS         : 5
AUTO_ALLURE_REPORT      : True
STRUCTURED_LOGS         : True
LOG_DIR                 : reports/logs
KEEP_STRUCTURED_LOGS    : 3
===================================================
```

**This is the actual configuration used.**

#### B. Environment echo (shell-level)

```bash
echo $FAIL_ON_EMPTY_LIST
```

Only useful to verify the shell, **not** framework behavior.

```
Framework configuration
Environment information
Session ID
Logging configuration
```

If the banner differs from your expectation, the problem is almost always in the environment variables supplied before pytest started.

---

## 5️⃣ Runtime Metadata vs Configuration (Common Confusion)


| Type | Owner |
| :--- | :--- |
| Runtime configuration | runtime_config.py |
| Service configuration | config_loader.py + config_\.py |
| Runtime metadata | runtime_metadata.py |
| Logging context | log_context.py |


> **If it changes during execution → not config.**

---

## 6️⃣ The `configs/` Folder (Important)

### What it is allowed to contain

The `configs/` folder may contain:

- Static, non-runtime configuration data
- Public mappings
- Environment-agnostic constants

**Examples:**

- Host mappings
- Endpoint maps
- Service names
- Non-sensitive defaults

### What it must NEVER contain

| ❌ **Not Allowed** |
|--------------------|
| Environment variable parsing |
| Calls to `os.getenv` |
| Runtime metadata |
| Session ids |
| CI detection logic |
| Behavior flags |

**All of that belongs in `runtime_config.py`.**


Only contains:

- API_HOSTS
- endpoint mappings
- public constants

> Environment variable parsing belongs in runtime_config.py, not in entity configuration files.

---

## 7️⃣ 🌐 API Base URL Resolution (Environment-Driven)

The framework does **not hardcode API URLs**.
Instead, it dynamically resolves them at runtime based on environment configuration.

This is a **critical design decision** to support multiple execution contexts:
- local development
- Docker environments
- CI pipelines

---

## 🔍 How the Base URL is Built

The base URL is resolved through a **pytest fixture**:

From `conftest.py`:

```python
env = os.getenv("API_ENV") or os.getenv("ENV", "test")
...
return module.API_HOSTS[env]
```
---

### 🌐 GraphQL Endpoint

GraphQL endpoint resolution follows the same environment-selection
principle as REST but uses dedicated GraphQL configuration.

```text
API_ENV
   ↓
config_graphql.py
   ↓
graphql_client fixture
   ↓
GraphQLClient
```
GraphQL endpoint configuration is infrastructure configuration and must
not be hardcoded in individual GraphQL tests.

---

### 🔄 Complete Base URL Resolution Flow

The framework resolves the API base URL dynamically at runtime.

When a test creates an API client, the following sequence occurs:

```text
pytest
    │
    ▼
runtime_config.py
    │
    ▼
config_loader.py
    │
    ▼
detect_service()
    │
    ▼
load_service_config()
    │
    ▼
API_HOSTS[API_ENV]
    │
    ▼
APIClient(base_url)
```
---
### ➕ Adding a New Environment

Adding a new execution environment requires only two steps.

### Step 1 — Select the environment

Set the desired environment before running pytest.

Example:

```bash
API_ENV=qa
```

### Step 2 — Register the environment for the entity

Each entity owns its own environment mapping under its `configs/` directory.

Examples:

```text
tests/
├── customers/
│   └── configs/
│       └── config_customers.py
├── products/
│   └── configs/
│       └── config_products.py
├── orders/
│   └── configs/
│       └── config_orders.py
└── coupons/
    └── configs/
        └── config_coupons.py
```

Add the new environment to the appropriate `API_HOSTS` dictionary.

Example (`tests/products/configs/config_products.py`):

```python
API_HOSTS = {
    ...
    "qa": "https://qa.example.com/wp-json/wc/v3/",
}
```

If multiple entities expose the same environment, add the mapping to each entity's configuration file.

No changes are required in:

- APIClient
- HttpClient
- API classes
- Helpers
- Tests

The framework automatically imports the correct `config_<entity>.py` module, looks up `API_HOSTS[API_ENV]`, and passes the resolved base URL to `APIClient`.

> **CI note**
>
> If the new environment will also be used in automated pipelines, update the
> CI environment configuration accordingly.
>
> For GitHub Actions in this project, the execution environment is configured
> by the reusable `configure-ci-env` composite action located at:
>
> ```text
> .github/
> └── actions/
>     └── configure-ci-env/
>         └── action.yml
> ```
>
> All workflows consume this shared action, ensuring a consistent
> `API_ENV` configuration across Smoke, Integration, Regression,
> Performance, Contract, Security and Preflight workflows.
>
> The reusable configure-ci-env composite action is the single place where GitHub Actions sets framework-specific environment variables such as API_ENV. All workflows reuse this action to ensure consistent configuration.
>
> See **README_CI_ARCHITECTURE.md** for the complete CI workflow design.

---

## 🧩 Environment → URL Mapping

Each service defines its own environment mapping.

Example (`config_customers.py`):

```python
API_HOSTS = {
    "test": "http://localhost:8888/kwakiweb/wp-json/wc/v3/",
    "docker": "http://wordpress/wp-json/wc/v3/",
    "local": "http://localhost:8888/kwakiweb/wp-json/wc/v3/",
    "dev": "http://host.docker.internal:8888/kwakiweb/wp-json/wc/v3/",
    "staging": "https://staging.example.com/wp-json/wc/v3/",
    "prod": "https://api.example.com/wp-json/wc/v3/",
    "ci": "http://localhost:8080/wp-json/wc/v3/",
}
```

> Each entity owns its own `config_<entity>.py` file, allowing services to evolve independently while using the same configuration load

---

## ⚠️ Important: Environment ≠ Infrastructure

A key concept:

> **Environment variables do not define infrastructure — they select a network topology.**

Different environments require different host resolution:

| Environment | Where tests run | How WordPress is reached |
|------------|----------------|--------------------------|
| `test`     | Host machine   | `localhost:8888`         |
| `docker`   | Inside Docker  | `wordpress` (Docker DNS) |
| `ci`       | Host (CI runner) + Docker containers | `localhost:8080` |

---

## 💥 Common Pitfall (CI Failure)

If CI runs with:

```bash
API_ENV=test
```

Then the framework resolves:

```
http://localhost:8888/kwakiweb/wp-json/wc/v3/
```

❌ This fails in CI because:
- CI is not running your local WordPress on port 8888

---

## ✅ Correct CI Configuration

You must explicitly select the correct environment:

```bash
API_ENV=ci
```

Example (GitHub Actions):

```yaml
- name: Configure environment (CI overrides)
  run: |
    echo "API_ENV=ci" >> $GITHUB_ENV
```

---

## 🧠 Why Not Use `docker` in CI?

```
docker → http://wordpress/
```

✔ Works only if:
- tests run **inside Docker network**

❌ In your setup:
- pytest runs on **host**
- containers run separately

➡️ `wordpress` hostname is **not resolvable**

---

## 🎯 Final Design (Correct and Clean)

You now have **three distinct execution modes**:

| Mode    | API_ENV | URL |
|--------|--------|-----|
| Local dev | `test` | localhost:8888 |
| Docker-native | `docker` | wordpress |
| CI pipeline | `ci` | localhost:8080 |

✔ No hacks
✔ No hardcoded overrides
✔ Fully configurable
✔ Matches real infrastructure

---

## 🧠 Design Principles Applied

- **Configuration-driven behavior**
- **Environment abstraction**
- **Separation of concerns**
- **Infrastructure-aware design**

---

## 🚀 Key Takeaway

> The framework does not “know” where the API is.
> It **resolves it dynamically based on execution context**.

This makes the system:
- portable
- CI-friendly
- Docker-compatible
- production-ready

---

## 8️⃣ `.env` Best Practices

- ✅ Use `.env.example` (tracked)
- ✅ Never commit real secrets
- ✅ All values are strings
- ✅ Booleans use: `1` / `true` / `yes` / `on`

**Example:**

```bash
FAIL_ON_EMPTY_LIST=false
PERF_ITERATIONS=5
AUTO_ALLURE_REPORT=true
```

---

## 9️⃣ REQUIRE_ENV strict mode

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

## 🔟  CI Usage (Recap)

1. **CI supplies environment variables**
2. **`runtime_config.py` resolves them once**
3. **Plugins consume resolved values**
4. **Logs show what was used**

> **There is no dynamic override mid-run.**

---

## 1️⃣️1️⃣Troubleshooting Checklist

| Issue | Solution |
|-------|----------|
| Setting ignored? | Check startup banner |
| Behavior differs locally vs CI? | Compare startup banners |
| Want different behavior? | Change env var **before** pytest starts |

---

## 1️⃣2️⃣. Final Reminder

Framework configuration is resolved once during startup.

After startup:

✔ Configuration remains immutable.

✔ Runtime metadata evolves during execution.

✔ Logging context changes per test.

Keeping these concerns separate makes the framework predictable,
testable and easy to maintain.
---

##  ⚖️ Single Source of Truth

`runtime_config.py`
    Framework runtime configuration

`config_loader.py`
    Service configuration

`config_<entity>.py`
    Public endpoint mappings

Everything else consumes these components rather than
reading environment variables directly.

---

# 🖥️ Windows (Git Bash) Notes

When running the Docker-based WooCommerce environment from **Git Bash on Windows**, Git Bash automatically rewrites Unix-style paths before invoking Docker.

For example:

`/var/www/html`

may become:

`C:/Program Files/Git/var/www/html`

This causes WP-CLI commands executed inside Docker containers to fail with messages such as:

`Error: This does not seem to be a WordPress installation.`

The framework automatically disables Git Bash path conversion by setting:

`MSYS_NO_PATHCONV=1`

before executing Docker Compose commands.

This setting has no effect on Linux, macOS or GitHub Actions but ensures consistent behaviour for Windows developers.

---

✨ **Follow the contract. Respect the boundaries.**
