# 🧪 Test Development Guide — TestEcommerceAPI

A comprehensive guide for writing tests in the TestEcommerceAPI framework. Designed for **QA engineers**, **developers**, and **new contributors**.

---

## Prerequisites

Before reading this guide, you should already know:

- **Basic Python** — variables, functions, classes, imports
- **Basic pytest** — fixtures, markers, assertions, test discovery
- **Basic REST APIs** — endpoints, requests, responses
- **HTTP methods** — GET, POST, PUT, DELETE, status codes

If you're new to pytest, the [pytest documentation](https://docs.pytest.org/) is an excellent resource.

---

## Related Documentation

This guide is part of a larger documentation ecosystem:

- **[README_FRAMEWORK_OVERVIEW.md](README_FRAMEWORK_OVERVIEW.md)** — High-level architecture and design principles
- **[README_API_CLIENT.md](README_API_CLIENT.md)** — Implementation details of HttpClient, APIClient, and HttpResponse
- **[README_QA_DEVELOPER_ONBOARDING.md](README_QA_DEVELOPER_ONBOARDING.md)** — Getting started as a QA engineer or developer
- **[README_CI_ARCHITECTURE.md](README_CI_ARCHITECTURE.md)** — CI/CD pipeline design and execution

---

## 📋 Table of Contents

