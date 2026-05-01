# 🧭 Environment & Configuration Guide

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
   ↓
plugins/_config.py
   ↓
framework behavior
```

**You do not access configuration programmatically via helper functions.**

---

## 3️⃣ Programmatic Access (Correct Way)

### ❌ What you should NOT do anymore

These patterns are **invalid** and **intentionally unsupported**:

- `get_config()`
- `get_config(reload=True)`
- `from config_pytest import STRICT_ENTITY_DISCOVERY`

> **There is no public config accessor API.**

### ✅ Correct access pattern

- **Plugins** import resolved constants directly from `_config.py`
- **Tests** rely on fixtures and plugin behavior

**Example (plugin code):**

```python
from EcommerceAPI.plugins._config import FAIL_ON_EMPTY_LIST

if FAIL_ON_EMPTY_LIST:
    ...
```

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

---

## 5️⃣ Runtime Metadata vs Configuration (Common Confusion)

| Type | Example | Where it lives |
|------|---------|----------------|
| Configuration | `FAIL_ON_EMPTY_LIST` | `_config.py` |
| Runtime metadata | session id | runtime metadata module |
| Logging context | nodeid | `log_context.py` |

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

**All of that belongs in `_config.py`.**

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

### Resolution Flow

```
pytest
   ↓
api_base_url fixture
   ↓
API_ENV (or ENV fallback)
   ↓
config_<service>.py
   ↓
API_HOSTS[env]
   ↓
Final base URL
```

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
ENV=test
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

## 8️⃣ CI Usage (Recap)

1. **CI supplies environment variables**
2. **`_config.py` resolves them once**
3. **Plugins consume resolved values**
4. **Logs show what was used**

> **There is no dynamic override mid-run.**

---

## 9️⃣ Troubleshooting Checklist

| Issue | Solution |
|-------|----------|
| Setting ignored? | Check startup banner |
| Behavior differs locally vs CI? | Compare startup banners |
| Want different behavior? | Change env var **before** pytest starts |

---

## 🔟 Final Reminder

> **Configuration is static and declarative.**
> **Runtime state is dynamic and contextual.**

**Mixing them causes bugs — the framework prevents that by design.**

---

✨ **Follow the contract. Respect the boundaries.**
