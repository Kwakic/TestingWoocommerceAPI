# 📘 Validators Architecture Guide

## 🎯 Purpose

This document explains how validation is structured in the EcommerceAPI test framework.

The goal is to keep validation:
- ✅ Clear for newcomers
- ✅ Maintainable for teams
- ✅ Scalable across microservices

---

## 🧠 High-Level Concept

There are **ONLY 3 validation layers**:

```
Schema Validator  → Structure (contract)
Assertions        → Business + DB validation (MAIN layer)
Base Validators   → Internal reusable helpers
```

---

## 🧱 1. Schema Validators (`*_schema_validator.py`)

### ✔ Purpose
Validate API response structure (contract)

### ✔ Responsibilities
- Required fields
- Field types
- JSON schema compliance

### ✔ Example
```python
validate_customer_response_schema(customer)
```

### ❗ Rules
- No business logic
- No DB checks

---

## 🧪 2. Assertions (`*_assertions.py`) ⭐ MAIN LAYER

### ✔ Purpose
This is the **primary validation layer used by tests and helpers**

### ✔ Responsibilities
- Business validation
- API correctness
- DB consistency
- Domain rules (e.g. uniqueness)

### ✔ Example
```python
assert_customer_matches_db(customer, db_customer)
assert_customer_exists_in_api(customers, email)
```

### ✔ Used by
- Helpers ✅
- Tests (optional) ✅

### ❗ Rules
- Keep functions readable
- Use domain language (customer, order, etc.)
- Combine structure + business validation if needed

---

## ⚙️ 3. Base Validators (`base_validators.py`) 🔒 INTERNAL

### ✔ Purpose
Reusable generic validation logic

### ✔ Responsibilities
- Shared validation logic
- Reduce duplication

### ✔ Example
```python
assert_entity_matches_db(...)
assert_entity_exists_in_api(...)
```

### ❗ Rules
- DO NOT use directly in tests
- DO NOT expose to users
- Used internally by assertions only

---

## 🚨 What NOT to do

### ❌ Do NOT use base validators directly in tests
```python
assert_entity_matches_db(...)  # ❌ WRONG
```

### ❌ Do NOT create extra validator layers
Avoid unnecessary abstraction like:
```
customer_validators.py  ❌
```

---

## 🔥 Recommended Flow

```
Test
 → Helper
   → Schema Validator
   → Assertions (MAIN)
```

---

## 🧠 Example Flow

```python
customer = create_valid_customer()

validate_customer_response_schema(customer)

assert_customer_matches_db(customer, db_customer)
```

---

## 🧩 Design Philosophy

| Layer | Responsibility |
|------|--------|
| Schema | Structure validation |
| Assertions | Business + DB validation |
| Base | Reusable internal logic |

---

## 🔥 Golden Rules

1. Always validate schema first
2. Use assertions as the main validation layer
3. Keep base validators internal
4. Prefer clarity over abstraction

---

## 💬 Final Takeaway

> 🔥 One clear validation layer is better than multiple confusing ones  
> 🔥 Simplicity > abstraction  

---

## 👥 For Newcomers

If you are unsure where to write validation:

👉 Use `*_assertions.py`

That is the **only place you need to care about**.



------------------------------------------------------------------
# 🔄 Framework Evolution — Pydantic Migration (NEW)

⚠️ Historical note:
This framework originally used **JSON Schema validation**.

It has now migrated to **Pydantic models** for structure validation.

Benefits:

- Strong typing
- Better validation errors
- IDE autocompletion
- Cleaner validator code
- Easier debugging during test failures


------------------------------------------------------------------
# 🧱 Updated Validation Architecture

The validation pipeline is now:

Structure validation
        ↓
API validation
        ↓
Business validation
        ↓
DB validation


------------------------------------------------------------------
# 🧠 Validator Responsibilities

Validators must **NOT fetch data**.

Validators only validate **data passed to them**.

Correct architecture:

TEST / HELPER
     ↓
FETCH DATA (API / DAO)
     ↓
VALIDATORS
     ↓
PYDANTIC MODELS
     ↓
DB VALIDATORS


------------------------------------------------------------------
# 📦 Validator Types in the Framework

STRUCTURE VALIDATION
--------------------
CustomerModel (Pydantic)


API VALIDATION
--------------
assert_valid_customer_response()
assert_customer_retrieved_successfully()


BUSINESS VALIDATION
-------------------
assert_customer_identity()


INTEGRATION VALIDATION
----------------------
assert_customer_matches_db()
assert_customer_exists_and_matches_api()
