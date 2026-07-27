# 🧪 Test Development Guide — TestEcommerceAPI (Enterprise)

A comprehensive guide for writing tests in the TestEcommerceAPI framework. Designed for **QA engineers**, **developers**, and **new contributors**.

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
│                    test_get_customer_by_id()                    │
└────────────────────────────┬──────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FIXTURE CREATES DATA                          │
│              create_valid_customer() is called                  │
│        - Calls helper to create customer on API                 │
│        - Validates response (status 201)                        │
│        - Extracts + validates JSON (Pydantic)                   │
│        - Registers cleanup                                       │
│        - Returns clean dict: {id, email, ...}                   │
└────────────────────────────┬──────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    TEST CALLS HELPER                             │
│         response = customer_helper.get_customer_by_id()         │
│                helper._calls_api()                              │
└────────────────────────────┬──────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     HELPER CALLS API                             │
│            APIClient.get("/customers/{id}")                     │
└────────────────────────────┬──────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   APICLIENT ORCHESTRATES                         │
│        - Validates inputs                                        │
│        - Logs request                                            │
│        - Calls HttpClient                                        │
│        - Implements retry logic                                  │
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
         ║     "id": 123,                             ║
         ║     "email": "customer@example.com",       ║
         ║     "created_at": "2024-01-01T...",       ║
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
│           customer_model = CustomerModel(**response.json)       │
│         (Pydantic validates all fields exist + correct types)   │
└────────────────────────────┬──────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   TEST VALIDATES (Layer 3)                       │
│                   Business Logic Validation                      │
│                                                                  │
│              assert customer_model.email == expected_email      │
│              assert customer_model.id is not None               │
└────────────────────────────┬──────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ✅ TEST PASSES                                │
└────────────────────────────┬──────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CLEANUP EXECUTES                              │
│              Fixture cleanup code runs                          │
│              - Calls customer_helper.delete_customer(id)        │
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
customers/
├── test_create.py
│   └── @pytest.mark.smoke
│   └── @pytest.mark.integration
├── test_update.py
│   └── @pytest.mark.regression
└── performance/
    └── test_retrieval_time.py
        └── @pytest.mark.performance

shared/
├── preflight/
│   └── test_logging.py
│       └── @pytest.mark.preflight
├── contract/
│   └── test_schema.py
│       └── @pytest.mark.contract
└── security/
    └── test_auth.py
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

def test_customer_created_in_database(customer_helper, create_valid_customer):
    """Verify customer appears in DB after API call."""
    customer = create_valid_customer()
    db_customer = get_customer_from_db(customer["id"])
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
    assert_customer_identity(customer_model, customer["id"], customer["email"])
```

### For Juniors: Start Simple

```python
def test_customer_has_email(create_valid_customer):
    """Verify customer email is captured."""
    customer = create_valid_customer()
    assert customer["email"]
    assert "@" in customer["email"]
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
def test_create_customer_with_invalid_email(customer_helper):
    """Verify API rejects invalid email."""
    
    response = customer_helper.create_customer(
        payload={"email": "invalid"},
        return_http_response=True
    )
    
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
customer_model = CustomerModel(**response.json)
```

### Layer 3: Business Validation

```python
assert customer_model.email == expected_email
```

### Layer 4: Database Validation

```python
@pytest.mark.integration
def test_customer_in_database(create_valid_customer):
    customer = create_valid_customer()
    db_customer = get_customer_from_db(customer["id"])
    assert db_customer.email == customer["email"]
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

### Example: Helper

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
            return response
        return response.json
    
    def get_customer_by_id(self, customer_id, return_http_response=False):
        """Retrieve a customer by ID."""
        response = APIClient.get(endpoint=f"/customers/{customer_id}")
        if return_http_response:
            return response
        return response.json
```

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
response = customer_helper.create_customer(return_http_response=True)

# Validate schema
customer_model = CustomerModel(**response.json)

# Validate business logic
assert_customer_identity(customer_model, expected_id, expected_email)
```

### Example Validators

```python
def assert_customer_retrieved_successfully(response):
    """Validate successful retrieval response.
    
    Returns:
        CustomerModel: Validated customer object
    """
    assert response.status_code == 200
    customer_model = CustomerModel(**response.json)
    return customer_model

def assert_customer_identity(customer_model, expected_id, expected_email):
    """Validate customer identity (business logic)."""
    assert customer_model.id == expected_id
    assert customer_model.email == expected_email
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
    customer = create_valid_customer()
    db_customer = get_customer_from_db(customer["id"])
    assert db_customer.email == customer["email"]
```

### When NOT to Mark as Integration

If a test does **not** query persistent state (database, cache, message queue, etc.), it should generally **not** be marked as an integration test.

```python
# ❌ NOT integration (no DB query)
@pytest.mark.smoke
def test_customer_response_has_email(create_valid_customer):
    """Verify response contains email."""
    customer = create_valid_customer()
    assert customer["email"]  # Only checks response, no DB query
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

**Performance expectations vary by entity.** A customer lookup should be < 100ms, but a bulk report might need 30 seconds.

### Location

Performance tests live with their entity, NOT in `tests/shared/`:

```
tests/customers/performance/test_customer_retrieval_time.py
```

### Example

```python
@pytest.mark.performance
def test_customer_retrieval_under_100ms(create_valid_customer):
    """Verify customer retrieval stays under 100ms."""
    customer = create_valid_customer()
    
    start = time.perf_counter()
    response = customer_helper.get_customer_by_id(customer["id"])
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
customer = create_valid_customer()
assert customer.status_code == 201  # ← AttributeError
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
# WRONG: Helpers should not assert
def create_customer(payload):
    response = APIClient.post("/customers", json=payload)
    assert response.status_code == 201  # ← NO!
    return response.json
