## Overview
The **Preflight Test Suite** performs *framework-level and environment diagnostics*  
**before any environment-dependent or business-level tests are executed**.

Preflight is intentionally **lightweight and non-invasive**.  
It verifies that the **test framework itself** is correctly wired and that the
execution environment is sane — **not** that the deployed application behaves correctly.

> 🔑 **Important change**  
> API schema validation tests have been **moved out of preflight** and now live in the
> **Shared Contract Test Suite**. Preflight no longer requires a live application.

---

## ✅ Purpose

Preflight tests **do not test APIs or business logic**.

They validate:
- 🧠 Logging configuration and global metadata wiring
- 🔗 Correlation ID and nodeid propagation
- 🧾 Structured logging availability and safety
- ⚙️ Pytest configuration, markers, and CLI flags
- 🧪 Framework health checks that must pass everywhere (local & CI)

If preflight fails, it indicates a **broken test harness**, not a broken system under test.

---

## 🧱 What Preflight Does *Not* Do

Preflight **does not**:
- Call live APIs
- Depend on Docker networks or deployed services
- Validate JSON schemas
- Require WordPress, WooCommerce, or databases
- Block deployment decisions

Those checks belong to **Contract** and **Environment Verification** stages.

---

## 🧪 Local Execution

Run preflight checks locally to validate your framework setup:

```bash
pytest -m preflight -v