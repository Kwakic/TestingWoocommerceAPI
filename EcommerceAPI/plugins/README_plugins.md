# Pytest Plugins Overview — EcommerceAPI Test Framework

This document gives a **high‑level overview** of the pytest plugins shipped with the EcommerceAPI test framework.

It is intentionally **not exhaustive**.  
Authoritative rules and contracts live in **PLUGINS_REFERENCE.md**.

---

## What a Plugin Is (in this framework)

A plugin is a Python module that:
- Is imported **once** by pytest
- Registers hooks, fixtures, or startup behavior
- Does **not** import any other plugin
- May depend on **runtime config or utilities**, never other plugins

All shared plugins live under:

```
EcommerceAPI/plugins/
```

They are loaded explicitly via `pytest_plugins` in the root `conftest.py`.

---

## Plugin Load Order (Critical)

```python
pytest_plugins = [
    "EcommerceAPI.plugins.logging_plugin",   # MUST load first
    "EcommerceAPI.plugins.config_pytest",
    "EcommerceAPI.plugins.runtime_context_pytest",
    "EcommerceAPI.plugins.reporting",
    "EcommerceAPI.plugins.allure_autogen",
    "EcommerceAPI.plugins.entities",
    "EcommerceAPI.plugins.db_fixtures",
    "EcommerceAPI.plugins.api_fixtures",
]
```

Why order matters:
- Logging installs the LogRecord factory
- Config must resolve before runtime metadata is attached
- Reporting and Allure depend on both

Do **not** reorder casually.

---

## Plugin Responsibilities (Summary)

### logging_plugin.py
- Configure logging and handlers
- Install LogRecord factory
- Inject nodeid and correlation_id via ContextVars
- Apply redaction and emoji rules
- Attach GLOBAL logging metadata **from runtime configs**

❌ Must not define config  
❌ Must not read env directly  
❌ Must not be imported by other plugins

---

### config_pytest.py
- Resolve environment variables
- Normalize values (bools, ints, paths)
- Create immutable FrameworkConfig
- Emit startup configuration banner
- Expose `get_config()` and `framework_config` fixture

✅ Single source of truth for framework behavior

---

### allure_autogen.py
- Manage Allure results directory lifecycle
- Generate environment.properties
- Attach run summary and CI links
- Optionally generate HTML report

Allure is best‑effort and must never fail pytest.

---

### reporting.py
- Test‑level reporting hooks
- Attach logs to Allure on failure
- Add labels (team, env, service)

---

### entities.py
- Entity discovery
- Resource tracking
- Best‑effort cleanup

---

### api_fixtures.py / db_fixtures.py
- High‑level fixtures for tests
- No discovery, no config parsing

---

## Golden Rules

- Plugins must NOT import other plugins
- Shared state lives in runtime/config modules
- Plugins consume — never define — config
- All env access goes through config_pytest

---

If you need exact contracts and forbidden patterns → see **PLUGINS_REFERENCE.md**
