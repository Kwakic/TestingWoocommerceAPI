# 🧪 Test Development Guide — TestEcommerceAPI (Enterprise)

A comprehensive guide for writing tests in the TestEcommerceAPI framework. Designed for **QA engineers**, **developers**, and **new contributors**.

---

## 📋 Table of Contents

1. [Introduction](#introduction)
2. [Who This Guide Is For](#who-this-guide-is-for)
3. [Testing Philosophy](#testing-philosophy)
4. [Framework Architecture (High Level)](#framework-architecture-high-level)
5. [Test Lifecycle](#test-lifecycle)
6. [Test Structure & Organization](#test-structure--organization)
7. [Marker Strategy (Standardized)](#marker-strategy-standardized)
8. [Choosing the Right Abstraction](#choosing-the-right-abstraction)
9. [Writing Happy-Path Tests](#writing-happy-path-tests)
10. [Writing Negative Tests](#writing-negative-tests)
11. [Validation Pipeline](#validation-pipeline)
12. [Fixtures (Gatekeepers)](#fixtures-gatekeepers)
13. [Helpers](#helpers)
14. [Validators](#validators)
15. [Integration Tests](#integration-tests)
16. [Shared Framework Suites](#shared-framework-suites)
17. [Performance Tests](#performance-tests)
18. [CI Strategy](#ci-strategy)
19. [Common Mistakes](#common-mistakes)
20. [Best Practices](#best-practices)
21. [Golden Rules](#golden-rules)
22. [Quick Reference / Cheat Sheet](#quick-reference--cheat-sheet)

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
| **New Contributors** | Start with Section 9 (Happy-Path Tests), use fixtures by default |
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

def test_customer_created_in_database(customer_helper, create_valid_customer):
    """Verify customer appears in DB after API call."""
    
    # Arrange
    customer = create_valid_customer()
    
    # Act
    db_customer = get_customer_from_db(customer["id"])
    
    # Assert
    assert db_customer.email == customer["email"]
```

---

## Choosing the Right Abstraction

One of the most important skills in this framework: **when to use what**.

### 📊 Decision Matrix

| Scenario | Use | Returns | Example |
|----------|-----|---------|---------|
| **Happy path** (normal operation) | Fixture | `dict` | `customer = create_valid_customer()` |
| **Need status / headers** (debug) | Helper (response mode) | `HttpResponse` | `response = customer_helper.create_customer(return_http_response=True)` |
| **Invalid input** (negative test) | Helper (response mode) | `HttpResponse` | `response = customer_helper.create_customer(email="invalid", return_http_response=True)` |
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
customer = create_valid_customer()
assert customer.status_code == 201  # ERROR: dict has no status_code

# ✅ CORRECT: Use helper for response metadata
response = customer_helper.create_customer(return_http_response=True)
assert response.status_code == 201
```

---

## Writing Happy-Path Tests

Happy-path tests verify normal, successful behavior. They should be **80% of your test suite**.

### Pattern: Arrange → Act → Assert

```python
def test_get_customer_by_id(customer_helper, create_valid_customer):
    """Verify customer can be retrieved by ID."""
    
    # Arrange
    customer = create_valid_customer()
    
    # Act
    response = customer_helper.get_customer_by_id(
        customer["id"],
        return_http_response=True
    )
    
    # Assert
    customer_model = assert_customer_retrieved_successfully(response)
    
    assert_customer_identity(
        customer_model,
        customer["id"],
        customer["email"]
    )
```

### For Juniors: Start Simple

```python
def test_customer_has_email():
    """Verify customer email is captured."""
    
    # Create data
    customer = create_valid_customer()
    
    # Check it
    assert customer["email"]
    assert "@" in customer["email"]
```

### Tips

✅ Use fixtures to create data (no setup code)
✅ Test one business behavior per test
✅ Name tests with `test_<what_you_are_testing>`
✅ Add docstring explaining the intent
✅ Use validators for complex assertions

---

## Writing Negative Tests

Negative tests verify **error handling and boundary conditions**. They should be **10–20% of your test suite**.

### Pattern: Helper + HttpResponse

Always use `return_http_response=True` for negative tests:

```python
def test_create_customer_with_invalid_email():
    """Verify API rejects invalid email."""
    
    # Arrange & Act
    response = customer_helper.create_customer(
        payload={"email": "invalid"},
        return_http_response=True
    )
    
    # Assert
    assert response.status_code == 400
    assert response.json["error"]["code"] == "INVALID_EMAIL"
```

### What to Validate

✅ HTTP status code (400, 401, 403, 404, 500, etc.)
✅ Error message structure (using validators)
✅ Business rule enforcement (e.g., "email must be unique")

### ❌ DO NOT

❌ Use fixtures for negative tests (they validate + pass, making negative tests impossible)
❌ Mix positive and negative assertions in one test
❌ Test multiple error conditions in one test

---

## Validation Pipeline

Validation happens in **strict order**. Each layer builds on the previous.

```
Transport Validation
    ↓ (status_code OK?)
Schema Validation
    ↓ (JSON structure valid?)
Business Validation
    ↓ (business rules satisfied?)
Database Validation
    ↓ (data persisted correctly?)
```

### Layer 1: Transport Validation

```python
assert response.status_code == 201  # HTTP level
```

### Layer 2: Schema Validation

```python
# Using Pydantic models (strict typing)
customer_model = CustomerModel(**response.json)

# Or using validators
assert_customer_response_schema(response.json)
```

### Layer 3: Business Validation

```python
assert customer_model.email == expected_email
assert customer_model.created_at > datetime.now()
```

### Layer 4: Database Validation

```python
db_customer = get_customer_from_db(customer_model.id)
assert db_customer.email == customer_model.email
```

### ⚠️ Important

- ✅ Validate in order
- ✅ Fail fast (stop at first layer failure)
- ❌ Never skip layers
- ❌ Never validate manually (use validators or Pydantic)

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

### Example: Good Fixture

```python
import pytest
from pydantic import ValidationError

@pytest.fixture
def create_valid_customer(customer_helper):
    """Factory fixture: creates and validates a customer."""
    
    created_customers = []
    
    def _create(**overrides):
        # Arrange
        payload = {
            "email": "customer@example.com",
            "first_name": "Test",
            "last_name": "User",
            **overrides
        }
        
        # Act
        response = customer_helper.create_customer(
            payload=payload,
            return_http_response=True
        )
        
        # Assert (Layer 1: Transport)
        assert response.status_code == 201, \
            f"Expected 201, got {response.status_code}: {response.json}"
        
        # Assert (Layer 2: Schema)
        try:
            customer_model = CustomerModel(**response.json)
        except ValidationError as e:
            raise AssertionError(f"Invalid schema: {e}")
        
        # Extract clean dict
        customer_dict = {
            "id": customer_model.id,
            "email": customer_model.email,
            "first_name": customer_model.first_name,
            "last_name": customer_model.last_name,
        }
        
        # Register cleanup
        created_customers.append(customer_dict["id"])
        
        # Return clean dict
        return customer_dict
    
    yield _create
    
    # Cleanup
    for customer_id in created_customers:
        customer_helper.delete_customer(customer_id)

```

### Usage in Tests

```python
def test_customer_email_is_captured(create_valid_customer):
    """Verify customer email is saved."""
    
    customer = create_valid_customer()
    
    # No HTTP noise, clean dict
    assert customer["email"] == "customer@example.com"
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

### Example: Good Helper

```python
class CustomerHelper:
    """Orchestrates customer API operations."""
    
    def create_customer(self, payload=None, return_http_response=False):
        """Create a customer and optionally return raw response."""
        
        default_payload = {
            "email": "customer@example.com",
            "first_name": "Test",
            "last_name": "User"
        }
        
        final_payload = {**default_payload, **(payload or {})}
        
        response = APIClient.post(
            endpoint="/customers",
            json=final_payload
        )
        
        if return_http_response:
            return response  # HttpResponse object
        
        # Default: return parsed JSON
        return response.json
    
    def get_customer_by_id(self, customer_id, return_http_response=False):
        """Retrieve a customer by ID."""
        
        response = APIClient.get(
            endpoint=f"/customers/{customer_id}"
        )
        
        if return_http_response:
            return response
        
        return response.json
```

### When to Use Helpers

✅ Retrieving data
✅ Creating data (fixtures use helpers)
✅ Multi-step workflows (login + create order + verify)
✅ Complex setup (not suitable for fixtures)

---

## Validators

Validators **assert structure and business logic** without fetching data.

### Validator Responsibilities

✅ Validate schema (Pydantic models)
✅ Validate business logic
✅ Validate DB consistency
✅ Provide clear error messages

### Validator Constraints

❌ DO NOT fetch data (pass it in)
❌ DO NOT call helpers
❌ DO NOT have side effects

### Pattern: Fetch → Validate

```python
# Fetch data
customer_json = response.json

# Validate schema
customer_model = CustomerModel(**customer_json)

# Validate business logic
assert_customer_identity(
    customer_model,
    expected_id,
    expected_email
)
```

### Example: Good Validator

```python
def assert_customer_retrieved_successfully(response):
    """Validate successful customer retrieval response.
    
    Returns:
        CustomerModel: Validated customer object
        
    Raises:
        AssertionError: If response is invalid
    """
    
    # Layer 1: Transport
    assert response.status_code == 200, \
        f"Expected 200, got {response.status_code}"
    
    # Layer 2: Schema
    try:
        customer_model = CustomerModel(**response.json)
    except ValidationError as e:
        raise AssertionError(f"Invalid customer schema: {e}")
    
    return customer_model

def assert_customer_identity(customer_model, expected_id, expected_email):
    """Validate customer identity (business logic).
    
    Args:
        customer_model: CustomerModel instance
        expected_id: Expected customer ID
        expected_email: Expected customer email
    """
    
    assert customer_model.id == expected_id, \
        f"Expected ID {expected_id}, got {customer_model.id}"
    
    assert customer_model.email == expected_email, \
        f"Expected email {expected_email}, got {customer_model.email}"
```

---

## Integration Tests

Integration tests verify **API + Database consistency**.

### When to Mark as Integration

If a test uses a DAO (Data Access Object) to query the database:

```python
@pytest.mark.integration
def test_customer_persisted_to_database(create_valid_customer):
    """Verify customer data is saved to database."""
    
    # Arrange
    customer = create_valid_customer()
    
    # Act
    db_customer = get_customer_from_db(customer["id"])
    
    # Assert
    assert db_customer.email == customer["email"]
    assert db_customer.created_at is not None
```

### Validation Pipeline for Integration Tests

```
API Response Validation
    ↓
Database Query
    ↓
Database Consistency Check
```

### Tips

✅ Use fixtures (they validate API response)
✅ Query DB using DAO layer
✅ Verify both API response AND database state
✅ Mark as `@pytest.mark.integration`

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

**Coverage:**

- Logging configuration
- Structured logging wiring
- Pytest marker sanity
- Configuration parsing
- Framework bootstrap validation

**Constraints:**

❌ Must NOT call live APIs
❌ Must NOT require Docker
❌ Must NOT require OAuth
❌ Must NOT require databases
❌ Must NOT require WooCommerce

### Contract 📋

**API contract and transport validation.** Verify APIs respond correctly.

**Coverage:**

- API connectivity
- HTTP status validation
- Response format validation
- Content-Type validation
- Schema validation
- Serialization behavior

Framework entities are **discovered automatically**, so new entities are included without modifying tests.

### Security 🔒

**Framework-level authentication validation.** Verify authentication works before business logic.

**Coverage:**

- Successful authentication (valid OAuth)
- Invalid OAuth rejection
- Authentication matrix (all entities)
- GET, POST, PUT, DELETE validation
- Error schema validation
- Error response validation (status, code, message)

Framework entities are **discovered automatically**.

### Performance (Entity-Specific)

Unlike Preflight, Contract, and Security, **performance tests belong to each business entity** because every API has different expectations.

```
tests/
├── customers/performance/
├── orders/performance/
└── products/performance/
```

Each entity owns:
- Benchmark scenarios
- Request parameters
- Performance thresholds
- Benchmark iterations

The shared framework provides only reusable utilities for measuring request duration and collecting statistics.

### Big Picture: Test Architecture

| Suite | Responsibility | Scope | Entity-Specific |
|-------|-----------------|-------|-----------------|
| Preflight | Framework sanity | Framework | ❌ |
| Contract | API contract | Framework | ❌ |
| Security | Auth validation | Framework | ❌ |
| Smoke | Critical flow | Entity | ✅ |
| Sanity | Recent changes | Entity | ✅ |
| Regression | Broad coverage | Entity | ✅ |
| Performance | Benchmarking | Entity | ✅ |
| Integration | API + DB | Entity | ✅ |

---

## Performance Tests

Performance tests verify **request timing and throughput** match expectations.

### Key Principle

**Performance expectations vary by entity.** A customer lookup should be < 100ms, but a bulk report might need 30 seconds.

### Location

Performance tests live with their entity, NOT in `tests/shared/`:

```
tests/customers/performance/test_customer_retrieval_time.py
tests/orders/performance/test_bulk_order_export_time.py
```

### Example: Simple Benchmark

```python
import pytest
import time

@pytest.mark.performance
def test_customer_retrieval_under_100ms(customer_helper, create_valid_customer):
    """Verify customer retrieval stays under 100ms."""
    
    # Arrange
    customer = create_valid_customer()
    
    # Act
    start = time.perf_counter()
    response = customer_helper.get_customer_by_id(customer["id"])
    duration_ms = (time.perf_counter() - start) * 1000
    
    # Assert
    assert response.status_code == 200
    assert duration_ms < 100, \
        f"Expected < 100ms, took {duration_ms:.2f}ms"
```

### Tips

✅ Set realistic thresholds (test environment vs production)
✅ Run multiple iterations (collect statistics)
✅ Account for network latency
✅ Mark as `@pytest.mark.performance`

---

## CI Strategy

CI pipelines execute tests in **stages**, from fast feedback to comprehensive validation.

### Fast Pipeline (PR / Commit)

**Goal:** Give feedback in < 5 minutes

```bash
pytest -m "smoke or sanity or preflight"
```

- Preflight (framework validation)
- Smoke (critical flows)
- Sanity (recent changes)

**Pass = merge candidate**

### Full Validation

**Goal:** Comprehensive validation before merge

```bash
pytest -m "not performance and not security"
```

- All of Fast Pipeline
- Plus regression tests
- Plus integration tests
- Excludes specialized suites

**Pass = safe to merge**

### Nightly

**Goal:** Deep coverage after hours

```bash
pytest -m regression
```

- All regression tests
- Catches edge cases
- Can take 30–60 minutes

### Scheduled (Weekly/Monthly)

**Goal:** Specialized validations

```bash
pytest -m performance
pytest -m security
```

- Performance benchmarks
- Security audits
- Runs at fixed times (e.g., Sunday 2 AM)

### Marker-Based Filtering

| Pipeline | Command | Time | Purpose |
|----------|---------|------|---------|
| PR Gate | `pytest -m "smoke or sanity or preflight"` | ~ 5 min | Fast feedback |
| Full | `pytest -m "not performance and not security"` | ~ 15 min | Safe to merge |
| Nightly | `pytest -m regression` | ~ 60 min | Deep coverage |
| Weekly | `pytest -m security` | ~ 10 min | Auth validation |
| Scheduled | `pytest -m performance` | ~ 30 min | Benchmarks |

---

## Common Mistakes

### ❌ Mistake 1: Mixing Abstraction Levels

```python
# WRONG
customer = create_valid_customer()
assert customer.status_code == 201  # ← fixtures return dict, not HttpResponse
```

**Fix:** Use helper for response metadata

```python
# RIGHT
response = customer_helper.create_customer(return_http_response=True)
assert response.status_code == 201
```

---

### ❌ Mistake 2: Validating in Helpers

```python
# WRONG
def create_customer(payload):
    response = APIClient.post("/customers", json=payload)
    assert response.status_code == 201  # ← NO! This belongs in fixture
    return response.json
```

**Fix:** Let fixtures validate

```python
# RIGHT
def create_customer(payload):
    return APIClient.post("/customers", json=payload)

@pytest.fixture
def create_valid_customer(customer_helper):
    def _create():
        response = customer_helper.create_customer({"email": "test@example.com"})
        assert response.status_code == 201  # ← Validation here
        return response.json
    return _create
```

---

### ❌ Mistake 3: Asserting Inside Helpers

```python
# WRONG
def get_customer(customer_id):
    response = APIClient.get(f"/customers/{customer_id}")
    assert response.status_code == 200  # ← NO! Let tests assert
    assert response.json["id"]  # ← NO!
    return response.json
```

**Fix:** Return response, let test assert

```python
# RIGHT
def get_customer(customer_id):
    return APIClient.get(f"/customers/{customer_id}")

def test_get_customer(customer_helper):
    response = customer_helper.get_customer("123")
    assert response.status_code == 200  # ← Test asserts
    assert response.json["id"]
```

---

### ❌ Mistake 4: Overusing Fixtures for Negative Tests

```python
# WRONG
@pytest.fixture
def create_invalid_customer(customer_helper):
    # This breaks the fixture contract!
    response = customer_helper.create_customer({"email": "invalid"})
    return response

def test_invalid_email(create_invalid_customer):
    assert create_invalid_customer.status_code == 400  # ← Confusing
```

**Fix:** Use helper directly

```python
# RIGHT
def test_invalid_email(customer_helper):
    response = customer_helper.create_customer(
        {"email": "invalid"},
        return_http_response=True
    )
    assert response.status_code == 400
```

---

### ❌ Mistake 5: Manual JSON Validation

```python
# WRONG
response = customer_helper.create_customer(...)
json_data = response.json
assert json_data["id"]  # ← Manual validation
assert json_data["email"]
assert json_data["created_at"]
```

**Fix:** Use Pydantic or validators

```python
# RIGHT
response = customer_helper.create_customer(...)
customer_model = CustomerModel(**response.json)  # Validates schema
assert customer_model.id
assert customer_model.email
assert customer_model.created_at
```

---

### ❌ Mistake 6: Using `request_raw()` in Normal Tests

```python
# WRONG
def test_customer_creation(customer_helper):
    resp, _ = APIClient.request_raw(
        method="post",
        endpoint="/customers",
        payload={"email": "test@example.com"}
    )
    assert resp.status_code == 201  # ← Low-level, error-prone
```

**Fix:** Use helper

```python
# RIGHT
def test_customer_creation(customer_helper):
    response = customer_helper.create_customer()
    assert response.status_code == 201
```

---

### ❌ Mistake 7: Reorganizing Test Folders

```
# WRONG
tests/
├── smoke/
│   ├── test_customer_smoke.py
│   ├── test_order_smoke.py
├── regression/
│   ├── test_customer_regression.py
│   ├── test_order_regression.py
```

**Fix:** Domain-driven organization

```
# RIGHT
tests/
├── customers/
│   ├── test_create_customer.py
│   ├── test_get_customer.py
├── orders/
│   ├── test_create_order.py
```

Markers (`@pytest.mark.smoke`, `@pytest.mark.regression`) handle tier separation.

---

### ❌ Mistake 8: Leaving Test Data Behind

```python
# WRONG
def test_customer_creation(customer_helper):
    response = customer_helper.create_customer()
    # NO CLEANUP! Data left in database
    assert response.status_code == 201
```

**Fix:** Use fixtures with cleanup

```python
# RIGHT
@pytest.fixture
def create_valid_customer(customer_helper):
    created_ids = []
    
    def _create():
        response = customer_helper.create_customer()
        created_ids.append(response.json["id"])
        return response.json
    
    yield _create
    
    # Cleanup
    for customer_id in created_ids:
        customer_helper.delete_customer(customer_id)
```

---

## Best Practices

### 1. Start with Happy-Path Tests

Write happy-path (positive) tests first. They should be ~80% of your suite.

```python
def test_customer_can_be_created(create_valid_customer):
    """Verify customer creation works."""
    customer = create_valid_customer()
    assert customer["id"]
```

### 2. Add Negative Tests for Error Cases

Then add negative tests for error scenarios (~10-20%).

```python
def test_create_customer_rejects_invalid_email(customer_helper):
    """Verify invalid email is rejected."""
    response = customer_helper.create_customer(
        {"email": "invalid"},
        return_http_response=True
    )
    assert response.status_code == 400
```

### 3. Use Fixtures for Setup

Fixtures are gatekeepers. Let them create and validate data.

```python
customer = create_valid_customer()  # Clean, safe
```

### 4. Use Helpers for Multi-Step Workflows

Helpers orchestrate complex logic.

```python
# Login + create order + verify
user = login_user(credentials)
order = create_order_for_user(user)
verify_order_in_database(order)
```

### 5. Use Validators for Assertions

Validators check schema and business logic.

```python
customer_model = assert_customer_retrieved_successfully(response)
assert_customer_has_valid_email(customer_model)
```

### 6. Keep Tests Focused

One behavior per test.

```python
# ❌ WRONG: Testing multiple behaviors
def test_customer_workflow():
    customer = create_valid_customer()
    assert customer["email"]
    updated = update_customer(customer["id"])
    assert updated["first_name"]
    deleted = delete_customer(customer["id"])
    assert deleted is None

# ✅ RIGHT: One behavior per test
def test_create_customer(create_valid_customer):
    customer = create_valid_customer()
    assert customer["email"]

def test_update_customer(create_valid_customer, customer_helper):
    customer = create_valid_customer()
    updated = customer_helper.update_customer(customer["id"])
    assert updated["first_name"]

def test_delete_customer(create_valid_customer, customer_helper):
    customer = create_valid_customer()
    result = customer_helper.delete_customer(customer["id"])
    assert result is None
```

### 7. Use Meaningful Test Names

Test names should describe what's being tested.

```python
# ❌ NOT clear
def test_customer():
    pass

# ✅ Clear
def test_customer_email_is_required():
    pass

def test_customer_created_with_valid_data():
    pass

def test_delete_customer_removes_from_database():
    pass
```

### 8. Add Docstrings to Complex Tests

```python
def test_customer_email_validation():
    """Verify email validation works for both valid and invalid formats.
    
    This test checks:
    - Valid emails are accepted
    - Invalid emails are rejected
    - Error message is clear
    """
    # Test code
```

### 9. Organize Imports

```python
# Standard library
import pytest
import time

# Framework
from framework.api_client import APIClient
from framework.helpers import CustomerHelper
from framework.validators import assert_customer_retrieved_successfully

# Tests
from tests.customers.conftest import create_valid_customer
```

### 10. Run Tests Locally Before Pushing

```bash
# Run one test
pytest tests/customers/test_create_customer.py::test_create_customer -v

# Run with markers
pytest -m smoke -v

# Run with coverage
pytest --cov=tests/customers tests/customers/
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
| Create test data | Fixture | `customer = create_valid_customer()` |
| Call API | Helper | `customer_helper.get_customer(id)` |
| Validate schema | Pydantic | `CustomerModel(**response.json)` |
| Validate logic | Validator | `assert_customer_has_valid_email(model)` |
| Check status code | Helper + response mode | `response = helper.create(..., return_http_response=True)` |
| Debug issue | `request_raw()` | `APIClient.request_raw(...)` |

### Marker Quick Reference

```python
# Smoke test (critical, fast)
@pytest.mark.smoke
def test_customer_creation(): pass

# Sanity test (focused, deep)
@pytest.mark.sanity
def test_recent_email_validation_fix(): pass

# Regression test (comprehensive)
@pytest.mark.regression
def test_customer_with_special_characters(): pass

# Integration test (API + DB)
@pytest.mark.integration
def test_customer_persisted_to_database(): pass

# Negative test (error scenarios)
@pytest.mark.negative
def test_create_customer_with_duplicate_email(): pass

# Performance test (timing)
@pytest.mark.performance
def test_customer_retrieval_under_100ms(): pass
```

### Common Test Patterns

#### Happy Path (Most Common)

```python
def test_customer_retrieval(create_valid_customer, customer_helper):
    customer = create_valid_customer()
    response = customer_helper.get_customer_by_id(customer["id"], return_http_response=True)
    assert response.status_code == 200
```

#### Negative Test

```python
def test_invalid_email_rejected(customer_helper):
    response = customer_helper.create_customer(
        {"email": "invalid"},
        return_http_response=True
    )
    assert response.status_code == 400
```

#### Integration Test

```python
@pytest.mark.integration
def test_customer_in_database(create_valid_customer):
    customer = create_valid_customer()
    db_customer = get_customer_from_db(customer["id"])
    assert db_customer.email == customer["email"]
```

#### Performance Test

```python
@pytest.mark.performance
def test_customer_retrieval_fast(create_valid_customer):
    customer = create_valid_customer()
    start = time.perf_counter()
    customer_helper.get_customer_by_id(customer["id"])
    duration_ms = (time.perf_counter() - start) * 1000
    assert duration_ms < 100
```

### CI Execution Commands

```bash
# Fast feedback (PR gate)
pytest -m "smoke or sanity or preflight"

# Full validation (before merge)
pytest -m "not performance and not security"

# Nightly (deep coverage)
pytest -m regression

# Performance benchmarks
pytest -m performance

# Security validation
pytest -m security
```

### Fixture Factory Template

```python
@pytest.fixture
def create_valid_customer(customer_helper):
    """Factory: create validated customer."""
    created_ids = []
    
    def _create(**overrides):
        # Setup
        payload = {"email": "test@example.com", **overrides}
        
        # Execute
        response = customer_helper.create_customer(payload, return_http_response=True)
        
        # Validate
        assert response.status_code == 201
        customer_model = CustomerModel(**response.json)
        
        # Register cleanup
        created_ids.append(customer_model.id)
        
        # Return clean dict
        return {
            "id": customer_model.id,
            "email": customer_model.email,
        }
    
    yield _create
    
    # Cleanup
    for customer_id in created_ids:
        customer_helper.delete_customer(customer_id)
```

---

## Conclusion

The TestEcommerceAPI framework is:

✅ **Enterprise-ready** — designed for teams and scale
✅ **Scalable** — domain-driven organization
✅ **Cleanly designed** — clear separation of concerns
✅ **Beginner-friendly** — fixtures make simple tests simple

**Your job:** Write tests that validate business behavior, not framework code.

**The framework's job:** Handle transport, schema validation, retry logic, and cleanup.

### Final Advice

Ask yourself:

> "Does this help me write better tests faster?"

If not → skip it.

---

**Happy testing! 🚀**
