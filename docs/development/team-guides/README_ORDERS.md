# 🧪 Orders Team Guide

This is the domain guide for working with Orders inside the EcommerceAPI test framework.

It documents the Order-specific fixtures, test-data patterns, and conventions used by the Orders domain. It complements the framework documentation and avoids repeating framework-wide guidance.

---

## ✅ Recommended fixtures (use these)

For Order tests, prefer the domain and framework fixtures already provided:

- `order_helper`
  High-level Order API operations, including create, retrieve, update, delete, and paginated listing.

- `orders_dao`
  DAO access for database assertions. Use it to retrieve Order, metadata, and line-item records before passing them to the Order DB validators.

- `create_valid_product` (when Product setup is required)
  Registered Product fixture for provisioning and cleanup of the Product used by an Order line item. Request it through pytest fixture injection; do not import it from the Products test package.

- `create_valid_order`
  Happy-path fixture that prepares data through OrderBuilder and OrderFactory, creates the Order through OrderProvisioner, checks the HTTP 201 response and Order structure, registers it for cleanup, and returns the validated response as a dictionary.

- `order_api_raw`
  Configured APIClient for negative or low-level cases that need direct request control. It bypasses OrderFactory, OrderBuilder, OrderProvisioner, and OrdersHelper; requests return the framework HttpResponse.

An Order needs an existing Product in its line items. The Order fixture does not create a Product implicitly.

Example:

```python
def test_get_order_by_id(
    order_helper,
    create_valid_product,
    create_valid_order,
):
    product = create_valid_product()
    product_id = product["id"]

    order = create_valid_order(product_id=product_id)
    order_id = order["id"]

    response = order_helper.get_order_by_id(
        order_id=order_id,
        return_http_response=True,
    )

    assert response.status_code == 200
```

The Product and Order are created through registered test fixtures, so their cleanup remains with the shared resource lifecycle.

---

## 🚫 Do NOT do the following

To keep Order tests stable and aligned with the framework, avoid:

- ❌ Importing helper, DAO, or fixture definitions directly from another test package.
- ❌ Building an Order payload inside OrdersHelper or calling RequestUtility from a test.
- ❌ Creating an Order without an existing Product ID or complete line_items.
- ❌ Manually deleting test-owned Orders when DELETE is not the operation under test.
- ❌ Bypassing resource registration and shared cleanup for valid setup data.
- ❌ Using the happy-path Order fixture for invalid creation payloads; it is designed to create valid Orders and asserts successful creation.

If a test verifies DELETE, the test should perform the deletion and ensure cleanup tracking does not try to delete the same Order again.

---

## 🧪 Order test-data patterns

Order tests separate preparing creation data, creating a real Order, and preparing changes to an existing Order.

### Create a new Order

Use create_valid_order for normal valid setup. First create a Product, because an Order line item must refer to a Product that already exists:

```python
product = create_valid_product()
order = create_valid_order(product_id=product["id"])
```

The fixture follows:

```text
OrderBuilder
    ↓
OrderFactory
    ↓
OrderProvisioner
    ↓
OrdersHelper / OrdersApi
    ↓
WooCommerce
    ↓
validated Order + ownership registration
```

The fixture owns setup validation and cleanup registration. Tests receive a validated Order dictionary and use the Order ID for the operation under test.

### Customize creation data

Pass scenario-specific creation fields through create_valid_order:

```python
order = create_valid_order(
    product_id=product["id"],
    quantity=2,
    status="processing",
    payment_method="bacs",
    payment_method_title="Direct Bank Transfer",
    set_paid=True,
)
```

OrderFactory builds the line_items structure from product_id and quantity and supplies the supported defaults. Prefer the dedicated OrderBuilder methods for readable scenario customization. Use line_items when a test needs a complete custom list of products; do not combine line_items with product_id or quantity.

The Order Builder answers:

> What should be different for this particular Order scenario?

The Order Factory answers:

> How do I assemble the supported creation payload around the Product ID?

The Order Provisioner answers:

> How do I send this prepared Order data to WooCommerce?

These responsibilities should remain separate. The Factory does not create Products, call the API, query the database, validate API responses, or register resources for cleanup.

A guest Order does not need a customer_id. Associate an existing Customer only when the scenario requires it.

### Prepare state for an existing Order

Use OrderStateBuilder to prepare a partial change and OrderStateProvisioner to apply prepared state to an existing Order:

```text
Existing Order
    ↓
OrderStateBuilder
    ↓
partial Order state
    ↓
OrderStateProvisioner
    ↓
OrdersHelper / OrdersApi
    ↓
updated Order
```

For example, a status change can be prepared as:

```python
order_state = OrderStateBuilder().with_status("cancelled").build()
```

The State Builder prepares only the fields the scenario intends to change. It does not create an Order or decide the expected result. The test remains responsible for asserting the HTTP status and the expected updated values. Do not use state preparation to hide a different operation that the test is meant to verify.

### Scenario-specific values

Keep one-off values in the test when they express the behavior being tested, including:

