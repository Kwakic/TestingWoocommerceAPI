
# 🧪 Customers Team Guide

This is the domain guide for working with Customers inside the EcommerceAPI test framework.

This guide documents the customer-specific conventions, fixtures, and testing patterns used by the Customers domain.

It complements the framework documentation and intentionally avoids repeating framework-wide concepts such as validators, markers, fixtures, or CI strategy.

---

## ✅ Recommended fixtures (use these)

For all customer tests prefer the domain-scoped fixtures provided by the `customers` test package:

- `customer_helper`
  High-level API helper for customer operations (create, update, list, delete).

- `customers_dao`
  DAO for database assertions (verify records exist, match API responses, etc.).

- `create_valid_customer`
  Happy-path domain fixture — builds valid creation data through the Customer Builder/Factory path, provisions the customer through the Customer Provisioner, validates the setup response, and registers ownership for automatic cleanup.

Example (pytest style):
```python
def test_update_customer(customer_helper, customers_dao, create_valid_customer):
    customer = create_valid_customer()  # validated, owned customer dict

    updated = customer_helper.update_customer(
        customer["id"],
        payload={"first_name": "New"},
    )

    assert updated["first_name"] == "New"
    assert customers_dao.exists(customer["id"])
```

---

## 🚫 Do NOT do the following

To keep tests stable and readable, avoid:

- ❌ Importing helper or DAO classes directly (use fixtures instead)
- ❌ Instantiating `RequestUtility` or similar low-level helpers yourself
- ❌ Deleting test-owned resources manually when DELETE is not the operation under test
- ℹ️ When a test explicitly verifies DELETE, the test performs the DELETE operation and must update ownership/cleanup tracking so the fixture does not attempt a second deletion
- ❌ Importing fixtures from another domain (e.g. `orders` → `customers`)
- ❌ Bypassing framework cleanup or resource tracking

Valid setup creation, response validation, ownership registration, and normal cleanup are handled through the framework. The test remains responsible for the operation it is actually verifying.

---

## 🧪 Customer test-data patterns

Customer tests now distinguish between **creating a new customer** and **preparing state
for an existing customer**.

### Create a new customer

Use `create_valid_customer()` for normal valid setup:

```python
customer = create_valid_customer()
```

The fixture follows:

```text
CustomerBuilder
    ↓
CustomerFactory
    ↓
CustomerProvisioner
    ↓
CustomersHelper / API
    ↓
WooCommerce
    ↓
validated customer + ownership
```

### Customize creation data

When a test needs reusable creation customization, use the Customer Builder:

```python
customer = create_valid_customer(
    email="known@example.com",
)
```

The fixture remains responsible for provisioning, validation, and ownership.

### Prepare an existing customer state

When another operation needs an existing customer in a specific prerequisite state, use
`CustomerStateBuilder` together with `CustomerStateProvisioner`.

```text
Existing customer
    ↓
CustomerStateBuilder
    ↓
CustomerStateProvisioner
    ↓
existing customer in required state
```

Do **not** use the State Provisioner to hide the operation under test. If the test is
verifying `PUT /customers/{id}`, the PUT remains visible in the test's Act step.

### Scenario-specific values

Not every value belongs in the Factory or Builder. Keep values in the test when they are
specific to that scenario, such as:

- intentionally invalid values;
- boundary values;
- non-existent IDs;
- pagination-specific identifiers;
- one-off business inputs.

The goal is clear responsibility, not maximum abstraction.

---

## 🔁 Cross-team / cross-domain usage (advanced)

If another team (for example, `orders`) needs to interact with customers, use the framework’s generic access helpers — do not import domain fixtures across packages.

Allowed pattern:
```python
def test_order_for_existing_customer(entity_helper):
    customer_helper = entity_helper("customers")

    # Use the generic domain access path for cross-domain setup.
    customer = customer_helper.create_customer(
        payload={"email": "known@example.com"}
    )

    # use customer in the orders test...
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

    # Use the generic domain access path for cross-domain setup.
    customer = customer_helper.create_customer(
        payload={"email": "known@example.com"}
    )

    # use customer in the orders test...
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
- If the test is **ABOUT** customer behavior → use `customer_helper`
- If another domain **NEEDS** customer functionality → use `entity_helper("customers")`

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

---

## 🧭 Related Documentation

This guide covers **customer-specific testing conventions** only.

For framework-wide guidance, see:

- `README_TEST_DEVELOPMENT_GUIDE.md` — how to write tests in this framework
- `README_TEST_DATA_ARCHITECTURE.md` — test-data generation, state preparation, provisioning, ownership, and cleanup
- `README_ARCHITECTURE.md` — framework architecture
- `README_VALIDATORS.md` — reusable validation patterns
