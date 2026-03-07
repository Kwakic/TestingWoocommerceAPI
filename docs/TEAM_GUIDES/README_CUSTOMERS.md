# 🧪 Writing Customer API Tests (Team Guide)

A short, practical guide for writing customer-domain API tests using the shared test framework. Keep tests simple, stable, and maintainable by following the patterns below.

---

## ✅ Recommended fixtures (use these)

For all customer tests prefer the domain-scoped fixtures provided by the `customers` test package:

- `customer_helper`  
  High-level API helper for customer operations (create, update, list, delete).

- `customers_dao`  
  DAO for database assertions (verify records exist, match API responses, etc.).

- `create_valid_customer`  
  Happy-path factory fixture — creates a valid customer, validates the response, and registers cleanup automatically.

Example (pytest style):
```python
def test_update_customer(customer_helper, customers_dao, create_valid_customer):
    customer = create_valid_customer  # fixture returns a validated customer object
    updated = customer_helper.update_customer(customer["id"], {"name": "New"})
    assert updated["name"] == "New"
    assert customers_dao.exists(customer["id"])
```

---

## 🚫 Do NOT do the following

To keep tests stable and readable, avoid:

- ❌ Importing helper or DAO classes directly (use fixtures instead)  
- ❌ Instantiating `RequestUtility` or similar low-level helpers yourself  
- ❌ Calling delete APIs manually in tests (framework handles cleanup)  
- ❌ Importing fixtures from another domain (e.g. `orders` → `customers`)  
- ❌ Bypassing framework cleanup or resource tracking

All lifecycle management (creation, validation, cleanup) is handled by the framework.

---

## 🔁 Cross-team / cross-domain usage (advanced)

If another team (for example, `orders`) needs to interact with customers, use the framework’s generic access helpers — do not import domain fixtures across packages.

Allowed pattern:
```python
def test_order_for_existing_customer(entity_helper):
    customer_helper = entity_helper("customers")
    customer = customer_helper.create_customer()
    # use customer in orders test...
```

- ✔ This is allowed and decouples teams  
- ✔ No imports from `tests/customers`  
- ❌ Do NOT import `customer_helper` from the `customers` test package directly

---

## ⚙️ Advanced / framework-level access (use sparingly)

Framework-level fixtures are available for special cases:

- `entity_helper("customers")`  
- `entity_dao("customers")`  
- `all_resources` (rare cases only)

Intended uses:
- Cross-domain tests  
- Parametrized tests across domains  
- Framework or infrastructure validation

Most customer tests should not require these low-level fixtures.

---

## 🧭 Cheat Sheet: `customer_helper` vs `entity_helper("customers")`

Use this cheat sheet to decide which fixture is correct for your test.

### ✅ Use `customer_helper` when…
- You are writing customer-domain tests  
- The test lives under `tests/customers/`  
- The test is about customer behavior or validation  
- You want the simplest, most readable API

Example:
```python
def test_create_customer(customer_helper):
    customer = customer_helper.create_customer()
    assert customer["id"]
```

- ✔ Preferred  
- ✔ Most common case  
- ✔ Domain-owned and ergonomic

---

### 🔁 Use `entity_helper("customers")` when…
- You are not in the customers domain (e.g. orders, payments)  
- You need to reuse customer functionality across teams  
- You are writing generic or parametrized tests  
- The test should not depend on customer test code

Example:
```python
def test_order_for_existing_customer(entity_helper):
    customer_helper = entity_helper("customers")
    customer = customer_helper.create_customer()
    # use customer in orders test...
```

- ✔ Cross-domain safe  
- ✔ No coupling between teams  
- ✔ Framework-level access

---

### 🚫 Do NOT do this
```python
# ❌ Wrong
from tests.customers.conftest import customer_helper
```

- ❌ Breaks domain boundaries  
- ❌ Creates tight coupling  
- ❌ Not supported

---

### 🧠 Rule of Thumb
- If the test is **ABOUT** customers → use `customer_helper`  
- If the test **NEEDS** customers → use `entity_helper("customers")`

When in doubt, default to `customer_helper`.

---

## 🧠 Key principles

- The framework owns discovery and generic access.  
- Domains own ergonomic, easy-to-use fixtures — prefer them over low-level access.  
- No fixture leakage across domains.  
- No coupling between teams via imports.  
- Cleanup is automatic — do not delete resources manually.  
- If you think you need low-level access, ask first — the framework likely already supports your use case.

---

Need examples or help? See the pytest docs: [pytest documentation](https://docs.pytest.org/en/stable/) or ask the 
framework maintainers on the team channel. 😊


------------------------------------------------------------------
# 🧪 Validation Pattern in Customer Tests (NEW)

Customer tests follow a structured validation pipeline.

Example:

response = customer_helper.get_customer_by_id(customer_id, return_http_response=True)

customer_model = assert_customer_retrieved_successfully(response)

assert_customer_identity(customer_model, customer_id, email)

customer_helper.assert_customer_exists_and_matches_db(email, customers_dao)


Validation stages:

Transport validation
      ↓
Structure validation (Pydantic)
      ↓
Business validation
      ↓
DB validation


------------------------------------------------------------------
# 🧠 Why This Pattern Exists

This layered validation approach ensures:

- API responses are structurally valid
- business rules are verified
- API and DB remain consistent

It also keeps tests readable for newcomers and prevents duplication
of validation logic across test files.
    