- intentionally invalid Order fields or payloads;
- a non-existent Order ID;
- boundary values for quantity, totals, or status;
- one-off billing or shipping details;
- a Customer or Coupon association needed only for that scenario.

Use the Factory or Builder for reusable valid creation defaults and supported scenario customization. The goal is clear responsibility, not maximum abstraction.

---

## 🔍 When to use order_api_raw

Most Order tests should use order_helper and the normal test-data fixtures.

Use order_api_raw when the test needs direct control of the request or must inspect an expected error response, for example:

- invalid or incomplete Order creation payloads;
- unsupported Order status values;
- malformed line_items;
- raw status and error details.

Example:

```python
def test_reject_order_with_invalid_status(
    order_api_raw,
    create_valid_product,
):
    product = create_valid_product()

    response = order_api_raw.post(
        endpoint="orders",
        payload={
            "status": "not-a-valid-order-status",
            "line_items": [
                {
                    "product_id": product["id"],
                    "quantity": 1,
                }
            ],
        },
    )

    assert response.status_code == 400
```

The test owns the HTTP status assertion. Validate the response body with the appropriate Order validator. Use order_api_raw for the invalid operation; keep valid prerequisites in the normal fixture lifecycle.

---

## 🗄 Order API and database validation

Use order_helper for the API operation and orders_dao to fetch persisted records. Pass those supplied records to assert_order_matches_db; the DB validator compares data and does not fetch it.

A typical comparison retrieves:

- the Order record;
- Order metadata;
- Order line-item rows;
- metadata for each product line item.

This keeps fetching in the test/DAO boundary and comparison in the DB validator. Do not put database access in OrdersHelper or validators.

The Orders API wrapper is the source of truth for Order endpoint paths and HTTP methods. Normal tests should use order_helper; use order_api_raw only when the test specifically needs direct API control.

---

## 🔁 Cross-domain usage

Orders may depend on Products and may optionally refer to Customers or Coupons.

- Do not import fixtures from another domain's conftest.
- For generic cross-domain API or DAO access, use entity_helper("products"), entity_helper("customers"), entity_helper("coupons"), or entity_dao(name).
- Keep test-owned resources within the shared ownership and cleanup lifecycle. A helper call by itself does not replace fixture-based resource registration.
- Avoid creating a Customer or Coupon unless the Order scenario needs that relationship.

Most tests under tests/orders/ should use order_helper and orders_dao for Order behavior.

---

## ⚙️ Advanced / framework-level access (use sparingly)

Framework-level fixtures are available for special cases:

- entity_helper("orders")
- entity_dao("orders")
- all_resources

Intended uses:

- Cross-domain tests.
- Parametrized tests spanning multiple entities.
- Framework or infrastructure validation.

Most Order tests should use order_helper and orders_dao instead of accessing all_resources directly.

---

## 🧭 Cheat Sheet: order_helper vs entity_helper("orders")

### ✅ Use order_helper when…

- You are writing an Order-domain test under tests/orders/.
- The test is about Order behavior or validation.
- You want the simplest domain-scoped API interface.

### 🔁 Use entity_helper("orders") when…

- A test outside the Orders domain needs generic Order helper access.
- You are writing a parametrized test across entities.
- The test is framework or infrastructure validation.

### 🚫 Do NOT do this

```python
from tests.orders.conftest import order_helper
```

Use pytest fixture injection instead of importing fixtures from a test package.

### 🧠 Rule of thumb

- If the test is about Order behavior, use order_helper.
- If the test needs Order database records, use orders_dao.
- If a valid Order is needed as setup, use create_valid_order with an existing Product.
- If the test needs direct HTTP control, use order_api_raw.
- If another domain needs generic Order access, use entity_helper("orders").

When in doubt, default to the simplest fixture that matches the test's purpose.

---

## 🧠 Key principles

- OrderFactory and OrderBuilder prepare creation data; they do not create resources.
- An Order requires an existing Product line item; the Order fixture does not create that Product.
- OrderProvisioner crosses the system boundary; create_valid_order validates setup and registers ownership.
- OrderStateBuilder prepares partial state for an existing Order.
- Helpers orchestrate API operations; validators check supplied response or database data.
- Tests own the expected HTTP status and scenario-specific behavior assertions.
- Use OrdersDAO for database reads and Order DB validators for API/database comparisons.
- Cleanup is automatic for registered resources; do not bypass or duplicate it.
- Cross-domain access goes through framework fixtures rather than imports from another test package.

---

## 🧭 Related Documentation

This guide covers Orders-specific fixtures, test-data patterns, and testing conventions.

For framework-wide guidance, see:

- README_TEST_DEVELOPMENT_GUIDE.md — how to write tests in this framework.
- README_TEST_DATA_ARCHITECTURE.md — test-data generation, state preparation, provisioning, ownership, and cleanup.
- README_ARCHITECTURE.md — framework architecture.
- README_API_CLIENT.md — API client and endpoint-wrapper responsibilities.
- README_VALIDATORS.md — reusable validation patterns.
- README_CUSTOMERS.md, README_PRODUCTS.md, and README_COUPONS.md — related entity team guides.
