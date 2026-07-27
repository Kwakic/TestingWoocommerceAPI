# 📘 Configuration Contract

**Authoritative and normative definition of configuration behavior in the EcommerceAPI test framework.**

This document defines **what** configuration is, **where** it lives, **who** owns it, and **how** it may be consumed.
If behavior is unclear, **this document wins**.

---

## 1️⃣ Purpose

This contract exists to guarantee:

- ✅ **Deterministic framework behavior**
- ✅ **Zero hidden environment coupling**
- ✅ **Predictable CI runs**
- ✅ **Strict ownership boundaries**
- ✅ **Safe refactoring without behavioral drift**

> **Configuration is not an implementation detail.**
> It is a **framework-level contract**.

---

## 2️⃣ Configuration Architecture (Current)

```
┌──────────────────────────────┐
│ User / CI / OS               │
│ (.env, CI variables, shell)  │
└──────────────┬───────────────┘
               ↓  (strings only)
┌──────────────────────────────┐
│ plugins/_config.py           │
│  - env parsing               │
│  - defaults                  │
│  - validation                │
│  - runtime metadata init     │
└──────────────┬───────────────┘
               ↓  (typed, frozen)
┌─────────────────────��────────┐
│ Runtime Plugins & Fixtures   │
│  - logging                   │
│  - allure                    │
│  - pytest hooks              │
└──────────────────────────────┘
```

### **Key rule**

> All environment variables are interpreted **exactly once** — in `plugins/_config.py`.

---

## 3️⃣ Ownership Model (Strict)

| Layer | Responsibility |
|-------|----------------|
| `.env` / CI | Declare intent only (values as strings) |
| OS / Runner | Provide variables |
| `_config.py` | Parse, normalize, validate, freeze |
| Plugins | Consume resolved values |
| Tests | **Never** read env vars directly |

---

## 4️⃣ The Single Source of Truth

`runtime_config.py` is the **single source of truth** for framework configuration.

Framework configuration values must:

- Read environment variables
- Parse and normalize values
- Apply defaults
- Validate configuration
- Produce an immutable runtime configuration object
- Provide a consistent view of framework settings for all plugins and utilities

If a value affects framework behavior:

> It **must** be defined, resolved, and exposed through `runtime_config.py`.

### Compatibility

During the migration to `API_ENV`, the framework continues to accept the legacy `ENV` variable for backward compatibility.

The active environment is resolved using:

```python
os.getenv("API_ENV") or os.getenv("ENV", "test")
```

This compatibility lookup exists only to support older configurations and **must not introduce new configuration semantics**.

New framework code should use `API_ENV`.

> It **must** appear in `_config.py`. **No exceptions.**

---

## 5️⃣ Forbidden Patterns (Hard Rules)

| ❌ **Not Allowed** |
|--------------------|
| Plugins reading environment variables |
| Tests calling `os.getenv()` |
| Helpers parsing env vars |
| Multiple defaults for the same flag |
| "Convenience" config accessors outside `_config.py` |

> **Violating these rules breaks determinism and CI parity.**

---

## 6️⃣ Supported Configuration Flags

*(unchanged list, but now explicitly frozen at startup)*

All flags are:

- ✅ Resolved **once** at session start
- ✅ **Immutable** for the duration of the run
- ✅ Logged in the startup banner

### **Example categories**

- **Test behavior** (`FAIL_ON_EMPTY_LIST`, `PERF_ITERATIONS`)
- **Logging** (`STRUCTURED_LOGS`, `LOG_DIR`, `KEEP_STRUCTURED_LOGS`)
- **Reporting** (`AUTO_ALLURE_REPORT`)
- **Safety** (`REQUIRE_ENV`)

---

## 7️⃣ Runtime Metadata (Important Distinction)

The framework distinguishes between:

### **Configuration**
- 🔒 Static
- 🌍 Env-driven
- ❄️ Frozen at startup
- 📂 Lives in `_config.py`

### **Runtime metadata**
- ⚡ Dynamic
- 🏃 Session-scoped
- 📦 Lives in dedicated runtime modules

**Examples:**
- Session ID
- CI metadata
- Git metadata

> These are **not** configuration flags and must **not** be treated as such.

---

## 8️⃣ Logging Context Is Not Configuration

Contextual logging values (node id, correlation id):

- ✅ Are **runtime context**
- ✅ Are **dynamic**
- ❌ Must **NOT** be defined in `_config.py`
- ❌ Must **NOT** read env vars

They live in `utilities/log_context.py` and are populated by:

- pytest hooks
- runtime plugins

---

## 9️⃣ Guarantees Provided by This Contract

By following this contract, the framework guarantees:

- ✅ Identical behavior locally and in CI
- ✅ Visible startup configuration
- ✅ No hidden env coupling
- ✅ Safe refactors
- ✅ Predictable onboarding

---

## 🔟 Final Principle (Non-Negotiable)

> **If a value affects framework behavior,
> it must be defined, parsed, and logged in `_config.py`.**

**Everything else is runtime state.**

---

✨ **This is the contract. Follow it religiously.**
