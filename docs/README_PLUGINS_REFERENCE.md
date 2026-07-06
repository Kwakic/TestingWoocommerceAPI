# Pytest Plugins Reference — EcommerceAPI Test Framework

This document is the **authoritative contract** for plugin behavior, ownership, and boundaries.

If this document conflicts with any README or comment, **this document wins**.

---

## Core Principles

1. Plugins are isolated units
2. Plugins must never import each other
3. Configuration is resolved once
4. Runtime metadata is separate from config
5. Logging context is per‑test and ephemeral

---

## Architecture Layers

```
┌─────────────────────────────┐
│ Environment / CI / CLI      │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ config_pytest.py            │  ← config resolution
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ src/configs/runtime_*       │  ← session metadata
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ plugins/*                   │  ← consumers only
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ tests                        │
└─────────────────────────────┘
```

---

## Plugin Contracts

### logging_plugin.py

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

### config_pytest.py

**Responsibilities**
- Read environment variables
- Normalize values
- Apply defaults
- Enforce consistency
- Emit startup banner
- Cache immutable FrameworkConfig

This is the **only place** allowed to read env vars.

---

### allure_autogen.py

**Responsibilities**
- Allure lifecycle management
- Environment metadata generation
- CI links and run summary
- Optional HTML generation

**Guarantees**
- Never fails pytest
- Safe in CI and local runs

---

## Forbidden Patterns (Hard Rules)

❌ Plugin importing plugin

❌ Plugin calling os.getenv

❌ Shared mutable globals in plugins

❌ Config duplicated outside config_pytest

❌ Runtime state hidden in logging

---

## Why This Matters

Breaking these rules causes:
- Pytest rewrite warnings
- Missing banners
- Broken correlation IDs
- Circular imports
- Non‑deterministic CI runs

This architecture exists to prevent exactly those failures.

---

## Final Rule

If you are unsure where something belongs:

- Is it a **decision**? → config_pytest
- Is it **identity / metadata**? → src/configs
- Is it **per‑test context**? → ContextVars
- Is it **behavior**? → plugin
- Is it **reusable logic**? → src/utilities

Do not guess. Follow the contract.
