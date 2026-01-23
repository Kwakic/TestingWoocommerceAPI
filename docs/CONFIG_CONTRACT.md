# 📘 Test Framework Configuration Contract

Authoritative definition of how configuration works in the EcommerceAPI test framework.

---

## 1️⃣ Purpose

This document defines:

- **how configuration is provided**
- **where it is parsed**
- **how precedence is resolved**
- **what plugins may and may not do**
- **which configuration flags are supported**
- **how teams are expected to consume them**

This contract ensures:

- ✅ deterministic behavior  
- ✅ consistent CI execution  
- ✅ no hidden environment coupling  
- ✅ predictable onboarding

---

## 2️⃣ Configuration Architecture Overview

Configuration flows through the framework in four layers:

```
┌────────────────────────────┐
│ User / CI / Local machine │
│   (.env, GitHub Actions)  │
└──────────────┬─────────────┘
               ↓
┌────────────────────────────┐
│ Environment Variables      │
│   (always strings)         │
└──────────────┬─────────────┘
               ↓
┌────────────────────────────┐
│ Framework Config Resolver  │
│   plugins/_config.py       │
└──────────────┬─────────────┘
               ↓
┌────────────────────────────┐
│ Runtime Plugins & Fixtures │
└────────────────────────────┘
```

- Environment variables are always strings.
- All parsing, normalization and validation happens in `plugins/_config.py`.
- Plugins and tests consume resolved config values — not raw environment variables.

---

## 3️⃣ Configuration Ownership Model

- **.env** — Express intent only (do not implement logic here)  
- **OS / CI** — Supply environment variables  
- **_config.py** — Interpret, normalize, validate, log  
- **Plugins** — Consume resolved config constants from `_config.py`  
- **Tests** — Never read environment variables directly

---

## 4️⃣ Rules (Strict)

**✅ Allowed**

- `.env` contains only values (no parsing).
- `_config.py` parses environment variables.
- Plugins import config constants from `_config.py`.
- Startup banner logs the resolved config (shown once).

**❌ Forbidden**

- Plugins calling `os.getenv(...)` directly.
- Tests reading environment variables.
- Helpers parsing env vars directly.
- Duplicate defaults spread across plugins.

All environment access MUST go through `plugins/_config.py`.

---

## 5️⃣ Configuration Precedence

When the same setting exists in multiple places, precedence is:

1. CLI options (highest)
2. Environment variables (`.env` / CI)
3. Framework defaults (lowest)

Example:

- CLI: `pytest --fail-on-empty-list`  (wins)
- Env: `FAIL_ON_EMPTY_LIST=false`  (overrides default)
- Default: whatever `_config.py` sets

---

## 6️⃣ Boolean Parsing Contract

Environment variables are strings. Use the unified parser:

```python
env_bool("FLAG_NAME", default=False)
```

Truthy values (case-insensitive):

- `1`
- `true`
- `yes`
- `on`

Everything else → interpreted as `False`.

This keeps behavior consistent across Linux, Windows, Docker, and CI.

---

## 7️⃣ Supported Configuration Flags

Below are the supported flags, defaults, and short descriptions.

### 🔐 Entity Discovery
| Variable | Default | Description |
|---|---:|---|
| `STRICT_ENTITY_DISCOVERY` | `false` | Fail-fast when entity helpers / DAOs are partially discovered |

### 🧪 Test Behavior
| Variable | Default | Description |
|---|---:|---|
| `FAIL_ON_EMPTY_LIST` | `false` | Fail schema tests if list endpoints return empty |
| `PERF_ITERATIONS` | `5` | Default iterations for performance tests |

### 📊 Logging
| Variable | Default | Description |
|---|---:|---|
| `ENABLE_STRUCTURED_LOGS` | `true` | Enable JSONL structured logs |
| `ENABLE_JSON_PRETTY` | `false` | Pretty-print structured logs |
| `KEEP_STRUCTURED_LOGS` | `3` | Number of retained structured log files |
| `LOG_PAYLOADS` | `false` | Include masked payloads in logs |
| `REDACT_SENSITIVE_FIELDS` | `true` | Mask secrets in logs |
| `DISABLE_LOG_EMOJIS` | `false` | Disable emoji output in logs |

### 📁 Reporting
| Variable | Default | Description |
|---|---:|---|
| `AUTO_ALLURE_REPORT` | `true` | Generate Allure HTML report automatically |

### 🧱 Environment Safety
| Variable | Default | Description |
|---|---:|---|
| `REQUIRE_ENV` | `false` | Fail startup if `.env` is missing |

---

## 8️⃣ Startup Configuration Banner

At pytest startup, the framework logs a single, authoritative snapshot:

```text
⚙️ ================== TEST FRAMEWORK CONFIG ==================
STRICT_ENTITY_DISCOVERY: False
FAIL_ON_EMPTY_LIST:      False
PERF_ITERATIONS:         5
AUTO_ALLURE_REPORT:      True

STRUCTURED_LOGS:         True
JSON_PRETTY:             False
LOG_PAYLOADS:            False
REDACT_SENSITIVE_FIELDS: True

LOG_DIR:                 reports/logs
KEEP_STRUCTURED_LOGS:    3
==============================================================
```

- Emitted once per session  
- Authoritative and immutable during execution  
- Helpful for CI debugging

---

## 9️⃣ Plugin Integration Contract

Plugins MUST import config values from `_config.py` and use them — never read the environment directly.

✅ Correct (import resolved value)
```python
from EcommerceAPI.plugins._config import STRICT_ENTITY_DISCOVERY

if STRICT_ENTITY_DISCOVERY:
    raise pytest.UsageError("strict discovery enabled")
```

❌ Incorrect (forbidden)
```python
# Bad: reading env in plugin
os.getenv("STRICT_ENTITY_DISCOVERY")
```

### 🔁 Example: Entity Discovery modes
- `STRICT_ENTITY_DISCOVERY=false` → Log warnings only (friendly locally)
- `STRICT_ENTITY_DISCOVERY=true` → Fail pytest collection (strict in CI)

---

## 🔐 Guarantees Provided by the Framework

- deterministic startup behavior  
- visible configuration state in logs  
- no hidden environment coupling  
- no per-plugin env parsing  
- reproducible CI runs

---

## 🧭 Guidance for Teams

- Test authors:
  - never read environment variables directly
  - never change framework config inside tests
  - rely on fixtures for needed behavior

- Framework maintainers:
  - add all new environment flags to `plugins/_config.py`
  - document new flags here in the README
  - include them in the startup banner

---

## 📌 Summary

Configuration is a contract, not an implementation detail. This framework enforces:

- single source of truth (`plugins/_config.py`)  
- explicit defaults  
- observable behavior (startup banner)  
- zero ambiguity

✅ Final Principle:  
If a value affects framework behavior, it must appear in `_config.py`. Nothing else is allowed.

---

Resources:
- Read more about pytest: [pytest docs](https://docs.pytest.org/)
- Allure reporting: [Allure docs](https://docs.qameta.io/allure/)
---
**Recap:**

.env            → configuration input (human + CI)

env_utils.py    → configuration parsing (string → typed)

_config.py      → configuration contract (framework truth)

plugins         → configuration consumers