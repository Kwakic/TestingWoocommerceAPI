# 🧪 Coupons Team Guide

This is the domain guide for working with Coupons inside the EcommerceAPI test framework.

It covers coupon-specific fixtures, API usage, and testing conventions. Framework-wide architecture, validators, CI, and generic fixture behavior belong in the framework documentation.

---

## ✅ Recommended fixtures

For coupon-domain tests, prefer the domain-scoped fixtures:

- `coupon_helper`
  High-level API helper for coupon operations.

- `coupons_dao`
  DAO for database assertions and API/DB consistency checks.

- `create_valid_coupon`
  Happy-path factory fixture — creates a valid coupon, validates the response, and registers cleanup automatically.

- `coupon_api_raw`
  Raw API client for scenarios where the test must inspect the actual HTTP response, especially negative API tests.

Example:

```python
def test_get_coupon(coupon_helper, create_valid_coupon):
    coupon = create_valid_coupon()
    response = coupon_helper.get_coupon(coupon["id"])
    assert response["id"] == coupon["id"]
```

---

## 🚫 Do NOT do the following

- ❌ Import helper or DAO classes directly; use fixtures.
- ❌ Instantiate low-level HTTP/request utilities yourself.
- ❌ Call delete APIs manually; framework cleanup handles created resources.
- ❌ Import fixtures from another domain.
- ❌ Bypass resource registration or cleanup.

Keep coupon tests focused on coupon behavior; let the framework manage lifecycle concerns.

---

## 🔍 When to use `coupon_api_raw`

Most coupon tests should use `coupon_helper`.

Use `coupon_api_raw` when the test needs to verify the HTTP operation itself, for example:

- Expected `4xx` responses.
- Duplicate coupon-code scenarios.
- Response status and raw response details.
- Cases where the normal helper returns parsed data rather than `HttpResponse`.

Example:

```python
def test_create_coupon_with_duplicate_code(coupon_api_raw):
    response = coupon_api_raw.post(
        endpoint="coupons",
        payload={"code": "existing-code", "discount_type": "fixed_cart"},
    )

    assert response.status_code == 400
```

The test owns the HTTP status assertion. Response-body validation belongs to the appropriate validator.

---

## 🔁 Cross-domain usage

If another domain needs coupon functionality, use the framework's generic access helpers rather than importing coupon fixtures.

```python
def test_order_with_coupon(entity_helper):
    coupon_helper = entity_helper("coupons")
    coupon = coupon_helper.create_coupon()
    # use coupon in the order test...
```

- ✔ No imports from `tests/coupons`
- ✔ Keeps domain boundaries clean
- ✔ Suitable for cross-domain or generic tests

---

## ⚙️ Advanced access

Use framework-level access only when the test genuinely needs it:

- `entity_helper("coupons")`
- `entity_dao("coupons")`
- `all_resources` for special infrastructure/resource-management cases

Most coupon tests should remain domain-scoped.

---

## 🧭 Cheat Sheet

### Use `coupon_helper` when…

- The test lives under `tests/coupons/`.
- The test is about coupon behavior.
- You want normal parsed API data.

### Use `coupon_api_raw` when…

- The test is specifically checking HTTP behavior.
- You need to assert a `4xx`/other status.
- The normal helper return type is not suitable for the scenario.

### Use `entity_helper("coupons")` when…

- Another domain needs coupon functionality.
- The test is generic or parametrized across entities.
- You want to avoid coupling to `tests/coupons`.

### Rule of thumb

**If the test is ABOUT coupons → use `coupon_helper`.**

**If another domain NEEDS coupons → use `entity_helper("coupons")`.**

**If the test needs the actual HTTP response → use `coupon_api_raw`.**

---

## 🧠 Key principles

- The Coupons domain owns ergonomic, domain-scoped fixtures.
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
