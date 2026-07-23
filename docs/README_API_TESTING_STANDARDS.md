# 🚀 API Testing Standards & Guidelines — TestEcommerceAPI

For how the underlying client is built (HttpClient / APIClient / HttpResponse), see README_ARCHITECTURE.md.
This document covers how to write tests against that architecture.
---

# 🧠 Core Principles

- ✅ Tests own business validation; transport layers don't validate.
- ✅Fixtures act as **gatekeepers**: they validate and normalize before a test ever sees the data.
- ❌ Transport layers (`HttpClient` / `APIClient` / API layer) do **not** validate.
- ✅ Keep tests clean, readable, and business-focused.
- ✅Fail fast on transport errors.
- ✅Use the framework's consistent response model (`HttpResponse`) rather than raw `requests.Response`.
---

# 🧱 Layer Responsibilities (quick reference)

| Layer | Responsibility |
|---|---|
| HttpClient | Sends raw HTTP requests |
| APIClient | Orchestrates requests, retries, logging; returns `HttpResponse` |
| HttpResponse | Parsed + normalized response object |
| API layer | Endpoint mapping (thin, no logic) |
| Helper | Business orchestration, optional abstraction |
| Fixture | ✅ Validates + returns a clean `dict` |
| Test | Business assertions |

*(Full detail on each layer lives in `README_ARCHITECTURE.md`.)*

---

# 🧠 Mental Model

```
HttpClient      → send request
ApiClient       → manage request
HttpResponse    → safe response
Fixture         → validated data
Test            → business validation
```

---


# 🛠️Choosing the Right Tool

| Scenario | Use |
|---|---|
| Happy path | Fixture |
| Need status code / headers | Helper (`return_http_response=True`) |
| Negative testing | Helper (`return_http_response=True`) |
| Deep debugging | `request_raw()` |

---

# 🟢 Positive Tests (Recommended)

Use fixtures → clean, validated dict

```python
customer = create_valid_customer()

assert customer["id"]
assert customer["email"]
```

* No HTTP noise
* Always valid data
* Safe for juniors

---

# 🔵 Advanced Validation (When Needed)

Use helper with HttpResponse

```python
response = customer_helper.create_customer(return_http_response=True)

assert response.status_code == 201
assert response.json["id"]
```

Use this when:
- Debugging failures
- Checking headers
- Validating timing / metadata

---

# 🔴 Negative Tests

Use helper in response mode (preferred modern approach)

```python
response = customer_helper.create_customer(
    email="invalid",
    return_http_response=True
)

assert response.status_code == 400
```

* Required for error scenarios
* Do NOT use fixtures here

---

# 🔬 Debugging (Advanced Only)

Use `request_raw()` ONLY when needed:

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
- Returns `requests.Response`
- JSON parsing may fail
- Not for normal tests

---

# ⚠️ Core Rules

## **Rule 1 — Fixtures are strict.** Fixtures like `create_valid_customer`:

Fixtures like `create_valid_customer`:

- ALWAYS return dict
- ALWAYS return valid data
- NEVER return HttpResponse
- NEVER return invalid objects

---

## **Rule 2 — Validation order (mandatory).** Always validate in this order:

Always follow:

1. Transport status validation (`status_code`)
2. JSON extraction
3. Structure validation (Pydantic)
4. Business validation
5. Database validation (if applicable)

---

## Rule 3 — Do NOT mix abstraction levels

❌ WRONG:

```python
customer = create_valid_customer()
assert customer.status_code == 201
```

✔ CORRECT:

```python
response = customer_helper.create_customer(return_http_response=True)
assert response.status_code == 201
```

---

## Rule 4 — Use the right tool

| Scenario                | Use |
|------------------------|-----|
| Happy path             | Fixture |
| Need status / headers  | Helper (response mode) |
| Negative testing       | Helper (response mode) |
| Deep debugging         | request_raw() |

---

# 🧪 Fixtures (Factory Pattern)

Fixtures act as **Gatekeepers**:

- Call the helper
- Validate status
- Extract JSON
- Validate schema (Pydantic)
- Register cleanup
- Return a clean dict
---

# 🧠 Why this works

- Separation of concerns
- Fail-fast validation
- Clean test code
- Reusable setup
- Prevents flaky tests
- Predictable behavior

---

# 🚀 Summary

*  Fixtures → validated dict
*  Helpers → optional HttpResponse
*  Tests → business logic
*  No validation in transport layers
*  request_raw → debugging only

---

# 👨‍💻 For Juniors

Start with:

```python
customer = create_valid_customer()
```

Then move to:

```python
response = customer_helper.create_customer(return_http_response=True)
```

Use `request_raw()` only for debugging.

---

# 🎯 Final Takeaway

```
HttpClient → raw
RequestUtility → orchestrate
HttpResponse → safe
Fixture → validated
Test → assert
```

---

**End of Document**



------------------------------------------------------------------
# 🔄 Structure Validation Update (Pydantic)

The framework now uses **Pydantic models instead of JSON Schema**
for response structure validation.

Old pattern:

validate_customer_response_schema(customer)

New pattern:

customer_model = CustomerModel(**customer)

Advantages:

- strict typing
- clearer validation errors
- easier debugging
- better IDE support


------------------------------------------------------------------
# Updated Validation Order

Always validate responses in this order:

1. Transport status validation
2. JSON extraction
3. Structure validation (Pydantic)
4. Business validation
5. Database validation (if applicable)


------------------------------------------------------------------
# 🧪 Shared Test Suites (Framework-Level Tests)

The framework also contains shared tests that validate infrastructure,
security, and environment behavior before running entity-specific tests.

These suites are framework-level validation suites.

Shared Framework suites execute once for the framework rather than once per entity.

Where validation must cover every supported API entity (for example Contract
and Security), the tests dynamically discover the framework entities and
iterate over them internally.

This avoids duplicated CI executions while ensuring complete platform
coverage.

Consequently, CI reports identify them using

**Scope: Shared Framework rather than an entity name.**

Directory structure:

tests/shared/

    preflight/
        test_api_connectivity.py
        test_response_format.py
        test_logging_globals.py

    security/
        test_authentication_matrix.py
        test_authentication_success.py

    contracts/
        test_api_connectivity.py
        test_response_format.py

---

Purpose of each category:

Preflight tests
---------------
Verify the test environment and framework configuration before executing
the full test suite.

Examples:
- API connectivity
- logging configuration
- response format validation

---

Security tests
--------------
Validate authentication and access control behavior.

Example matrix:

4 entities
× 4 HTTP methods
× 3 invalid credential cases
= 48 security tests

---

Performance tests
-----------------
Provide lightweight baseline response time checks to detect regressions
in API responsiveness.

---

Contract tests
-----------------

Contract tests validate API contracts and response schemas independently for every discovered framework entity

---


### 🔀 The workflow:

| Workflow | Type | Scope | Public |
|----------|------|-------|:------:|
| Preflight | Shared | Framework | ❌ |
| Contract | Shared | Framework | ❌ |
| Security | Shared | Framework | ❌ |
| Smoke | Entity | Customers / Orders / ... | ✅ |
| Integration | Entity | Customers / Orders / ... | ✅ |
| Regression | Entity | Customers / Orders / ... | ✅ |
| Performance | Entity | Customers / Orders / ... | ✅ |

------------------------------------------------------------------
