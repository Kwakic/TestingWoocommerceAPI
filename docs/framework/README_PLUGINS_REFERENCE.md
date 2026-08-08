# Pytest Plugins Reference — EcommerceAPI Test Framework

This document is the **authoritative contract** for plugin behavior, ownership, and boundaries.

If this document conflicts with any README or comment, **this document wins**.

---

# 🎯 Core Principles

1. Plugins are isolated units
2. Plugins must never import each other
3. Configuration is resolved once
4. Runtime metadata is separate from config
5. Logging context is per‑test and ephemeral

---

# 🏛️ Architecture Layers

```
┌─────────────────────────────┐
Environment / CI / CLI
            │
            ▼
     config_pytest.py
            │
            ▼
      runtime_config
            │
            ▼
   ┌─────────────────────────────┐
   │     Framework Plugins       │
   │                             │
   │ logging_plugin              │
   │ allure_autogen              │
   │ reporting                   │
   │ entity_metadata             │
   │ entities                    │
   │ api/shared                  │
   │ api/<entity>                │
   │ db_fixtures                 │
   └─────────────────────────────┘
            │
            ▼
          pytest
```

---

# 📋 Plugin Contracts

## logging_plugin.py

**Responsibilities**
- Configure logging
- Install LogRecord factory
- Apply redaction and formatting
- Inject ContextVar‑based metadata
- Attach GLOBAL logging metadata

**Forbidden**
- Parsing env vars
- Defining config flags
- Importing other plugins

**Allowed imports**
- src.utilities.*
- src.configs.runtime_*

---

## config_pytest.py

**Responsibilities**
- Read environment variables
- Normalize values
- Apply defaults
- Enforce consistency
- Emit startup banner
- Cache immutable FrameworkConfig

This is the **only place** allowed to read env vars.

---

## allure_autogen.py

**Responsibilities**
- Allure lifecycle management
- Environment metadata generation
- CI links and run summary
- Optional HTML generation

**Guarantees**
- Never fails pytest
- Safe in CI and local runs

---

## api/shared.py

**Responsibilities**

- Provide the shared `api_client` fixture.
- Create framework-level HTTP infrastructure.
- Expose common API utilities used by entity plugins.
- Perform session-level environment validation (fail-fast gate)

**Forbidden**

- Entity-specific fixtures.
- Business logic.
- Reading environment variables.

### 🚨 Environment Gate Rule

The shared `api_client` fixture is responsible for validating:

- API connectivity
- Authentication correctness
- Environment configuration

This validation must:

- Run once per session
- Terminate execution on failure (`pytest.exit`)
- Produce a clear, non-test failure message

This prevents cascading failures across all tests.

---

## api/<entity>.py

**Responsibilities**

- Register entity-specific pytest fixtures.
- Create valid test data factories.
- Expose helpers for the owning business domain.

Examples:

- customers.py
- orders.py
- products.py
- coupons.py

**Forbidden**

- HTTP implementation.
- Runtime configuration.
- Cross-entity imports.

---

## entities.py

**Responsibilities**

- Build the runtime entity registry.
- Discover implemented runtime resources.
- Create EntityBundle objects.
- Provide unified access to helpers, APIs and DAOs.

See:

README_ENTITY_DISCOVER_ARCHITECTURE_GUIDE.md

---

## entity_metadata.py

**Responsibilities**

- Define the framework's architectural entity registry.
- Provide metadata used by CI, documentation and reporting.
- Act as the single source of truth for supported business domains.

This module defines framework architecture rather than runtime resources.

---

## reporting.py

**Responsibilities**

- Collect execution metadata.
- Build report summaries.
- Integrate with Allure and CI reporting.

This plugin consumes runtime metadata but does not perform test execution.

---

## db_fixtures.py

**Responsibilities**

- Register shared database fixtures.
- Provide reusable DAO access.
- Support integration and cleanup workflows.

Database fixtures must remain infrastructure-focused and contain no business logic.


---

# 🚫 Forbidden Patterns (Hard Rules)

❌ Plugin importing plugin

❌ Plugin calling os.getenv

❌ Shared mutable globals in plugins

❌ Config duplicated outside config_pytest

❌ Runtime state hidden in logging

---

# 💡 Why This Matters

Breaking these rules causes:
- Pytest rewrite warnings
- Missing banners
- Broken correlation IDs
- Circular imports
- Non‑deterministic CI runs

This architecture exists to prevent exactly those failures.

---
# ⚠️ Important Note:

fixtures are not auto-discovered across arbitrary nested folders unless they’re exposed via conftest.py or registered
plugins.
So putting api_fixtures.py under tests/customers/plugins/ and expecting global availability will fail.


---

# 🏁 Final Rule

If you are unsure where something belongs:

- Is it a **decision**? → config_pytest
- Is it **identity / metadata**? → src/configs
- Is it **per‑test context**? → ContextVars
- Is it **behavior**? → plugin
- Is it **reusable logic**? → src/utilities

Do not guess. Follow the contract.
