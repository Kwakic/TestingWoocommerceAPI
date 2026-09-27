# 🧪 Products Team Guide

This is the domain guide for working with Products inside the EcommerceAPI test framework.

This guide documents the product-specific conventions, fixtures, test-data patterns, and testing practices used by the Products domain.

It complements the framework documentation and intentionally avoids repeating framework-wide concepts such as validators, markers, fixtures, or CI strategy.


---

## ✅ Recommended fixtures (use these)

For all product tests prefer the domain-scoped fixtures provided by the `products` test package:

- `product_helper`
  High-level API helper for product operations (create, update, list, delete, and product-specific queries).

- `products_dao`
  DAO for database assertions (verify records exist, match API responses, etc.).

- `create_valid_product`
  Happy-path domain fixture — builds valid creation data through the Product Builder/Factory path, provisions the product through the Product Provisioner, validates the setup response, and registers ownership for automatic cleanup.

- `product_api_raw`
  Raw API client for scenarios where the test must inspect the actual HTTP response, especially negative API tests.

Example (pytest style):

```python
def test_update_product(product_helper, products_dao, create_valid_product):
    product = create_valid_product()

    updated = product_helper.update_product(
        product["id"],
        payload={"name": "Updated Product"},
    )

    assert updated["name"] == "Updated Product"
    assert products_dao.exists(product["id"])
```


---

## 🚫 Do NOT do the following

To keep tests stable, readable, and aligned with the Products architecture, avoid:

- ❌ Importing helper or DAO classes directly (use fixtures instead)
- ❌ Instantiating `RequestUtility` or similar low-level helpers yourself
- ❌ Deleting test-owned resources manually when DELETE is not the operation under test
- ℹ️ When a test explicitly verifies DELETE, the test performs the DELETE operation and must update ownership/cleanup tracking so the fixture does not attempt a second deletion
- ❌ Importing fixtures from another domain (e.g. `orders` → `products`)
- ❌ Bypassing framework cleanup or resource tracking

Valid setup creation, response validation, ownership registration, and normal cleanup are handled through the framework. The test remains responsible for the operation it is actually verifying.


---

## 🧪 Product test-data patterns

Product tests distinguish between **creating a new product** and **preparing state for an existing product**.

### Create a new product

Use `create_valid_product()` for normal valid setup:

```python
product = create_valid_product()
```

The fixture follows:

```text
ProductBuilder
    ↓
ProductFactory
    ↓
ProductProvisioner
    ↓
ProductsHelper / API
    ↓
WooCommerce
    ↓
validated product + ownership
```

The fixture is the test-facing gatekeeper for normal product creation. The test receives a validated product dictionary and does not need to manage provisioning or cleanup itself.

### Customize creation data

When a test needs reusable creation customization, pass scenario-specific overrides through `create_valid_product()`:

```python
product = create_valid_product(
    name="Known Product",
    sku="known-sku",
    regular_price="49.99",
)
```

The fixture remains responsible for:

- building the creation data through the Product Builder/Factory path;
- provisioning the product;
- validating the creation response;
- registering ownership for cleanup.

The Product Builder answers:

> What should be different for this particular scenario?

The Product Factory answers:

> How do I generate a complete valid product?

The Product Provisioner answers:

> How do I send this already-prepared product creation data into the real system?

These responsibilities should remain separate.

### Prepare an existing product state

When another operation needs an existing product in a specific prerequisite state, use `ProductStateBuilder` together with `ProductStateProvisioner`.

```text
Existing product
    ↓
ProductStateBuilder
    ↓
ProductStateProvisioner
    ↓
existing product in required state
```

Use the State Builder for partial state preparation, for example:

```python
state = (
    ProductStateBuilder()
    .with_regular_price("100.00")
    .with_sale_price("80.00")
    .build()
)
```

Then provision that state through the State Provisioner.

Do **not** use the State Provisioner to hide the operation under test. If the test is verifying `PUT /products/{id}`, the PUT remains visible in the test's Act step.

The State Builder is intentionally separate from the Product Factory: state preparation for an existing resource should not silently generate a complete new product or introduce unrelated defaults.

### Scenario-specific values

Not every value belongs in the Factory or Builder. Keep values in the test when they are specific to that scenario, such as:

- intentionally invalid values;
- boundary values;
- non-existent IDs;
- duplicate SKUs used to exercise rejection behavior;
- pagination-specific identifiers;
- one-off business inputs.

For example, an invalid product type should normally remain visible in the negative test rather than being hidden inside a factory abstraction.

The goal is clear responsibility, not maximum abstraction.

### Generated product values

Reusable generation logic that creates valid product test data belongs in the Product Factory.

For example, `ProductFactory.generate_sale_price()` can generate a sale price derived from a regular price for scenarios that need a valid relationship between the two values.

The Factory owns generation of test-data values. The Product Helper should not generate test data; it should orchestrate product/API operations.

This distinction keeps test-data generation separate from domain/API orchestration.

### Unit vs integration coverage for test-data generation

When a Product Factory method contains its own calculation or validation logic, test that logic separately from the Product API integration test.

