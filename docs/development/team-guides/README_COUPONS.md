# 🧪 Coupons Team Guide

This is the domain guide for working with Coupons inside the EcommerceAPI test framework.

This guide documents the coupon-specific conventions, fixtures, test-data patterns, and testing practices used by the Coupons domain.

It complements the framework documentation and intentionally avoids repeating framework-wide concepts such as validators, markers, fixtures, or CI strategy.

---

## ✅ Recommended fixtures (use these)

For all coupon tests prefer the domain-scoped fixtures provided by the `coupons` test package:

- `coupon_helper`
  High-level API helper for coupon operations (create, update, list, get, and delete).

- `coupons_dao`
  DAO for database assertions (verify records exist, match API responses, etc.).

- `create_valid_coupon`
  Happy-path domain fixture — builds valid creation data through the Coupon Builder/Factory path, provisions the coupon through the Coupon Provisioner, validates the setup response, and registers ownership for automatic cleanup.

- `coupon_api_raw`
  Raw API client for scenarios where the test must inspect the actual HTTP response, especially negative API tests.

Example (pytest style):

```python
def test_update_coupon(coupon_helper, coupons_dao, create_valid_coupon):
    coupon = create_valid_coupon()

    updated = coupon_helper.update_coupon(
        coupon["id"],
        payload={"description": "Updated coupon"},
    )

    assert updated["description"] == "Updated coupon"
    assert coupons_dao.exists(coupon["id"])
```

---

## 🚫 Do NOT do the following

To keep tests stable, readable, and aligned with the Coupons architecture, avoid:

- ❌ Importing helper or DAO classes directly (use fixtures instead)
- ❌ Instantiating `RequestUtility` or similar low-level helpers yourself
- ❌ Deleting test-owned resources manually when DELETE is not the operation under test
- ℹ️ When a test explicitly verifies DELETE, the test performs the DELETE operation and must update ownership/cleanup tracking so the fixture does not attempt a second deletion
- ❌ Importing fixtures from another domain (e.g. `orders` → `coupons`)
- ❌ Bypassing framework cleanup or resource tracking

Valid setup creation, response validation, ownership registration, and normal cleanup are handled through the framework. The test remains responsible for the operation it is actually verifying.

---

## 🧪 Coupon test-data patterns

Coupon tests distinguish between **creating a new coupon** and **preparing state for an existing coupon**.

### Create a new coupon

Use `create_valid_coupon()` for normal valid setup:

```python
coupon = create_valid_coupon()
```

The fixture follows:

```text
CouponBuilder
    ↓
CouponFactory
    ↓
CouponProvisioner
    ↓
CouponsHelper / API
    ↓
WooCommerce
    ↓
validated coupon + ownership
```

The fixture is the test-facing gatekeeper for normal coupon creation. The test receives a validated coupon dictionary and does not need to manage provisioning or cleanup itself.

### Customize creation data

When a test needs reusable creation customization, pass scenario-specific overrides through `create_valid_coupon()`:

```python
coupon = create_valid_coupon(
    code="known-coupon",
    discount_type="fixed_cart",
    amount="25.00",
)
```

The fixture remains responsible for:

- building the creation data through the Coupon Builder/Factory path;
- provisioning the coupon;
- validating the creation response;
- registering ownership for cleanup.

The Coupon Builder answers:

> What should be different for this particular scenario?

The Coupon Factory answers:

> How do I generate a complete valid coupon?

The Coupon Provisioner answers:

> How do I send this already-prepared coupon creation data into the real system?

These responsibilities should remain separate.

### Prepare an existing coupon state

When another operation needs an existing coupon in a specific prerequisite state, use `CouponStateBuilder` together with `CouponStateProvisioner`.

```text
Existing coupon
    ↓
CouponStateBuilder
    ↓
CouponStateProvisioner
    ↓
existing coupon in required state
```

Use the State Builder for partial state preparation, for example:

```python
state = (
    CouponStateBuilder()
    .with_amount("20.00")
    .with_discount_type("fixed_cart")
    .build()
)
```

Then provision that state through the State Provisioner.

Do **not** use the State Provisioner to hide the operation under test. If the test is verifying `PUT /coupons/{id}`, the PUT remains visible in the test's Act step.

The State Builder is intentionally separate from the Coupon Factory: state preparation for an existing resource should not silently generate a complete new coupon or introduce unrelated defaults.

### Scenario-specific values

Not every value belongs in the Factory or Builder. Keep values in the test when they are specific to that scenario, such as:

- intentionally invalid values;
- boundary values;
- non-existent IDs;
- duplicate coupon codes used to exercise rejection behavior;
- pagination-specific identifiers;
- one-off business inputs.

For example, a duplicate coupon code used to verify API rejection should remain visible in the negative test rather than being hidden inside a factory abstraction.

The goal is clear responsibility, not maximum abstraction.

### Generated coupon values

Reusable generation logic that creates valid coupon test data belongs in the Coupon Factory.

For example, the Coupon Factory can generate a unique coupon code when the scenario does not supply one.

The Factory owns generation of test-data values. The Coupons Helper should not generate test data; it should orchestrate coupon/API operations.

This distinction keeps test-data generation separate from domain/API orchestration.

### Unit vs integration coverage for test-data generation

When a Coupon Factory method contains its own calculation or validation logic, test that logic separately from the Coupon API integration test.

For example:

- `tests/shared/unit_tests/test_data_infrastructure/test_coupon_factory.py`
  Tests Coupon Factory generation logic in isolation.

- `tests/coupons/.../test_create_coupons.py`
  Tests that a coupon can actually be created using generated or customized test data.

The two tests answer different questions:

