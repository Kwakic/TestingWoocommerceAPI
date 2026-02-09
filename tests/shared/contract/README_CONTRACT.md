
## Overview
The **Shared Contract Test Suite** validates the **API data contracts** exposed by the platform.

A *contract* defines the **exact shape, types, and required fields** of API responses.  
These tests ensure that every environment (test, staging, prod) returns responses that conform to the agreed JSON schemas — regardless of implementation details.

Unlike preflight tests, **contract tests actively call live APIs** and validate their payloads.

---

## ✅ Purpose

Contract tests exist to protect teams from **breaking API changes**.

They validate that:
- 📜 API responses conform to published **JSON schemas**
- 🔗 Required fields exist and have correct data types
- 🧩 Optional fields, if present, match expected formats
- 🧪 Entity lists and single-entity endpoints remain structurally compatible
- 🚨 Backward-incompatible changes are caught early in CI

Contract tests **do not validate business rules** — only structure and compatibility.

---

## 🚫 What Contract Tests Do NOT Do

Contract tests intentionally do **not**:
- Test business logic or workflows
- Assert specific database state
- Create, update, or delete entities
- Validate performance or response times
- Replace full API or regression testing

They answer one question only:
> “Does this API still speak the same language?”

---

## 🧱 Execution Behavior

### 🧪 Local Runs

Run all shared contract tests:

```bash
pytest tests/shared/contract -v
