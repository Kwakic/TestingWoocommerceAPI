# 🧪 Products Team Guide

This is the domain guide for working with Products inside the EcommerceAPI test framework.

It covers product-specific fixtures, API usage, and testing conventions. Framework-wide architecture, validators, CI, and generic fixture behavior belong in the framework documentation.

---

## ✅ Recommended fixtures

For product-domain tests, prefer the domain-scoped fixtures:

- `product_helper`
  High-level API helper for product operations.

- `products_dao`
  DAO for database assertions and API/DB consistency checks.

- `create_valid_product`
  Happy-path factory fixture — creates a valid product, validates the response, and registers cleanup automatically.

- `product_api_raw`
  Raw API client for scenarios where the test must inspect the actual HTTP response, especially negative API tests.

Example:

```python
def test_get_product(product_helper, create_valid_product):
    product = create_valid_product()
    response = product_helper.get_product(product["id"])
    assert response["id"] == product["id"]
```

---

## 🚫 Do NOT do the following

- ❌ Import helper or DAO classes directly; use fixtures.
- ❌ Instantiate low-level HTTP/request utilities yourself.
- ❌ Call delete APIs manually; framework cleanup handles created resources.
- ❌ Import fixtures from another domain.
- ❌ Bypass resource registration or cleanup.

Keep product tests focused on product behavior; let the framework manage lifecycle concerns.

---

## 🔍 When to use `product_api_raw`

Most product tests should use `product_helper`.

Use `product_api_raw` when the test needs to verify the HTTP operation itself, for example:

- Expected `4xx` responses.
- Duplicate SKU or other API rejection scenarios.
- Response status and raw response details.
- Cases where the normal helper returns parsed data rather than `HttpResponse`.

Example:

```python
def test_create_product_with_duplicate_sku(product_api_raw):
    response = product_api_raw.post(
        endpoint="products",
        payload={"name": "Duplicate", "sku": "existing-sku"},
    )

    assert response.status_code == 400
```

The test owns the HTTP status assertion. Response-body validation belongs to the appropriate validator.

---

## 🔁 Cross-domain usage

If another domain needs product functionality, use the framework's generic access helpers rather than importing product fixtures.

```python
def test_order_with_existing_product(entity_helper):
    product_helper = entity_helper("products")
    product = product_helper.create_product()
    # use product in the order test...
```

- ✔ No imports from `tests/products`
- ✔ Keeps domain boundaries clean
- ✔ Suitable for cross-domain or generic tests

---

## ⚙️ Advanced access

Use framework-level access only when the test genuinely needs it:

- `entity_helper("products")`
- `entity_dao("products")`
- `all_resources` for special infrastructure/resource-management cases

Most product tests should remain domain-scoped.

---

## 🧭 Cheat Sheet

### Use `product_helper` when…

- The test lives under `tests/products/`.
- The test is about product behavior.
- You want normal parsed API data.

### Use `product_api_raw` when…

- The test is specifically checking HTTP behavior.
- You need to assert a `4xx`/other status.
- The normal helper return type is not suitable for the scenario.

### Use `entity_helper("products")` when…

- Another domain needs product functionality.
- The test is generic or parametrized across entities.
- You want to avoid coupling to `tests/products`.

### Rule of thumb

**If the test is ABOUT products → use `product_helper`.**

**If another domain NEEDS products → use `entity_helper("products")`.**

**If the test needs the actual HTTP response → use `product_api_raw`.**

---

## 🧠 Key principles

- The Products domain owns ergonomic, domain-scoped fixtures.
- Tests own HTTP status assertions for the operation under test.
- Validators own response/data validation, not transport assertions.
- Cross-domain tests use generic entity access.
- Cleanup is automatic — do not delete resources manually.
- Prefer the simplest fixture that matches the test's purpose.

---

## 🧭 Related Documentation

For framework-wide guidance, see:

- `README_TEST_DEVELOPMENT_GUIDE.md` — how to write tests
- `README_ARCHITECTURE.md` — framework architecture
- `README_VALIDATORS.md` — reusable validation patterns
- `README_API_CLIENT.md` — API client and response handling