```text
Unit test
CouponFactory
    ↓
Does the test-data generation logic behave correctly?


Integration test
CouponFactory
    ↓
CouponBuilder / fixture
    ↓
CouponProvisioner
    ↓
CouponsHelper / API
    ↓
WooCommerce
    ↓
Can the real coupon operation succeed with that data?
```

Do not move an API integration scenario into the unit-test area merely because it uses a Factory method.

---

## 🔍 When to use `coupon_api_raw`

Most coupon tests should use `coupon_helper`.

Use `coupon_api_raw` when the test needs to verify the HTTP operation itself, for example:

- Expected `4xx` responses.
- Duplicate coupon-code or other API rejection scenarios.
- Response status and raw response details.
- Cases where the normal helper returns parsed data rather than `HttpResponse`.

Example:

```python
def test_create_coupon_with_duplicate_code(
    coupon_api_raw,
    create_valid_coupon,
):
    existing = create_valid_coupon(code="existing-code")

    response = coupon_api_raw.post(
        endpoint="coupons",
        payload={
            "code": existing["code"],
            "discount_type": "fixed_cart",
        },
    )

    assert response.status_code == 400
```

The test owns the HTTP status assertion. Response-body validation belongs to the appropriate validator.

A useful pattern for negative tests is:

```text
Valid precondition
    ↓
create_valid_coupon()
    ↓
owned/validated coupon
    ↓
Raw API operation with invalid or duplicate data
    ↓
test asserts expected HTTP behavior
```

The valid setup remains inside the normal test-data lifecycle; only the intentionally invalid operation bypasses the normal happy-path pipeline.

---

## 🔁 Cross-team / cross-domain usage (advanced)

If another team (for example, `orders`) needs to interact with coupons, use the framework's generic access helpers — do not import domain fixtures across packages.

Allowed pattern:

```python
def test_order_with_coupon(entity_helper):
    coupon_helper = entity_helper("coupons")

    # Use the generic domain access path for cross-domain setup.
    coupon = coupon_helper.create_coupon()

    # use coupon in the orders test...
```

- ✔ This is allowed and decouples teams
- ✔ No imports from `tests/coupons`
- ❌ Do NOT import `coupon_helper` from the `coupons` test package directly

Cross-domain tests should consume the generic framework access path rather than depending on another domain's pytest fixtures.

---

## ⚙️ Advanced / framework-level access (use sparingly)

Framework-level fixtures are available for special cases:

- `entity_helper("coupons")`
- `entity_dao("coupons")`
- `all_resources` (rare cases only)

Intended uses:

- Cross-domain tests
- Parametrized tests across domains
- Framework or infrastructure validation

Most coupon tests should not require these low-level fixtures.

---

## 🧭 Cheat Sheet: `coupon_helper` vs `entity_helper("coupons")`

Use this cheat sheet to decide which fixture is correct for your test.

### ✅ Use `coupon_helper` when…

- You are writing coupon-domain tests
- The test lives under `tests/coupons/`
- The test is about coupon behavior or validation
- You want the simplest, most readable API

Example:

```python
def test_create_coupon(coupon_helper):
    coupon = coupon_helper.create_coupon()
    assert coupon["id"]
```

- ✔ Preferred
- ✔ Most common case
- ✔ Domain-owned and ergonomic

### 🔁 Use `entity_helper("coupons")` when…

- You are not in the coupons domain (e.g. orders)
- You need to reuse coupon functionality across teams
- You are writing generic or parametrized tests
- The test should not depend on coupon test code

Example:

```python
def test_order_for_existing_coupon(entity_helper):
    coupon_helper = entity_helper("coupons")

    # Use the generic domain access path for cross-domain setup.
    coupon = coupon_helper.create_coupon()

    # use coupon in the orders test...
```

- ✔ Cross-domain safe
- ✔ No coupling between teams
- ✔ Framework-level access

### 🚫 Do NOT do this

```python
# ❌ Wrong
from tests.coupons.conftest import coupon_helper
```

- ❌ Breaks domain boundaries
- ❌ Creates tight coupling
- ❌ Not supported

### 🧠 Rule of Thumb

- If the test is **ABOUT** coupon behavior → use `coupon_helper`
- If another domain **NEEDS** coupon functionality → use `entity_helper("coupons")`
- If the test needs the **actual HTTP response** → use `coupon_api_raw`
- If the test needs a **new valid coupon** → use `create_valid_coupon`
- If the test needs to **prepare state for an existing coupon** → use `CouponStateBuilder` + `CouponStateProvisioner`

When in doubt, default to the simplest domain-scoped fixture that matches the test's purpose.

---

## 🧠 Key principles

- The framework owns discovery and generic access.
- Domains own ergonomic, easy-to-use fixtures — prefer them over low-level access.
- Coupon test-data generation belongs in the Coupon Factory, not the API Helper.
- Coupon creation and existing-coupon state preparation are separate flows.
- Builders customize test data; Factories generate complete valid defaults.
- Provisioners cross the system boundary; they do not generate or validate test data.
- Tests remain responsible for the behavior they actually verify.
- No fixture leakage across domains.
- No coupling between teams via imports.
- Cleanup is automatic — do not delete resources manually.
- If you think you need low-level access, ask first — the framework likely already supports your use case.

---

## 🧭 Related Documentation

This guide covers **coupon-specific testing conventions and test-data patterns** only.

For framework-wide guidance, see:

- `README_TEST_DEVELOPMENT_GUIDE.md` — how to write tests in this framework
- `README_TEST_DATA_ARCHITECTURE.md` — test-data generation, state preparation, provisioning, ownership, and cleanup
- `README_ARCHITECTURE.md` — framework architecture
- `README_VALIDATORS.md` — reusable validation patterns
