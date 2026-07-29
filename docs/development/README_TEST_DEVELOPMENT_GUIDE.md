# 🧪 Test Development Guide — TestEcommerceAPI

*How to write tests in this framework: what goes where, and why.*

This guide replaces two overlapping documents (`README_API_TESTING_STANDARDS.md` and `README_TEST_WRITING_GUIDE.md`) with one source of truth. For how the underlying HTTP client itself is built (`HttpClient` / `APIClient` / `HttpResponse` internals), see `README_ARCHITECTURE.md` — this document covers how to *write tests* against that architecture.

**Audience:** QA engineers, developers adding API tests, and new contributors — including juniors who are new to the framework.

>Prerequisite: This guide assumes you're familiar with the repository structure and local setup. If you're new to the project, read README_QA_DEVELOPER_ONBOARDING.md first.

---

## 📋 Contents

1. Quick Start (for new contributors)
2. Core Philosophy
3. Architecture & Layer Responsibilities
4. Writing Positive Tests
5. Advanced Validation & Negative Tests
6. Debugging with `request_raw()`
7. Core Rules
8. Fixtures (Factory Pattern)
9. Validators
10. Helpers
11. Test Structure & Organization
12. Marker Strategy
13. CI Strategy
14. Shared Test Suites (Framework-Level Tests)
15. Cleanup, Observability, Retry & Timeout
16. What NOT to Do
17. Golden Rules

---

## 1. 🚀 Quick Start (for new contributors)

If you only read one section, read this one. Three levels, in the order you'll actually need them:

**Level 1 — Happy path (most tests):**
```python
customer = create_valid_customer()

assert customer["id"]
assert customer["email"]
```
Fixtures give you clean, pre-validated data. No HTTP noise, always valid, safe to build on without understanding the transport layer yet.

**Level 2 — You need status codes, headers, or a negative case:**
```python
response = customer_helper.create_customer(return_http_response=True)

assert response.status_code == 201
assert response.json["id"]
```
Call the helper directly in "response mode" instead of going through a fixture.

**Level 3 — Something's actually broken and you need to see the raw wire traffic:**
```python
resp, _ = APIClient.request_raw(
    method="post",
    endpoint="customers",
    payload={"email": "invalid"}
)

print(resp.status_code)
print(resp.text)
```
Debugging only — never for normal test assertions.

👉 Start at Level 1. Only reach for Level 2 or 3 when the situation calls for it — jumping straight to `request_raw()` for a normal test is the most common mistake newcomers make.

```
Need to write a test?
        │
        ▼
    Happy path?
   │          │
  Yes        No
   │          │
   ▼          ▼
Fixture   Need status/header?
              │
         Yes       No
          │         │
          ▼         ▼
      Helper     request_raw()
                 (debug only)

```


---

## 2. 🧠 Core Philosophy

Tests should be:
- ✅ Readable and focused on business behavior
- ✅ Stable in CI
- ✅ Responsible for creating their own data, and querying only that data
- ✅ Business-focused in their assertions