```

**Fix:** Let fixtures validate

```python
# RIGHT: Helpers just orchestrate
def create_customer(payload):
    return APIClient.post("/customers", json=payload)
```

---

### ❌ Mistake 3: Asserting Inside Helpers

Let tests assert, not helpers.

**Fix:** Return data, let test assert

```python
def get_customer(customer_id):
    return APIClient.get(f"/customers/{customer_id}")

def test_get_customer():
    response = customer_helper.get_customer("123")
    assert response.status_code == 200
```

---

### ❌ Mistake 4: Using Fixtures for Negative Tests

```python
# WRONG: Breaks fixture contract
@pytest.fixture
def create_invalid_customer():
    response = customer_helper.create_customer({"email": "invalid"})
    return response  # ← Fixture returning HttpResponse!
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
# WRONG: Repeating schema checks
json_data = response.json
assert json_data["id"]
assert json_data["email"]
assert isinstance(json_data["created_at"], str)
```

**Fix:** Use Pydantic

```python
# RIGHT: One validation, all checked
customer_model = CustomerModel(**response.json)
```

---

### ❌ Mistake 6: Using `request_raw()` in Normal Tests

**Fix:** Use helper

```python
# ONLY for debugging:
resp, _ = APIClient.request_raw(method="post", endpoint="/customers", payload={...})

# Normal tests use helpers:
response = customer_helper.create_customer()
```

---

### ❌ Mistake 7: Reorganizing Test Folders

Don't create smoke/regression/integration folders. Use markers instead.

**Fix:** Domain-driven organization

```
tests/customers/
├── test_create_customer.py
│   └── @pytest.mark.smoke
│   └── @pytest.mark.regression
├── test_update_customer.py
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
def create_valid_customer(customer_helper):
    created_ids = []
    
    def _create():
        response = customer_helper.create_customer()
        created_ids.append(response["id"])
        return response
    
    yield _create
    
    for customer_id in created_ids:
        customer_helper.delete_customer(customer_id)
```

---

## Best Practices

### 1. Start with Happy-Path Tests

Write ~80% happy-path tests (positive cases).

```python
def test_customer_can_be_created(create_valid_customer):
    customer = create_valid_customer()
    assert customer["id"]
```

### 2. Add Negative Tests for Error Cases

Add ~10-20% negative tests (error scenarios).

```python
def test_invalid_email_rejected(customer_helper):
    response = customer_helper.create_customer(
        {"email": "invalid"},
        return_http_response=True
    )
    assert response.status_code == 400
```

### 3. Use Fixtures for Setup

```python
customer = create_valid_customer()  # Clean, safe
```

### 4. Use Helpers for Workflows

```python
user = login_user(credentials)
order = create_order_for_user(user)
verify_order_in_database(order)
```

### 5. Use Validators for Assertions

```python
customer_model = assert_customer_retrieved_successfully(response)
assert_customer_has_valid_email(customer_model)
```

### 6. Keep Tests Focused

One behavior per test.

```python
# ✅ RIGHT: Separate concerns
def test_create_customer(create_valid_customer):
    customer = create_valid_customer()
    assert customer["email"]

def test_update_customer_first_name(create_valid_customer):
    customer = create_valid_customer()
    updated = customer_helper.update_customer(customer["id"], {"first_name": "Bob"})
    assert updated["first_name"] == "Bob"
```

### 7. Use Meaningful Names

```python
# ✅ Clear
def test_customer_email_is_required():
    pass
```

### 8. Run Tests Locally

```bash
pytest tests/customers/test_create_customer.py -v
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
| Create test data | Fixture | `customer = create_valid_customer()` |
| Call API | Helper | `customer_helper.get_customer(id)` |
| Validate schema | Pydantic | `CustomerModel(**response.json)` |
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
def test_customer_retrieval(create_valid_customer, customer_helper):
    customer = create_valid_customer()
    response = customer_helper.get_customer_by_id(customer["id"], return_http_response=True)
    assert response.status_code == 200
```

#### Negative Test

```python
def test_invalid_email_rejected(customer_helper):
    response = customer_helper.create_customer({"email": "invalid"}, return_http_response=True)
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
    assert (time.perf_counter() - start) * 1000 < 100
```

### Fixture Factory Template

```python
@pytest.fixture
def create_valid_customer(customer_helper):
    created_ids = []
    
    def _create(**overrides):
        payload = {"email": "test@example.com", **overrides}
        response = customer_helper.create_customer(payload, return_http_response=True)
        assert response.status_code == 201
        customer_model = CustomerModel(**response.json)
        created_ids.append(customer_model.id)
        return {"id": customer_model.id, "email": customer_model.email}
    
    yield _create
    
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

**Your job:** Write tests that validate business behavior.

**The framework's job:** Handle transport, schema validation, retry logic, and cleanup.

### Final Advice

Ask yourself:

> "Does this help me write better tests faster?"

If not → skip it.

---

**Happy testing! 🚀**