For example:

- `tests/shared/unit_tests/test_data_infrastructure/test_product_factory.py`
  Tests `ProductFactory.generate_sale_price()` in isolation.

- `tests/products/.../test_create_products.py`
  Tests that a product can actually be created using generated sale-price data.

The two tests answer different questions:

```text
Unit test
ProductFactory
    ↓
Does the test-data generation logic behave correctly?


Integration test
ProductFactory
    ↓
ProductBuilder / fixture
    ↓
ProductProvisioner
    ↓
ProductsHelper / API
    ↓
WooCommerce
    ↓
Can the real product operation succeed with that data?
```

Do not move an API integration scenario into the unit-test area merely because it uses a Factory method.


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
def test_create_product_with_duplicate_sku(
    product_api_raw,
    create_valid_product,
):
    existing = create_valid_product(sku="existing-sku")

    response = product_api_raw.post(
        endpoint="products",
        payload={"name": "Duplicate", "sku": existing["sku"]},
    )

    assert response.status_code == 400
```

The test owns the HTTP status assertion. Response-body validation belongs to the appropriate validator.


---

## 🔁 Cross-team / cross-domain usage (advanced)

If another team (for example, `orders`) needs to interact with products, use the framework's generic access helpers — do not import domain fixtures across packages.

Allowed pattern:

```python
def test_order_with_existing_product(entity_helper):
    product_helper = entity_helper("products")

    # Use the generic domain access path for cross-domain setup.
    product = product_helper.create_product()

    # use product in the orders test...
```

- ✔ This is allowed and decouples teams
- ✔ No imports from `tests/products`
- ❌ Do NOT import `product_helper` from the `products` test package directly

Cross-domain tests should consume the generic framework access path rather than depending on another domain's pytest fixtures.


---

## ⚙️ Advanced / framework-level access (use sparingly)

Framework-level fixtures are available for special cases:

- `entity_helper("products")`
- `entity_dao("products")`
- `all_resources` (rare cases only)

Intended uses:

- Cross-domain tests
- Parametrized tests across domains
- Framework or infrastructure validation

Most product tests should not require these low-level fixtures.


---

## 🧭 Cheat Sheet: `product_helper` vs `entity_helper("products")`

Use this cheat sheet to decide which fixture is correct for your test.

### ✅ Use `product_helper` when…

- You are writing product-domain tests
- The test lives under `tests/products/`
- The test is about product behavior or validation
- You want the simplest, most readable API

Example:

```python
def test_create_product(product_helper):
    product = product_helper.create_product()
    assert product["id"]
```

- ✔ Preferred
- ✔ Most common case
- ✔ Domain-owned and ergonomic


---

### 🔁 Use `entity_helper("products")` when…

- You are not in the products domain (e.g. orders)
- You need to reuse product functionality across teams
- You are writing generic or parametrized tests
- The test should not depend on product test code

Example:

```python
def test_order_for_existing_product(entity_helper):
    product_helper = entity_helper("products")

    # Use the generic domain access path for cross-domain setup.
    product = product_helper.create_product()

    # use product in the orders test...
```

- ✔ Cross-domain safe
- ✔ No coupling between teams
- ✔ Framework-level access


---

### 🚫 Do NOT do this

```python
# ❌ Wrong
from tests.products.conftest import product_helper
```

- ❌ Breaks domain boundaries
- ❌ Creates tight coupling
- ❌ Not supported


---

### 🧠 Rule of Thumb

- If the test is **ABOUT** product behavior → use `product_helper`
- If another domain **NEEDS** product functionality → use `entity_helper("products")`
- If the test needs the **actual HTTP response** → use `product_api_raw`
- If the test needs a **new valid product** → use `create_valid_product`
- If the test needs to **prepare state for an existing product** → use `ProductStateBuilder` + `ProductStateProvisioner`

When in doubt, default to the simplest domain-scoped fixture that matches the test's purpose.


---

## 🧠 Key principles

- The framework owns discovery and generic access.
- Domains own ergonomic, easy-to-use fixtures — prefer them over low-level access.
- Product test-data generation belongs in the Product Factory, not the API Helper.
- Product creation and existing-product state preparation are separate flows.
- Builders customize test data; Factories generate complete valid defaults.
- Provisioners cross the system boundary; they do not generate or validate test data.
- Tests remain responsible for the behavior they actually verify.
- No fixture leakage across domains.
- No coupling between teams via imports.
- Cleanup is automatic — do not delete resources manually.
- If you think you need low-level access, ask first — the framework likely already supports your use case.


---

## 🧭 Related Documentation

This guide covers **product-specific testing conventions and test-data patterns** only.

For framework-wide guidance, see:

- `README_TEST_DEVELOPMENT_GUIDE.md` — how to write tests in this framework
- `README_TEST_DATA_ARCHITECTURE.md` — test-data generation, state preparation, provisioning, ownership, and cleanup
- `README_ARCHITECTURE.md` — framework architecture
- `README_VALIDATORS.md` — reusable validation patterns