Tests should **NOT**:
- ❌ Orchestrate complex workflows (that's a Helper's job)
- ❌ Validate response structure manually (that's a Validator's job)
- ❌ Call low-level transport code directly (that's `request_raw()`, debugging only)

And a matching rule for the layers underneath tests:
- ✅ Fixtures act as **gatekeepers** — they validate and normalize before a test ever sees the data
- ❌ Transport layers (`HttpClient` / `APIClient` / API layer) do **not** validate — they fail fast on transport errors and leave structure/business validation to the layers above them
- ✅ Always use the framework's `HttpResponse` model instead of a raw `requests.Response`

---

## 3. 🧱 Architecture & Layer Responsibilities

```
HttpClient → APIClient → HttpResponse → API layer → Helper
```

| Layer | Responsibility |
|---|---|
| `HttpClient` | Sends raw HTTP requests; owns transport + timeout |
| `APIClient` | Orchestrates requests: retries, backoff, logging; returns `HttpResponse` |
| `HttpResponse` | Parsed and normalized response object |
| API layer | Endpoint mapping — thin, no logic |
| Helper | Calls the API layer, orchestrates workflows (optionally combining API + DAO/DB) |
| Validator | Validates structure, business logic, and DB consistency. Pattern: **fetch → validate**, never the reverse |
| Fixture | Calls Helper + Validator, registers cleanup, returns a clean validated `dict` |
| Test | Business assertions only |

*(Full internals of `HttpClient` / `APIClient` / `HttpResponse` live in `README_ARCHITECTURE.md`.)*

### Two paths from Helper to Test

```
                              Helper
                                │
                ┌───────────────┴────────────────┐
                ▼                                 ▼
          Fixture (happy path)          Test calls Helper directly
          • validates via Validator     (return_http_response=True)
          • registers cleanup           • used for negative tests
          • returns clean dict          • used for advanced/debug checks
                │                                 │
                ▼                                 ▼
              Test                              Test
      (business assertions)           (status / header / error assertions)
```

Most tests only need the left-hand path. Reach for the right-hand path when you need to inspect the response itself.

---

## 4. 🟢 Writing Positive Tests

Use a fixture. It hands you a clean, validated dict — no HTTP noise, always valid, safe for juniors to build on:

```python
customer = create_valid_customer()

assert customer["id"]
assert customer["email"]
```

For anything beyond a trivial assertion, follow **Arrange → Act → Assert**:

```python
def test_get_customer_by_id(customer_helper, create_valid_customer):

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
Notice this still uses a **Validator** (`assert_customer_retrieved_successfully`) to keep the test body short and the assertion logic reusable.

---

## 5. 🔵 Advanced Validation & 🔴 Negative Tests

**Advanced validation** — when you need status codes, headers, or timing metadata, call the helper in response mode instead of using a fixture:

```python
response = customer_helper.create_customer(return_http_response=True)

assert response.status_code == 201
assert response.json["id"]
```
Use this when: debugging failures, checking headers, validating timing/metadata.

**Negative tests** — always use the helper in response mode. Never use fixtures for negative cases, since fixtures are guaranteed-valid by design:

```python
response = customer_helper.create_customer(
    email="invalid",
    return_http_response=True
)

assert response.status_code == 400
```
Negative tests should also validate the error schema and whatever business rule the error is meant to enforce.

---

## 6. 🔬 Debugging with `request_raw()`

Use `request_raw()` only when you need to see the actual wire traffic:

```python
resp, _ = APIClient.request_raw(
    method="post",
    endpoint="customers",
    payload={"email": "invalid"}
)

print(resp.status_code)
print(resp.text)
print(resp.request.headers)
```

⚠️ Notes:
- Returns a raw `requests.Response`, not `HttpResponse`
- JSON parsing may fail — you're on your own here
- Not for use in normal test assertions

---

## 7. ⚠️ Core Rules

**Rule 1 — Fixtures are strict.** Fixtures like `create_valid_customer`:
- ALWAYS return a `dict`
- ALWAYS return valid data
- NEVER return an `HttpResponse`
- NEVER return invalid objects

**Rule 2 — Validation order is mandatory.** Always validate in this order:
1. Transport status validation (`status_code`)
2. JSON extraction
3. Structure validation (Pydantic model)
4. Business validation
5. Database validation (if applicable)

**Rule 3 — Don't mix abstraction levels.**

❌ Wrong:
```python
customer = create_valid_customer()
assert customer.status_code == 201   # fixture returns a dict, not a response!
```

✅ Correct:
```python
response = customer_helper.create_customer(return_http_response=True)
assert response.status_code == 201
```

**Rule 4 — Use the right tool for the job:**

| Scenario | Use |
|---|---|
| Happy path | Fixture |
| Need status / headers | Helper (response mode) |
| Negative testing | Helper (response mode) |
| Deep debugging | `request_raw()` |

**Other common mistakes to avoid:**
- Manually validating JSON structure inside a test instead of using a Validator
- Overusing Helpers for negative tests instead of asserting directly on the response
- Asserting inside a Helper (Helpers orchestrate, they don't assert)
- Fetching data inside a Validator (Validators validate, they don't fetch)

---

## 8. 📦 Fixtures (Factory Pattern)

Fixtures act as **gatekeepers**. A fixture must:
1. Call the Helper
2. Validate the transport status
3. Extract JSON
4. Validate schema (Pydantic model)
5. Register cleanup
6. Return a clean `dict`

**Structure validation has moved to Pydantic.** The framework now validates response structure with Pydantic models instead of hand-written JSON Schema:

```python
# Old pattern
validate_customer_response_schema(customer)

# New pattern
customer_model = CustomerModel(**customer)
```
This gives strict typing, clearer validation errors, easier debugging, and better IDE support.

---

## 9. 🔍 Validators

Validators are responsible for:
- Validating response structure
- Validating business logic
- Validating DB consistency (via the DAO layer)

Validators must **not** fetch data themselves. The pattern is always:

```
fetch → validate
```
A Test or Fixture fetches the data (via a Helper), then hands it to a Validator.

💡 If a test's validation touches the database, mark it `@pytest.mark.integration` (see §12).

---

## 10. 🧠 Helpers

Helpers are responsible for:
- Calling APIs
- Orchestrating workflows
- Combining API + DAO/DB logic where needed

Helpers must **not** assert. Assertions belong in Tests (business logic) or Validators (reusable structural/business checks) — never inside a Helper.

---

## 11. 📁 Test Structure & Organization (MANDATORY)

```
tests/
   customers/
   orders/
   products/
   coupons/
   shared/
```

- ✅ Domain-driven — matches the entity boundaries
- ✅ Enables team ownership per entity
- ✅ Scales easily as new entities are added
- ❌ Do **not** reorganize by smoke/regression folders

> Each business entity owns its own smoke, integration, regression, and performance tests. `tests/shared/` is reserved exclusively for framework-level test suites (see §14).

**Arrange → Act → Assert** is the required structure within a test (see the example in §4).

---

## 12. 🏷️ Marker Strategy

**1. Domain** (auto-applied via conftest — never add manually): `customers`, `orders`, `products`, `coupons`, `shared`

**2. Execution tier:**

| Marker | Meaning |
|---|---|
| `smoke` | Critical API health — broad, shallow, fast. Confirms the build is stable enough to test further. |
| `sanity` | Narrow and deep. Targets only the modules that recently changed; runs after smoke has passed. |
| `regression` | Full coverage |

**3. Test type:**

| Marker | Meaning |
|---|---|
| `integration` | API + DB validation |
| `contract` | Schema validation |
| `negative` | Invalid input tests |
| `e2e` | Multi-step workflow |

**4. Specialized:** `performance`, `security`, `preflight`, `bulk`

**Marker rules:**
- Max 2–3 markers per test, excluding domain
- Domain markers are auto-applied — never add them manually
- Use consistent naming (`negative`, not `negative_test`)

```python
pytestmark = [
    pytest.mark.integration,
    pytest.mark.regression
]
```

**Big picture:**
- Domain → `customers`, `orders`, etc.
- Execution → `smoke`, `sanity`, `regression`
- Type → `integration`, `contract`, `negative`, `e2e`
- Special → `performance`, `security`, `preflight`, `bulk`

---

## 13. 🤖 CI Strategy

| Pipeline | Command |
|---|---|
| Fast (PR / commit) | `pytest -m "smoke or sanity or preflight"` |
| Full validation | `pytest -m "not performance and not security"` |
| Nightly | `pytest -m regression` |
| Scheduled | `pytest -m performance` / `pytest -m security` |

These pytest markers map onto dedicated GitHub Actions workflows — see the table in §14.

---

## 14. 🧪 Shared Test Suites (Framework-Level Tests)

The framework also contains shared tests that validate infrastructure, security, and environment behavior **before** entity-specific tests run. These execute once for the whole framework rather than once per entity — where a suite must cover every entity (Contract, Security), it discovers entities dynamically and iterates internally, so CI reports show **Scope: Shared Framework** rather than an entity name, and adding a new entity extends coverage automatically without touching the tests.

```
tests/shared/
    preflight/
        test_logging_globals.py
    security/
        test_authentication_matrix.py
        test_authentication_success.py
    contracts/
        test_api_connectivity.py
        test_response_format.py
```

**Preflight** — verifies environment/framework configuration before the full suite runs (API connectivity, logging config, response format). Must NOT: call live APIs, require Docker, require OAuth credentials, require a database, or require WooCommerce.

**Contract** — validates API contracts and transport behavior: connectivity, HTTP status, response format, content-type, schema, serialization. Entities are discovered automatically.

**Security** — validates framework-level authentication: successful auth, invalid OAuth credential rejection, an authentication matrix across all entities, GET/POST/PUT/DELETE coverage, and error schema/response validation. Entities are discovered automatically.

**Performance** — the one exception: entity-specific, not shared, because every API has different performance expectations. Each entity owns its own benchmark scenarios, request parameters, thresholds, and iteration counts under e.g. `tests/customers/performance/`. The shared framework only provides reusable timing/benchmark utilities.

**Workflow mapping:**

| Workflow | Type | Scope | Public report |
|---|---|---|:---:|
| Preflight | Shared | Framework | ❌ |
| Contract | Shared | Framework | ❌ |
| Security | Shared | Framework | ❌ |
| Smoke | Entity | Customers / Orders / ... | ✅ |
| Integration | Entity | Customers / Orders / ... | ✅ |
| Regression | Entity | Customers / Orders / ... | ✅ |
| Performance | Entity | Customers / Orders / ... | ✅ |

---

## 15. 🧼 Framework Runtime Features (Cleanup, Observability, Retry & Timeout)

**Cleanup** — automatic via fixtures. Avoid leftover data between tests.

**Observability** — already included: structured logging, request duration, error logging. No need for a separate metrics system.

**Retry & timeout** — `HttpClient` owns timeout; `APIClient` owns retry/backoff. Tests don't need to think about either.

---

## 16. 🚫 What NOT to Do

- ❌ No `ResponseAdapter`
- ❌ No extra metrics layer
- ❌ No extra abstraction beyond the layers in §3
- ❌ No folder restructuring — domain-driven `tests/<entity>/` is mandatory (§11)
- ❌ No over-tagging — 2–3 markers max, excluding domain (§12)

---

## 17. 🎯 Golden Rules

1. Fixtures return validated data
2. Helpers orchestrate — they don't assert
3. Validators validate — they don't fetch
4. Tests verify business logic
5. Keep tests simple

Before adding anything new, ask: **"Does this help me write better tests, faster?"** If not, skip it.

```
HttpClient   → raw
APIClient    → orchestrate
HttpResponse → safe
Helper       → workflow
Validator    → checks
Fixture      → validated
Test         → assert
```

This framework is ready, scalable, and cleanly designed. Focus on writing tests, not refactoring the framework.

---

**End of Document**