1. [Introduction](#introduction)
2. [Who This Guide Is For](#who-this-guide-is-for)
3. [Testing Philosophy](#testing-philosophy)
4. [Framework Architecture (High Level)](#framework-architecture-high-level)
5. [How a Request Flows Through the Framework](#how-a-request-flows-through-the-framework)
6. [Test Lifecycle](#test-lifecycle)
7. [Test Structure & Organization](#test-structure--organization)
8. [Marker Strategy (Standardized)](#marker-strategy-standardized)
9. [Choosing the Right Abstraction](#choosing-the-right-abstraction)
10. [Writing Happy-Path Tests](#writing-happy-path-tests)
11. [Writing Negative Tests](#writing-negative-tests)
12. [Validation Pipeline](#validation-pipeline)
13. [Fixtures (Gatekeepers)](#fixtures-gatekeepers)
14. [Helpers](#helpers)
15. [Validators](#validators)
16. [Integration Tests](#integration-tests)
17. [Shared Framework Suites](#shared-framework-suites)
18. [Performance Tests](#performance-tests)
19. [CI Strategy](#ci-strategy)
20. [Common Mistakes](#common-mistakes)
21. [Best Practices](#best-practices)
22. [Golden Rules](#golden-rules)
23. [Quick Reference / Cheat Sheet](#quick-reference--cheat-sheet)

---

## Introduction

The TestEcommerceAPI framework provides a **standardized, enterprise-grade approach** to API testing.

This guide teaches you:

- ✅ How to write tests that are **readable and stable**
- ✅ How to use framework helpers and validators correctly
- ✅ How to organize tests for scalability
- ✅ How to debug failures effectively
- ✅ How to participate in CI/CD pipelines

**Goal:** Write better tests faster.

---

## Who This Guide Is For

| Role | What You Need |
|------|--------------|
| **QA Engineers** | Domain-driven test organization, marker strategy, fixture patterns |
| **Developers** | Integration testing, negative tests, validation pipeline |
| **New Contributors** | Start with Section 10 (Happy-Path Tests), use fixtures by default |
| **Tech Leads** | CI strategy, architecture layers, performance benchmarking |

---

## Testing Philosophy

### ✅ Tests SHOULD Be

- **Readable** — clear intent, self-documenting
- **Stable** — pass consistently in CI
- **Focused** — validate one business behavior
- **Independent** — create their own data
- **Isolated** — query only their own data

### ❌ Tests SHOULD NOT Be

- Orchestrating complex workflows (use helpers)
- Validating response structure manually (use validators)
- Calling low-level transport code (use APIClient)

The framework provides abstractions to handle these concerns.

---

## Framework Architecture (High Level)

```
HttpClient → APIClient → HttpResponse → API → Helpers → Validators → Tests
```

| Layer | Responsibility |
|-------|-----------------|
| **HttpClient** | Transport + timeout + retries |
| **APIClient** | Request orchestration, logging, retry logic |
| **HttpResponse** | Parsed + normalized response object |
| **API** | Endpoint definitions (thin, no logic) |
| **Helper** | Business orchestration, optional abstraction |
| **Validator** | Schema + business logic assertions |
| **Test** | Business behavior validation |

**Key Principle:** Transport layers do NOT validate. Validation happens in fixtures, validators, and tests.

**Note:** This is a conceptual view only. Implementation details are documented in `README_API_CLIENT.md`. This guide focuses on **writing tests**, not framework internals.

---

## How a Request Flows Through the Framework

Understanding the request flow helps you debug issues and write better tests.

```
┌─────────────────────────────────────────────────────────────────┐
│                          TEST STARTS                             │
│                    test_get_product_by_id()                     │
└────────────────────────────┬──────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FIXTURE CREATES DATA                          │
│              create_valid_product() is called                   │
│        - Calls helper to create product on API                  │
│        - Validates response (status 201)                        │
│        - Extracts + validates JSON (Pydantic)                   │
│        - Registers cleanup                                       │
│        - Returns clean dict: {id, name, price, ...}             │
└────────────────────────────┬──────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    TEST CALLS HELPER                             │
│         response = product_helper.get_product_by_id()           │
│                helper._calls_api()                              │
└────────────────────────────┬──────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     HELPER CALLS API                             │
│            APIClient.get("/products/{id}")                      │
└────────────────────────────┬──────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   APICLIENT ORCHESTRATES                         │
│        - Prepares the request                                    │
│        - Logs the request                                        │
│        - Applies retry policy                                    │
│        - Calls HttpClient                                        │
└────────────────────────────┬──────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    HTTPCLIENT SENDS                              │
│    - Establishes connection to WooCommerce API                  │
│    - Sends HTTP GET request                                     │
│    - Enforces timeout (default: 30s)                            │
│    - Handles low-level HTTP concerns                            │
└────────────────────────────┬──────────────────────────────────────┘
                             │
                             ▼
         ╔════════════════════════════════════════════╗
         ║     🌐 WooCommerce API Responds 🌐         ║
         ║                                            ║
         ║   HTTP 200                                 ║
         ║   Content-Type: application/json           ║
         ║                                            ║
         ║   {                                        ║
         ║     "id": 456,                             ║
         ║     "name": "Test Product",                ║
         ║     "price": "99.99",                      ║
         ║     ...                                    ║
         ║   }                                        ║
         ╚════════════════════════════════════════════╝
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  HTTPCLIENT RECEIVES                             │
│      - Returns raw requests.Response                            │
│      - Status code, headers, body                               │
└────────────────────────────┬──────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                 APICLIENT NORMALIZES                             │
│      - Wraps raw response in HttpResponse                       │
│      - Parses JSON safely                                        │
│      - Validates content-type                                   │
│      - Returns: HttpResponse(status_code=200, json={...})      │
└────────────────────────────┬──────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  TEST RECEIVES RESPONSE                          │
│              response = HttpResponse(...)                       │
└────────────────────────────┬──────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   TEST VALIDATES (Layer 1)                       │
│                   Transport Layer Validation                    │
│                                                                  │
│              assert response.status_code == 200                 │
└────────────────────────────┬──────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   TEST VALIDATES (Layer 2)                       │
│                   Schema Layer Validation                        │
│                                                                  │
│           product_model = ProductModel(**response.json)         │
│         (Pydantic validates all fields exist + correct types)   │
└────────────────────────────┬──────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   TEST VALIDATES (Layer 3)                       │
│                   Business Logic Validation                      │
│                                                                  │
│              assert product_model.price > 0                     │
│              assert product_model.name is not None              │
└────────────────────────────┬──────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ✅ TEST PASSES                                │
└────────────────────────────┬──────────────────────────────────────┘
                             │
                             ▼
┌────────────���────────────────────────────────────────────────────┐
│                    CLEANUP EXECUTES                              │
│              Fixture cleanup code runs                          │
│              - Calls product_helper.delete_product(id)          │
│              - Data is removed from WooCommerce                 │
│              - No leftover data                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Key Takeaway

Each layer has a specific responsibility. Tests don't worry about HTTP details—the framework handles them. Tests only assert **business logic**.

---

## Test Lifecycle

```
Test Created
    ↓
Test Marked (domain + execution tier + type)
    ↓
Test Runs in CI (via marker filters)
    ↓
Fixture Creates Data (with validation)
    ↓
Test Calls Helper or API
    ↓
Request Flows Through Framework (see above)
    ↓
Response Validated (status → schema → business logic)
    ↓
Database Verified (if integration)
    ↓
Cleanup Executed (automatic via fixture)
    ↓
Test Passes or Fails
```

---

## Test Structure & Organization

### Directory Organization

```
tests/
├── customers/
│   ├── test_create_customer.py
│   ├── test_get_customer.py
│   ├── integration/
│   └── performance/
├── orders/
│   ├── test_create_order.py
│   ├── integration/
│   └── performance/
├── products/
├── coupons/
└── shared/
    ├── preflight/
    ├── contract/
    └── security/
```

✅ **Domain-driven** (matches microservices / business entities)
✅ **Enables team ownership** (each team owns a domain)
✅ **Scales easily** (add new domains without refactoring)

❌ **DO NOT** reorganize by smoke/regression/integration folders

Each business entity owns its own smoke, integration, regression, and performance tests. The `shared/` directory is reserved exclusively for **framework-level test suites**.

---

## Marker Strategy (Standardized)

Markers organize tests for selective execution. Use up to 3 markers per test (excluding domain).

### Marker Hierarchy

```
customers/                    orders/
├── test_create.py           ├── test_create.py
│   ├── @pytest.mark.smoke   │   ├── @pytest.mark.smoke
│   ├── @pytest.mark.integration
│   └── @pytest.mark.regression
├── performance/             ├── performance/
│   └── @pytest.mark.performance
│                            shared/
                            ├── preflight/
                            │   └── @pytest.mark.preflight
                            ├── contract/
                            │   └── @pytest.mark.contract
                            └── security/
                                └── @pytest.mark.security
```

### 1. Domain Markers (Auto-Applied)

Automatically applied via `conftest.py` based on directory.

```
customers, orders, products, coupons, shared
```

✅ Do NOT manually add domain markers.

### 2. Execution Tier

| Marker | Meaning | Speed | Scope | When |
|--------|---------|-------|-------|------|
| `smoke` | Critical API health | ⚡ Fast | Broad, shallow | Every commit (PR gate) |
| `sanity` | Functional checks on recent changes | 🏃 Moderate | Narrow, deep | After smoke passes |
| `regression` | Full coverage | 🐢 Slow | Comprehensive | Nightly |

#### 🔥 Smoke Tests MUST Be:
- **Fast** (< 5 min total suite)
- **Deterministic** (always pass on healthy API)
- **Isolated** (no flaky network timeouts)
- Broad, shallow checks of critical flows

#### 📍 Sanity Tests MUST Be:
- **Narrow** (focus on recently changed modules only)
- **Deep** (verify logic in detail)
- **Targeted** (run after smoke passes)

### 3. Test Type

| Marker | Meaning |
|--------|---------|
| `integration` | API + DB validation required |
| `contract` | Schema + transport validation |
| `negative` | Invalid input / error scenarios |
| `e2e` | Multi-step workflow validation |

### 4. Specialized Markers

| Marker | Purpose |
|--------|---------|
| `performance` | Benchmark / timing validation |
| `security` | Auth + access control |
| `preflight` | Framework bootstrap validation |
| `bulk` | Bulk operation testing |

### Marker Rules

✅ Max 2–3 markers per test (excluding domain)
✅ Domain markers auto-applied (no manual addition)
✅ Use consistent naming (`negative`, NOT `negative_test`)
✅ Uppercase for pytest.mark syntax

### Example

```python
import pytest

pytestmark = [
    pytest.mark.integration,
    pytest.mark.regression
]

def test_order_persisted_to_database(order_helper, create_valid_order):
    """Verify order appears in DB after API call."""
    order = create_valid_order()
    db_order = get_order_from_db(order["id"])
    assert db_order.total == order["total"]
```

---

## Choosing the Right Abstraction

One of the most important skills in this framework: **when to use what**.

### 📊 Decision Matrix

| Scenario | Use | Returns | Example |
|----------|-----|---------|---------|
| **Happy path** (normal operation) | Fixture | `dict` | `product = create_valid_product()` |
| **Need status / headers** (debug) | Helper (response mode) | `HttpResponse` | `response = product_helper.create_product(return_http_response=True)` |
| **Invalid input** (negative test) | Helper (response mode) | `HttpResponse` | `response = product_helper.create_product(price=-10, return_http_response=True)` |
| **Deep debugging** (rare) | `request_raw()` | `requests.Response` | `resp, _ = APIClient.request_raw(...)` |

### Mental Model

```
Fixture         → validated dict (safe, clean)
Helper          → optional HttpResponse (flexible)
request_raw()   → debugging only (low-level)
```

### ❌ DO NOT Mix Abstraction Levels

```python
# ❌ WRONG: Fixture can't have status_code
product = create_valid_product()
assert product.status_code == 201  # ERROR: dict has no status_code

# ✅ CORRECT: Use helper for response metadata
response = product_helper.create_product(return_http_response=True)
assert response.status_code == 201
```

---

## Writing Happy-Path Tests

Happy-path tests verify normal, successful behavior. They should be **80% of your test suite**.

### Pattern: Arrange → Act → Assert

```python
def test_get_product_by_id(product_helper, create_valid_product):
    """Verify product can be retrieved by ID."""
    
    # Arrange
    product = create_valid_product()
    
    # Act
    response = product_helper.get_product_by_id(
        product["id"],
        return_http_response=True
    )
    
    # Assert
    product_model = assert_product_retrieved_successfully(response)
    assert_product_identity(product_model, product["id"], product["name"])
```

### For Juniors: Start Simple

```python
def test_product_has_price(create_valid_product):
    """Verify product price is captured."""
    product = create_valid_product()
    assert product["price"]
    assert float(product["price"]) > 0
```

### Tips

✅ Use fixtures to create data (no setup code)
✅ Test one business behavior per test
✅ Name tests with `test_<what_you_are_testing>`
✅ Add docstring explaining the intent

---

## Writing Negative Tests

Negative tests verify **error handling and boundary conditions**. They should be **10–20% of your test suite**.

### Pattern: Helper + HttpResponse

Always use `return_http_response=True` for negative tests:

```python
def test_create_coupon_with_invalid_discount(coupon_helper):
    """Verify API rejects invalid discount percentage."""
    
    response = coupon_helper.create_coupon(
        payload={"discount_percent": 150},  # Invalid: > 100%
        return_http_response=True
    )
    
    assert response.status_code == 400
    assert response.json["error"]["code"] == "INVALID_DISCOUNT"
```

### What to Validate

✅ HTTP status code (400, 401, 403, 404, 500, etc.)
✅ Error message structure (using validators)
✅ Business rule enforcement (e.g., "discount cannot exceed 100%")

### ❌ DO NOT

❌ Use fixtures for negative tests (they validate + pass, making negative tests impossible)
❌ Mix positive and negative assertions in one test
❌ Test multiple error conditions in one test

---

## Validation Pipeline

Validation happens in **strict order**. Each layer builds on the previous.

```
Transport Validation        (HTTP status code)
    ↓
Schema Validation           (JSON structure)
    ↓
Business Validation         (business rules)
    ↓
Database Validation         (data persistence)
```

### Layer 1: Transport Validation

```python
assert response.status_code == 201
```

### Layer 2: Schema Validation

```python
product_model = ProductModel(**response.json)
```

### Layer 3: Business Validation

```python
assert product_model.price > 0
```

### Layer 4: Database Validation

```python
@pytest.mark.integration
def test_product_in_database(create_valid_product):
    product = create_valid_product()
    db_product = get_product_from_db(product["id"])
    assert db_product.name == product["name"]
```

### ⚠️ Important

- ✅ Validate in order
- ✅ Fail fast (stop at first layer failure)
- ❌ Never skip layers

---

## Fixtures (Gatekeepers)

Fixtures act as **gatekeepers**: they create valid data, validate it, clean it up, and return a clean dictionary.

### Fixture Responsibilities

✅ Call the API (via helper)
✅ Validate HTTP status (transport layer)
✅ Extract JSON response
✅ Validate schema (Pydantic)
✅ Register cleanup
✅ Return a clean `dict`

### Fixture Constraints

✅ **ALWAYS** return `dict`
✅ **ALWAYS** return valid data
✅ **NEVER** return `HttpResponse`
✅ **NEVER** return invalid objects

### Example: Fixture Template

```python
@pytest.fixture
def create_valid_order(order_helper):
    """Factory fixture: creates and validates an order."""
    
    created_orders = []
    
    def _create(**overrides):
        # Arrange
        payload = {
            "customer_id": 123,
            "total": "99.99",
            **overrides
        }
        
        # Act
        response = order_helper.create_order(
            payload=payload,
            return_http_response=True
        )
        
        # Assert (Layer 1: Transport)
        assert response.status_code == 201, \
            f"Expected 201, got {response.status_code}: {response.json}"
        
        # Assert (Layer 2: Schema)
        try:
            order_model = OrderModel(**response.json)
        except ValidationError as e:
            raise AssertionError(f"Invalid schema: {e}")
        
        # Extract clean dict
        order_dict = {
            "id": order_model.id,
            "total": order_model.total,
            "status": order_model.status,
        }
        
        # Register cleanup
        created_orders.append(order_dict["id"])
        
        return order_dict
    
    yield _create
    
    # Cleanup
    for order_id in created_orders:
        order_helper.delete_order(order_id)
```

### Usage in Tests

```python
def test_order_total_is_captured(create_valid_order):
    """Verify order total is saved."""
    order = create_valid_order()
    assert order["total"] == "99.99"
```

---

## Helpers

Helpers **orchestrate business logic** and bridge the gap between tests and the API layer.

### Helper Responsibilities

✅ Call APIs (via `APIClient`)
✅ Orchestrate multi-step workflows
✅ Combine API + DB logic
✅ Return optional `HttpResponse` (when needed)

### Helper Constraints

❌ DO NOT assert inside helpers
❌ DO NOT validate (that's the fixture's job)
❌ DO NOT return invalid data

### When to Use Helpers

✅ Retrieving data
✅ Creating data (fixtures use helpers)
✅ Multi-step workflows (login + create order + verify)

---

## Validators

Validators **assert structure and business logic** without fetching data.

### Validator Responsibilities

✅ Validate schema (Pydantic models)
✅ Validate business logic
✅ Validate DB consistency

### Validator Constraints

❌ DO NOT fetch data (pass it in)
❌ DO NOT call helpers

### Pattern: Fetch → Validate

```python
# Fetch data (in fixture or test)
response = product_helper.get_product(return_http_response=True)

# Validate schema
product_model = ProductModel(**response.json)

# Validate business logic
assert_product_has_valid_price(product_model)
```

---

## Integration Tests

Integration tests verify **API + Database consistency**.

### When to Mark as Integration

If a test uses a DAO (Data Access Object) to query the database:

```python
@pytest.mark.integration
def test_order_persisted_to_database(create_valid_order):
    """Verify order data is saved to database."""
    order = create_valid_order()
    db_order = get_order_from_db(order["id"])
    assert db_order.total == order["total"]
```

### When NOT to Mark as Integration

If a test does **not** query persistent state (database, cache, message queue, etc.), it should generally **not** be marked as an integration test.

```python
# ❌ NOT integration (no DB query)
@pytest.mark.smoke
def test_order_response_has_total(create_valid_order):
    """Verify response contains total."""
    order = create_valid_order()
    assert order["total"]  # Only checks response, no DB query
```

---

## Shared Framework Suites

Shared framework suites validate **infrastructure, security, and environment behavior** before running entity-specific tests.

These suites execute **once for the framework**, not per entity. They use dynamic discovery to cover all supported API entities.

### Directory Structure

```
tests/shared/
├── preflight/
│   └── test_logging_globals.py
├── contract/
│   ├── test_api_connectivity.py
│   └── test_response_format.py
└── security/
    ├── test_authentication_matrix.py
    └── test_authentication_success.py
```

### Preflight ⚡

**Framework-level validation only.** Verify the test environment and framework configuration.

**Coverage:** Logging configuration, pytest marker sanity, configuration parsing, framework bootstrap validation.

**Constraints:** Must NOT call live APIs, require Docker, OAuth, databases, or WooCommerce.

### Contract 📋

**API contract and transport validation.** Verify APIs respond correctly.

**Coverage:** API connectivity, HTTP status, response format, content-type, schema validation, serialization behavior.

**Discovery:** Framework entities are discovered automatically.

### Security 🔒

**Framework-level authentication validation.** Verify authentication works before business logic.

**Coverage:** Valid OAuth, invalid OAuth rejection, authentication matrix (all entities), GET/POST/PUT/DELETE validation, error schema validation.

**Discovery:** Framework entities are discovered automatically.

### Performance (Entity-Specific)

Unlike Preflight, Contract, and Security, **performance tests belong to each business entity** because every API has different expectations.

```
tests/
├── customers/performance/
├── orders/performance/
└── products/performance/
```

Each entity owns benchmark scenarios, request parameters, performance thresholds, and benchmark iterations.

---

## Performance Tests

Performance tests verify **request timing and throughput** match expectations.

### Key Principle

**Performance expectations vary by entity.** A product lookup should be < 100ms, but a bulk export might need 30 seconds.

### Location

Performance tests live with their entity, NOT in `tests/shared/`:

```
tests/products/performance/test_product_retrieval_time.py
```

### Example

```python
@pytest.mark.performance
def test_product_retrieval_under_100ms(create_valid_product):
    """Verify product retrieval stays under 100ms."""
    product = create_valid_product()
    
    start = time.perf_counter()
    response = product_helper.get_product_by_id(product["id"])
    duration_ms = (time.perf_counter() - start) * 1000
    
    assert response.status_code == 200
    assert duration_ms < 100
```

---

## CI Strategy

CI pipelines execute tests in **stages**, from fast feedback to comprehensive validation.

### Workflow Architecture

```
┌─────────────────────────────────────────────────┐
│  GitHub Workflow: Fast Pipeline (PR Gate)       │
│  ✓ Preflight                                    │
│  ✓ Smoke                                        │
│  ✓ Sanity                                       │
│  ⏱️  ~ 5 minutes                                │
│  🎯 If PASS → proceed to Full Validation        │
└─────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────┐
│  GitHub Workflow: Full Validation               │
│  ✓ Contract                                     │
│  ✓ Integration                                  │
│  ✓ Regression                                   │
│  ⏱️  ~ 15 minutes                               │
│  🎯 If PASS → safe to merge                     │
└─────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────┐
│  GitHub Workflow: Nightly (Deep Coverage)       │
│  ✓ Regression (comprehensive)                   │
│  ⏱️  ~ 60 minutes                               │
│  🎯 Catches edge cases                          │
└─────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────┐
│  GitHub Workflow: Security (Weekly)             │
│  ✓ Security                                     │
│  ⏱️  ~ 10 minutes                               │
│  🎯 Auth validation                             │
└─────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────┐
│  GitHub Workflow: Performance (Scheduled)       │
│  ✓ Performance                                  │
│  ⏱️  ~ 30 minutes                               │
│  🎯 Benchmarks + SLA checks                     │
└─────────────────────────────────────────────────┘
```

### Command Reference

| Pipeline | Command | Time | Purpose |
|----------|---------|------|---------|
| **PR Gate** | `pytest -m "smoke or sanity or preflight"` | ~5 min | Fast feedback |
| **Full** | `pytest -m "not performance and not security"` | ~15 min | Safe to merge |
| **Nightly** | `pytest -m regression` | ~60 min | Deep coverage |
| **Security** | `pytest -m security` | ~10 min | Auth validation |
| **Performance** | `pytest -m performance` | ~30 min | Benchmarks |

---

## Common Mistakes

### ❌ Mistake 1: Mixing Abstraction Levels

```python
# WRONG: Fixtures return dict, not HttpResponse
product = create_valid_product()
assert product.status_code == 201  # ← AttributeError
```

**Fix:** Use helper for response metadata

```python
# RIGHT
response = product_helper.create_product(return_http_response=True)
assert response.status_code == 201
```

---

### ❌ Mistake 2: Validating in Helpers

```python
# WRONG: Helpers should not assert
def create_product(payload):
    response = APIClient.post("/products", json=payload)
    assert response.status_code == 201  # ← NO!
    return response.json
```

**Fix:** Let fixtures validate

```python
# RIGHT: Helpers just orchestrate
def create_product(payload):
    return APIClient.post("/products", json=payload)
```

---

### ❌ Mistake 3: Asserting Inside Helpers

Let tests assert, not helpers.

**Fix:** Return data, let test assert

```python
def get_product(product_id):
    return APIClient.get(f"/products/{product_id}")

def test_get_product():
    response = product_helper.get_product("123")
    assert response.status_code == 200
```

---

### ❌ Mistake 4: Using Fixtures for Negative Tests

```python
# WRONG: Breaks fixture contract
@pytest.fixture
def create_invalid_product():
    response = product_helper.create_product({"price": -10})
    return response  # ← Fixture returning HttpResponse!
```

**Fix:** Use helper directly

```python
# RIGHT
def test_invalid_price(product_helper):
    response = product_helper.create_product(
        {"price": -10},
        return_http_response=True
    )
    assert response.status_code == 400
```

---

### ❌ Mistake 5: Manual JSON Validation

```python
# WRONG: Repeating schema checks
json_data = response.json
assert json_data["id"]
assert json_data["name"]
assert isinstance(json_data["price"], str)
```

**Fix:** Use Pydantic

```python
# RIGHT: One validation, all checked
product_model = ProductModel(**response.json)
```

---

### ❌ Mistake 6: Using `request_raw()` in Normal Tests

**Fix:** Use helper

```python
# ONLY for debugging:
resp, _ = APIClient.request_raw(method="post", endpoint="/products", payload={...})

# Normal tests use helpers:
response = product_helper.create_product()
```

---

### ❌ Mistake 7: Reorganizing Test Folders

Don't create smoke/regression/integration folders. Use markers instead.

**Fix:** Domain-driven organization

```
tests/products/
├── test_create_product.py
│   └── @pytest.mark.smoke
├── test_update_product.py
│   └── @pytest.mark.regression
└── integration/
    └── test_database_consistency.py
        └── @pytest.mark.integration
```

---

### ❌ Mistake 8: Leaving Test Data Behind

**Fix:** Use fixtures with cleanup

```python
@pytest.fixture
def create_valid_product(product_helper):
    created_ids = []
    
    def _create():
        response = product_helper.create_product()
        created_ids.append(response["id"])
        return response
    
    yield _create
    
    for product_id in created_ids:
        product_helper.delete_product(product_id)
```

---

## Best Practices

### 1. Start with Happy-Path Tests

Write ~80% happy-path tests (positive cases).

```python
def test_product_can_be_created(create_valid_product):
    product = create_valid_product()
    assert product["id"]
```

### 2. Add Negative Tests for Error Cases

Add ~10-20% negative tests (error scenarios).

```python
def test_invalid_price_rejected(product_helper):
    response = product_helper.create_product(
        {"price": -10},
        return_http_response=True
    )
    assert response.status_code == 400
```

### 3. Use Fixtures for Setup

```python
product = create_valid_product()  # Clean, safe
```

### 4. Use Helpers for Workflows

```python
customer = login_customer(credentials)
order = create_order_for_customer(customer)
verify_order_in_database(order)
```

### 5. Use Validators for Assertions

```python
product_model = assert_product_retrieved_successfully(response)
assert_product_has_valid_price(product_model)
```

### 6. Keep Tests Focused

One behavior per test.

```python
# ✅ RIGHT: Separate concerns
def test_create_product(create_valid_product):
    product = create_valid_product()
    assert product["name"]

def test_update_product_name(create_valid_product):
    product = create_valid_product()
    updated = product_helper.update_product(product["id"], {"name": "New Name"})
    assert updated["name"] == "New Name"
```

### 7. Use Meaningful Names

```python
# ✅ Clear
def test_product_name_is_required():
    pass
```

### 8. Run Tests Locally

```bash
pytest tests/products/test_create_product.py -v
pytest -m smoke -v
```

---

## Golden Rules

1. **Fixtures return validated data** (dict, not HttpResponse)
2. **Helpers orchestrate** (no assertions)
3. **Validators validate** (no data fetching)
4. **Tests verify business logic** (not transport)
5. **Keep tests simple** (Arrange → Act → Assert)
6. **One behavior per test** (focused scope)
7. **Create your own data** (independence)
8. **Clean up after yourself** (via fixtures)
9. **Use markers correctly** (max 3 per test)
10. **Fail fast** (validate in order)

---

## Quick Reference / Cheat Sheet

### When to Use What

| Need | Use | Example |
|------|-----|---------|
| Create test data | Fixture | `product = create_valid_product()` |
| Call API | Helper | `product_helper.get_product(id)` |
| Validate schema | Pydantic | `ProductModel(**response.json)` |
| Check status code | Helper + response mode | `response = helper.create(..., return_http_response=True)` |
| Debug issue | `request_raw()` | `APIClient.request_raw(...)` |

### Marker Quick Reference

```python
@pytest.mark.smoke  # Critical + fast
@pytest.mark.sanity  # Recent changes
@pytest.mark.regression  # Full coverage
@pytest.mark.integration  # API + DB
@pytest.mark.negative  # Error scenarios
@pytest.mark.performance  # Timing checks
```

### Common Test Patterns

#### Happy Path

```python
def test_product_retrieval(create_valid_product, product_helper):
    product = create_valid_product()
    response = product_helper.get_product_by_id(product["id"], return_http_response=True)
    assert response.status_code == 200
```

#### Negative Test

```python
def test_invalid_price_rejected(product_helper):
    response = product_helper.create_product({"price": -10}, return_http_response=True)
    assert response.status_code == 400
```

#### Integration Test

```python
@pytest.mark.integration
def test_product_in_database(create_valid_product):
    product = create_valid_product()
    db_product = get_product_from_db(product["id"])
    assert db_product.name == product["name"]
```

#### Performance Test

```python
@pytest.mark.performance
def test_product_retrieval_fast(create_valid_product):
    product = create_valid_product()
    start = time.perf_counter()
    product_helper.get_product_by_id(product["id"])
    assert (time.perf_counter() - start) * 1000 < 100
```

### Fixture Factory Template

```python
@pytest.fixture
def create_valid_order(order_helper):
    created_ids = []
    
    def _create(**overrides):
        payload = {"customer_id": 123, "total": "99.99", **overrides}
        response = order_helper.create_order(payload, return_http_response=True)
        assert response.status_code == 201
        order_model = OrderModel(**response.json)
        created_ids.append(order_model.id)
        return {"id": order_model.id, "total": order_model.total}
    
    yield _create
    
    for order_id in created_ids:
        order_helper.delete_order(order_id)
```

---

## Conclusion

The TestEcommerceAPI framework is:

✅ **Enterprise-ready** — designed for teams and scale
✅ **Scalable** — domain-driven organization
✅ **Cleanly designed** — clear separation of concerns
✅ **Beginner-friendly** — fixtures make simple tests simple

**Your job:** Write tests that validate business behavior.

**The framework's job:** Handle transport, schema validation, retry logic, and cleanup.

### Final Advice

Ask yourself:

> "Does this help me write better tests faster?"

If not → skip it.

---

**Happy testing! 🚀**
