# 🧪 Test Development Guide — TestEcommerceAPI

**How to write API tests in this framework — what to use, where to use it, and why.**

This guide explains how to build API tests using the framework's existing layers: fixtures, Helpers, `HttpResponse`, Validators, and `request_raw()`. It focuses on **test development**, not on the internal implementation of the HTTP client.

**Audience:** QA engineers, developers adding API tests, and contributors who need to understand the framework's testing patterns.

> **Prerequisite:** Be familiar with the repository structure and local setup. If you are new to the project, start with `README_QA_DEVELOPER_ONBOARDING.md`.

### Related guides

- **Environment configuration:** `docs/framework/README_ENVIRONMENT_CONFIG_GUIDE.md`
- **Playwright / UI testing:** `docs/development/README_UI_TESTING_GUIDE.md`
- **HTTP client internals:** `README_API_CLIENT.md`

---

## 📋 Contents

1. Quick Start — the test interfaces
2. Core Philosophy
3. Architecture & Layer Responsibilities
4. Writing Tests
5. Which Interface to Use for Each HTTP Method
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

## 1. 🚀 Quick Start — The 3 Test Levels

There are **three ways to interact with the API from a test**. Start with the simplest one that gives you what the test needs.

The levels are not "junior", "senior", "simple", or "advanced" versions of testing. They describe **how much of the framework you need to expose to the test**.

---
⚠️ **Note**: The test owns the HTTP status of the operation it is testing. The Validator owns the response/error body

---

### 🔹Level 1 — Happy path / valid test data

**Use this for most normal tests.**

When a test needs a valid customer, product, coupon, etc. as a **precondition**, use the entity fixture:

```python
def test_get_customer_by_id(customer_helper, create_valid_customer):

    # ARRANGE
    # Create valid test data.
    # The fixture performs the POST, validates the expected 201 response,
    # validates the response body, and registers cleanup.
    customer = create_valid_customer()

    # ACT
    # Perform the GET operation that this test is actually testing.
    customer_data = customer_helper.get_customer_by_id(customer["id"])

    # ASSERT
    # Assert the behaviour/data that matters to this test.
    assert customer_data["id"] == customer["id"]
    assert customer_data["email"] == customer["email"]
```

The important point is that the fixture does **more than create data**.

Its internal flow is:

```text
create_valid_customer()
        │
        ▼
    Helper
        │
        ▼
  HttpResponse
        │
        ├── validate expected HTTP status (for example 201)
        │
        ▼
   response.json
        │
        ▼
 Pydantic / domain validation
        │
        ▼
 cleanup registration
        │
        ▼
 clean validated dict
        │
        ▼
       Test
```

So when the test receives:

```python
customer = create_valid_customer()
```

it can trust the fixture contract:

- the creation request succeeded;
- the expected HTTP status was received;
- the response body was validated;
- the data is valid;
- cleanup has been registered;
- the test receives a `dict`, **not** an `HttpResponse`.

**Level 1 is therefore the normal starting point for valid setup data.**

---

### 🔹 Level 2 — You need the HTTP response

Use **Helper response mode** when the test needs to inspect the actual HTTP response of the operation being tested.

**⚠️ Status-code rule:** the test that owns the API operation validates its expected HTTP status code. Validators validate the response body/data contract; they do not normally own the HTTP status assertion.

The main exception is the `create_valid_<entity>()` fixture: it validates the `POST` status used to create valid setup data because that POST belongs to the fixture's setup contract.

```python
response = customer_helper.get_customer_by_id(
    customer["id"],
    return_http_response=True,
)

assert response.status_code == 200

customer_data = response.json
assert customer_data["id"] == customer["id"]
```

With:

```python
return_http_response=True
```

the Helper returns the framework's `HttpResponse` object:

```text
HttpResponse
├── status_code
├── headers
├── elapsed
├── text
└── json   ← response body
```

**It does not make another HTTP request.**

The response body is already part of the `HttpResponse`:

```python
response.json
```

So the two Helper modes mean:

```text
return_http_response=False  (default)
        │
        ▼
   parsed response body
        │
        ▼
       dict


return_http_response=True
        │
        ▼
    HttpResponse
    ├── status_code
    ├── headers
    ├── elapsed
    ├── text
    └── json  ← body
```

Use `True` when the test needs things such as:

- HTTP status code;
- response headers;
- elapsed/request timing;
- response text;
- an error payload;
- transport metadata;
- a response Validator that expects an `HttpResponse`.

A positive test can therefore use Level 2. **"Positive" does not automatically mean Level 1.**

For example, this is a positive GET test:

```python
def test_get_customer_by_id(customer_helper, create_valid_customer):

    # ARRANGE
    customer = create_valid_customer()

    # ACT
    # We need the HTTP response because this test verifies the GET response.
    response = customer_helper.get_customer_by_id(
        customer["id"],
        return_http_response=True,
    )

    # ASSERT — transport
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. "
        f"Response: {response.text}"
    )

    # ASSERT — response body
    customer_model = assert_valid_customer_response(response.json)

    # Business/identity assertion.
    assert_customer_identity(
        customer_model,
        customer["id"],
        customer["email"],
    )
```

Here the creation of the customer is setup, so the fixture handles it. The **GET is the operation under test**, so the test receives its `HttpResponse`.

---

### Level 2 also covers negative tests

A negative test normally needs the HTTP response because the expected error status and error payload are part of what the test verifies.

```python
def test_get_customer_by_id_not_found(customer_helper):

    # ARRANGE
    # Deliberately use an ID that should not exist.
    non_existing_id = 999999

    # ACT
    # Response mode is required because the expected 404 is part of the test.
    response = customer_helper.get_customer_by_id(
        non_existing_id,
        return_http_response=True,
    )

    # ASSERT
    assert response.status_code == 404

    # The error body is already inside the HttpResponse.
    error = response.json

    # Reusable Validator checks the error contract.
    assert_customer_not_found_error(error)
```

The principle is:

> **If the test needs to inspect the HTTP response of the operation under test, use `return_http_response=True`.**

---

### 🔹 Level 3 — Raw wire-level debugging

Use `request_raw()` only when the normal framework layers are not giving you enough information to understand a problem.

```python
resp, _ = APIClient.request_raw(
    method="post",
    endpoint="customers",
    payload={"email": "invalid"},
)

print(resp.status_code)
print(resp.text)
print(resp.request.headers)
```

This exposes the underlying raw `requests.Response`.

Use it for **debugging**, for example when investigating:

- unexpected transport behaviour;
- authentication problems;
- request/response details;
- serialization problems;
- something that appears wrong below the normal Helper/Validator layers.

It is **not** the normal way to write an API test.

### Quick decision table

| What do you need? | Use |
|---|---|
| A valid resource for test setup | **Level 1 — fixture** |
| Clean validated API data | **Level 1 — Helper default return** |
| Status code of the operation under test | **Level 2 — `return_http_response=True`** |
| Headers / elapsed time / response text | **Level 2 — `return_http_response=True`** |
| Error response | **Level 2 — `return_http_response=True`** |
| Raw wire-level investigation | **Level 3 — `request_raw()`** |

**Start at Level 1. Move to Level 2 when the test needs the response itself. Use Level 3 only for low-level debugging.**

---

## 2. 🧠 Core Philosophy

Tests should be:

- ✅ Readable and focused on the behaviour being verified
- ✅ Stable in CI
- ✅ Responsible for creating their own test data
- ✅ Focused on business behaviour rather than framework internals
- ✅ Built from the framework's existing fixtures, Helpers, and Validators

Tests should **not**:

- ❌ Orchestrate complex workflows that belong in Helpers
- ❌ Reimplement reusable response validation
- ❌ Call low-level transport code directly during normal test execution
- ❌ Query unrelated or shared test data when the test can create its own data

And the framework layers have clear responsibilities:

- ✅ Fixtures prepare valid test data and act as gatekeepers
- ❌ `HttpClient` / `APIClient` / API layers do not perform business validation
- ✅ `HttpResponse` provides the normalized HTTP response to the layers that need it
- ✅ Validators validate response/data contracts; they do not fetch data or own HTTP status assertions
- ✅ Helpers orchestrate API/domain workflows; they do not assert
- ✅ Tests verify the behaviour and business outcome

---

## 2.5 🚨 Environment Gate (Session-Level Safety Check — Separate from Preflight)

The framework includes a **session-scoped environment validation gate**
implemented in the shared `api_client` fixture. This is separate from the
`preflight` test suite: **Preflight does not call live APIs**, while this gate
performs the live API/authentication check required before environment-dependent tests.

This gate runs **once per test session** and ensures:

- API is reachable
- Authentication is valid
- The target environment is correctly configured

If validation fails, the test session is **terminated immediately** using `pytest.exit()`.

#### ⚠️ Important

- This is **NOT a test failure**
- This is an **infrastructure failure**
- No tests are executed after this point

#### 💡 Why this exists

Without this gate:

- All tests would fail with the same error (e.g. 401)
- Test output becomes noisy and misleading
- Debugging becomes harder
- e.g. missing credentials → tests keep running → pagination loops → massive output

#### 👉 Example output

```text
🚨 ENVIRONMENT GATE FAILED — NOT A TEST FAILURE

API rejected credentials (401)
Check WC_KEY / WC_SECRET in .env
```

#### Design principle

- Fail fast
- Fail once
- Fail clearly

**💡 Note:**

Pagination is additionally protected at runtime to prevent incomplete datasets.
See the framework architecture documentation for *Failure Handling & Data Integrity Layers*.

---

## 3. 🧱 Architecture & Layer Responsibilities

```text
HttpClient → APIClient → HttpResponse → API layer → Helper
                                      ↘
                                        Test / Fixture
```

| Layer | Responsibility |
|---|---|
| `HttpClient` | Sends raw HTTP requests; owns transport + timeout |
| `APIClient` | Orchestrates requests: retries, backoff, logging; returns `HttpResponse` |
| `HttpResponse` | Parsed and normalized HTTP response object, including response metadata and body |
| API layer | Endpoint mapping — thin, no business logic |
| Helper | Calls the API layer and orchestrates workflows (optionally combining API + DAO/DB) |
| Validator | Validates response/data structure, business rules, and DB consistency; does not own HTTP status assertions |
| Fixture | Calls Helper + Validator, validates setup, registers cleanup, returns clean validated data |
| Test | Arranges data, performs the operation under test, and asserts behaviour |

*(Full internals of `HttpClient` / `APIClient` / `HttpResponse` live in `README_API_CLIENT.md`.)*

### How a normal test uses the layers

```text
ARRANGE
   │
   └── Fixture → valid setup data
                  │
                  ▼
ACT
   │
   └── Helper → API → HttpResponse
                         │
                         ▼
ASSERT
   │
   ├── transport validation, when required
   ├── response/body validation
   └── business assertions
```

The test does not need to know how `HttpClient` performs retries, timeouts, authentication, or request construction. Those responsibilities belong to the framework layers below the test.

---

## 4. 🧪 Writing Tests

### 4.1 Arrange → Act → Assert — what each part means

All API tests should normally follow **Arrange → Act → Assert (AAA)**.

The three parts have different purposes:

#### Arrange — prepare everything the test needs

This includes:

- creating valid test data with fixtures;
- defining IDs, codes, emails, or other inputs;
- preparing an invalid value for a negative test;
- setting up any required preconditions.

**Arrange should not perform the behaviour that the test is supposed to verify.**

Example:

```python
# ARRANGE
# We need an existing customer so that we can test GET /customers/{id}.
customer = create_valid_customer()
customer_id = customer["id"]
```

#### Act — perform the operation being tested

This is the actual API action whose behaviour the test is verifying.

```python
# ACT
response = customer_helper.get_customer_by_id(
    customer_id,
    return_http_response=True,
)
```

#### Assert — verify the expected result

This can include:

- HTTP status;
- response contract;
- Pydantic validation;
- business rules;
- identity;
- database consistency when the test is an integration test.

```python
# ASSERT
customer_model = assert_customer_retrieved_successfully(response)

assert_customer_identity(
    customer_model,
    customer_id,
    customer["email"],
)
```

### 4.2 Complete example — GET by ID

```python
def test_get_customer_by_id(customer_helper, create_valid_customer):

    # ============================================================
    # ARRANGE
    # Create valid setup data.
    #
    # The fixture handles the POST /customers request, validates
    # the expected 201 response and response body, and registers
    # cleanup. The test receives only a clean customer dict.
    # ============================================================
    customer = create_valid_customer()

    # ============================================================
    # ACT
    # GET is the operation under test.
    #
    # We use response mode because we want the HttpResponse for
    # the GET operation, not just its parsed body.
    # ============================================================
    response = customer_helper.get_customer_by_id(
        customer["id"],
        return_http_response=True,
    )

    # ============================================================
    # ASSERT — transport
    # The test owns the HTTP status of the GET operation.
    # ============================================================
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. "
        f"Response: {response.text}"
    )

    # ASSERT — response body
    customer_model = assert_valid_customer_response(response.json)

    # Business/identity assertion.
    assert_customer_identity(
        customer_model,
        customer["id"],
        customer["email"],
    )
```

Notice the important distinction:

```text
POST /customers
    ↓
fixture setup
    ↓
status + body validation happens inside fixture
    ↓
clean customer dict
    ↓
GET /customers/{id}
    ↓
operation under test
    ↓
HttpResponse
    ↓
status/body validation
    ↓
business assertions
```

The test does **not** need to validate the POST status again because the POST is only test-data setup.

---

### 4.3 `return_http_response=False` vs `True`

The Helper normally returns parsed JSON:

```python
# Default: return_http_response=False
customer = customer_helper.get_customer_by_id(customer_id)

# customer is the parsed response body, normally a dict.
assert customer["id"] == customer_id
```

When the test needs the actual response:

```python
# Response mode
response = customer_helper.get_customer_by_id(
    customer_id,
    return_http_response=True,
)

# response is an HttpResponse object.
assert response.status_code == 200

# The body is already inside that same response.
customer = response.json

assert customer["id"] == customer_id
```

There is **no second API request** between `response` and `response.json`.

Think of it this way:

```text
return_http_response=False
    API request
        ↓
    HttpResponse
        ↓
    response.json
        ↓
    return dict


return_http_response=True
    API request
        ↓
    HttpResponse
        ↓
    return HttpResponse
        │
        ├── status_code
        ├── headers
        ├── elapsed
        ├── text
        └── json  ← body
```

### 4.4 Where should HTTP status validation live?

Use one consistent rule:

> **The test validates the HTTP status of the API operation it is testing. Validators validate the response body/data contract.**

For example:

```python
# ACT
response = customer_helper.get_customer_by_id(
    customer_id,
    return_http_response=True,
)

# ASSERT — transport
assert response.status_code == 200, (
    f"Expected 200, got {response.status_code}. "
    f"Response: {response.text}"
)

# ASSERT — response data
customer = assert_valid_customer_response(response.json)

# ASSERT — business behaviour
assert_customer_identity(customer, customer_id, customer_email)
```

This keeps responsibilities clear:

```text
API operation under test
        │
        ├── HTTP status       ← TEST
        │
        └── response body     ← VALIDATOR
```

A Validator such as `assert_valid_customer_response()` should validate the supplied
response data. It should not need to know whether the HTTP request returned `200`,
`201`, `400`, `404`, etc.

The exception is the valid-data creation fixture:

```text
create_valid_customer()
        │
        └── POST /customers
              │
              ├── assert 201       ← FIXTURE validates its setup contract
              ├── validate body   ← VALIDATOR
              ├── cleanup
              └── return dict
```

The POST above is not the operation being tested by the consuming test. It is the
fixture's responsibility to guarantee that valid test data was created successfully.

Therefore:

```text
Fixture:
    POST setup → assert expected 201 → validate body → return dict

Test:
    GET/PUT/DELETE/POST under test → assert expected status → validate body
```

For a negative scenario:

```python
# ACT
response = customer_helper.update_customer(
    customer_id,
    invalid_payload,
    return_http_response=True,
)

# ASSERT — transport
assert response.status_code == 400, (
    f"Expected 400, got {response.status_code}. "
    f"Response: {response.text}"
)

# ASSERT — error contract
assert_customer_error_response(response.json)
```

The important point is that **status validation stays with the test that owns the
operation**. This avoids having some status codes asserted in tests and others hidden
inside data validators.

### 4.5 Positive tests

A positive test can use either Level 1 or Level 2.

#### Level 1 — data is all the test needs

```python
def test_get_customer_by_id(customer_helper, create_valid_customer):

    # ARRANGE
    customer = create_valid_customer()

    # ACT
    customer_data = customer_helper.get_customer_by_id(customer["id"])

    # ASSERT
    assert customer_data["id"] == customer["id"]
```

#### Level 2 — the HTTP response is part of the assertion

```python
def test_get_customer_by_id_returns_200(
    customer_helper,
    create_valid_customer,
):

    # ARRANGE
    customer = create_valid_customer()

    # ACT
    response = customer_helper.get_customer_by_id(
        customer["id"],
        return_http_response=True,
    )

    # ASSERT
    assert response.status_code == 200

    customer_data = response.json
    assert customer_data["id"] == customer["id"]
```

Both are valid. The second exposes the HTTP layer because the status code is explicitly part of what the test verifies.

---

### 4.6 Negative tests

Negative tests normally use Level 2 because the expected error response is part of the behaviour being tested.

```python
def test_get_customer_by_id_not_found(customer_helper):

    # ARRANGE
    # Deliberately choose an ID that should not exist.
    non_existing_id = 999999

    # ACT
    response = customer_helper.get_customer_by_id(
        non_existing_id,
        return_http_response=True,
    )

    # ASSERT — transport
    assert response.status_code == 404, (
        f"Expected 404, got {response.status_code}. "
        f"Response: {response.text}"
    )

    # ASSERT — error body
    error = response.json
    assert_customer_not_found_error(error)
```

Do not use a valid-resource fixture for the invalid operation itself. A fixture such as `create_valid_customer` is designed to create **valid** state.

If a negative test needs valid setup as well as an invalid operation, it can still use a fixture:

```text
ARRANGE
    ↓
create valid resource (fixture)
    ↓
prepare invalid input
    ↓
ACT
    ↓
perform invalid operation (Helper, response=True)
    ↓
ASSERT
    ↓
expected status + error contract
```

---

### 4.7 Level 3 — when normal test layers are not enough

If a test is failing and you need to investigate the actual request/response at the lowest level, use `request_raw()`.

```python
resp, _ = APIClient.request_raw(
    method="post",
    endpoint="customers",
    payload={"email": "invalid"},
)

print(resp.status_code)
print(resp.text)
print(resp.request.headers)
```

This is a diagnostic tool, not a normal test interface.

---

## 5. 🧭 Which Interface to Use for Each HTTP Method

The framework uses the **create fixture primarily for POST/create operations**.

This distinction is important:

> **The fixture creates valid test data. It is not the mechanism used to test GET, PUT, or DELETE.**

A test for GET, PUT, or DELETE may still *use* the fixture during **Arrange** to create the resource it needs. In that case, the fixture is only preparing valid test data; the operation under test is still the GET, PUT, or DELETE call.

### Method-by-method guide

| Operation | Real example | Where is HTTP status validated? |
|---|---|---|
| **POST — valid setup** | `customer = create_valid_customer()` | **Inside the fixture** |
| **POST — valid creation under test** | `response = customer_helper.create_customer(..., return_http_response=True)` | **Inside the test** |
| **POST — negative** | `response = customer_api_raw.post(...)` | **Inside the test** |
| **GET — by ID** | `response = customer_helper.get_customer_by_id(id, return_http_response=True)` | **Inside the test** |
| **GET — list/filter/email** | `response = customer_helper.get_customer_by_email(email, return_http_response=True)` | **Inside the test** |
| **PUT — valid update** | `response = customer_helper.update_customer(id, payload, return_http_response=True)` | **Inside the test** |
| **PUT — negative** | `response = customer_helper.update_customer(id, invalid_payload, return_http_response=True)` | **Inside the test** |
| **DELETE — valid deletion** | `response = customer_helper.delete_customer(id, return_http_response=True)` | **Inside the test** |
| **DELETE — negative** | `response = customer_helper.delete_customer(invalid_id, return_http_response=True)` | **Inside the test** |
| **Raw debugging** | `resp, _ = APIClient.request_raw(...)` | **Inside the debugging code** |

The key rule is deliberately simple:

> **If the test is testing the API operation, the test validates that operation's HTTP status code.**

The `create_valid_<entity>()` fixture is the setup exception because its purpose is to
create valid test state. It validates the `POST → 201` contract before returning the
clean `dict` used by the test.

### POST — valid setup

```python
# ARRANGE
# Fixture owns the POST setup and validates 201.
customer = create_valid_customer()

customer_id = customer["id"]
```

The fixture performs:

```text
create_valid_customer()
        │
        └── POST /customers
              │
              ├── assert 201       ← FIXTURE
              ├── validate body    ← VALIDATOR
              ├── register cleanup
              └── return dict
```

The consuming test does not need to see or re-check that setup response.

### GET — operation under test

```python
# ARRANGE
customer = create_valid_customer()

# ACT
response = customer_helper.get_customer_by_id(
    customer["id"],
    return_http_response=True,
)

# ASSERT — transport
assert response.status_code == 200, (
    f"Expected 200, got {response.status_code}. "
    f"Response: {response.text}"
)

# ASSERT — body
customer_model = assert_valid_customer_response(response.json)

# ASSERT — business behaviour
assert_customer_identity(
    customer_model,
    customer["id"],
    customer["email"],
)
```

The fixture creates the precondition. The test owns the GET and therefore owns the
`200` assertion.

### PUT — operation under test

```python
def test_update_customer(customer_helper, create_valid_customer):

    # ARRANGE
    customer = create_valid_customer()

    # ACT
    response = customer_helper.update_customer(
        customer["id"],
        payload={"first_name": "Updated"},
        return_http_response=True,
    )

    # ASSERT — transport
    assert response.status_code == 200

    # ASSERT — body
    updated_customer = assert_valid_customer_response(response.json)

    # ASSERT — business behaviour
    assert updated_customer.first_name == "Updated"
```

The `PUT → 200` status belongs to the test because PUT is the operation being tested. This follows the current Customer update pattern.

### DELETE — operation under test

```python
def test_delete_customer(customer_helper, create_valid_customer):

    # ARRANGE
    customer = create_valid_customer()

    # ACT
    delete_response = customer_helper.delete_customer(
        customer["id"],
        return_http_response=True,
    )

    # ASSERT — transport
    assert delete_response.status_code == 200

    # ASSERT — body
    delete_data = delete_response.json
    assert delete_data["id"] == customer["id"]
```

Again, the fixture owns the POST setup, while the test owns the DELETE status. This follows the current Customer deletion pattern.

### Negative operation

```python
def test_update_customer_invalid_data(customer_helper, create_valid_customer):

    # ARRANGE
    customer = create_valid_customer()
    invalid_payload = {"email": "not-an-email"}

    # ACT
    response = customer_helper.update_customer(
        customer["id"],
        payload=invalid_payload,
        return_http_response=True,
    )

    # ASSERT — transport
    assert response.status_code == 400

    # ASSERT — error body
    assert_customer_error_response(response.json)
```

The same pattern applies to negative POST, GET, PUT, and DELETE tests:

```text
ACT
    ↓
API operation
    ↓
HttpResponse
    ↓
assert expected HTTP status       ← TEST
    ↓
validate response/error body      ← VALIDATOR
```

### Why we do not hide status validation inside normal response-data Validators

A data Validator should answer questions such as:

```text
Is this a valid Customer?
Does this error have the expected structure?
Does this response contain the expected customer?
Does the returned data satisfy the business rules?
```

The test should answer:

```text
Did the API operation return the HTTP status expected by this scenario?
```

Keeping these responsibilities separate gives us one predictable rule across the framework:

```text
POST / setup fixture
    → fixture validates 201
    → validator validates body
    → clean dict

POST / GET / PUT / DELETE under test
    → test validates HTTP status
    → validator validates body
    → test validates business behaviour

Negative operation
    → test validates error status
    → validator validates error body
```

### The rule to remember

> **The fixture owns valid POST setup. The test owns the HTTP status of the operation it is actually testing. Validators validate the response body/data contract.**



## 6. 🔬 Debugging with `request_raw()`

`request_raw()` bypasses the normal `HttpResponse` abstraction and exposes the underlying response.

```python
resp, _ = APIClient.request_raw(
    method="post",
    endpoint="customers",
    payload={"email": "invalid"},
)

print(resp.status_code)
print(resp.text)
print(resp.request.headers)
```

⚠️ Notes:

- Returns a raw `requests.Response`, not `HttpResponse`
- JSON parsing may fail — you're responsible for handling it
- It bypasses the normal test abstraction
- It should not be used for normal test assertions

Use it when you need to answer a debugging question such as:

> "What exactly did the server receive and what exactly did it send back?"

---

## 7. ⚠️ Core Rules

### Rule 1 — Use Arrange → Act → Assert

- **Arrange:** prepare valid state and test inputs.
- **Act:** perform the operation under test.
- **Assert:** verify transport, response data, business behaviour, and DB state where applicable.

### Rule 2 — Fixtures are strict

Fixtures like `create_valid_customer`:

- ALWAYS return a `dict`
- ALWAYS return valid data
- ALWAYS validate the expected creation status before returning
- NEVER return an `HttpResponse`
- NEVER return invalid objects

### Rule 3 — `return_http_response` controls the interface, not whether the body exists

```text
False → return parsed body (dict)
True  → return HttpResponse containing metadata + body
```

`True` does **not** cause a second request. The body is already available through:

```python
response.json
```

### Rule 4 — Validate transport before validating the response body

When a test receives an `HttpResponse`, the logical validation order is:

1. Transport status validation
2. JSON extraction
3. Structure validation (Pydantic model)
4. Business validation
5. Database validation, when applicable

The test performs the HTTP status assertion; the Validator then validates the response body/data.

### Rule 5 — Use the right interface for the test's intent

| Test need | Use |
|---|---|
| Valid resource as setup/precondition | Level 1 — fixture |
| Clean validated data | Level 1 — Helper default return |
| Inspect status / headers / timing | Level 2 — Helper response mode |
| Inspect an error response | Level 2 — Helper response mode |
| Raw wire-level investigation | Level 3 — `request_raw()` |

### Rule 6 — Don't mix abstraction levels

❌ Wrong:

```python
customer = create_valid_customer()

# Fixture returns a dict, not an HttpResponse.
assert customer.status_code == 201
```

The fixture already validated the creation status before returning.

✅ Correct when testing fixture setup data:

```python
customer = create_valid_customer()

assert customer["id"]
assert customer["email"]
```

✅ Correct when testing the GET operation itself:

```python
response = customer_helper.get_customer_by_id(
    customer["id"],
    return_http_response=True,
)

customer_model = assert_customer_retrieved_successfully(response)
```

### Rule 7 — Keep responsibilities separate

- Helpers orchestrate; they do not assert.
- Validators validate data; they do not fetch it.
- Fixtures create validated test data and handle cleanup.
- Tests verify behaviour and business outcomes.
- `request_raw()` is for low-level debugging, not normal test design.

---

## 8. 📦 Fixtures (Factory Pattern)

Fixtures act as **gatekeepers for test data**.

A fixture that creates a valid resource should:

1. Call the Helper
2. Receive an `HttpResponse`
3. Validate the expected transport status
4. Extract JSON
5. Validate the response structure/domain rules
6. Register cleanup
7. Return a clean `dict`

Example flow:

```text
fixture
   │
   ▼
Helper
   │
   ▼
HttpResponse
   │
   ├── expected status
   │
   ▼
response.json
   │
   ▼
Pydantic / domain validation
   │
   ▼
cleanup registration
   │
   ▼
clean dict
```

The test therefore does not need to inspect the HTTP response used to create its setup data.

The fixture's contract is:

```text
ALWAYS → valid data
ALWAYS → clean dict
NEVER  → HttpResponse
NEVER  → invalid data
```

This does not mean fixtures are only for "simple" or "junior" tests. They are the standard way to prepare valid test state.

**Structure validation uses Pydantic models:**

```python
customer_model = CustomerModel(**customer)
```

Pydantic provides strict typing, clearer validation errors, easier debugging, and better IDE support.

---

## 9. 🔍 Validators

Validators are responsible for:

- Validating response structure
- Validating business rules
- Validating DB consistency when required
- Providing reusable response/data contracts

Validators must **not** fetch data themselves. The pattern is always:

```text
fetch → validate
```

A Test or Fixture fetches the data (via a Helper), then hands it to a Validator.

A Validator may receive an `HttpResponse` so it can extract or validate the response
body, but the HTTP status assertion belongs to the test.

For example:

```python
assert response.status_code == 200
customer_model = assert_valid_customer_response(response.json)
```

Other Validators receive already-parsed data:

```python
customer_model = assert_single_customer_by_email(
    customers,
    email,
)
```

The important distinction is:

- **Response/data Validator:** validates the supplied response content.
- **Business Validator:** validates business rules and expectations.
- **DB Validator:** validates consistency with persisted data.
- **HTTP status assertion:** belongs to the test, except for the valid-creation fixture's own setup contract.

💡 If a test's validation touches the database, mark it `@pytest.mark.integration`.

---

## 10. 🧠 Helpers

Helpers are responsible for:

- Calling APIs
- Orchestrating workflows
- Combining API + DAO/DB logic where needed
- Providing either a clean parsed result or the `HttpResponse`, depending on `return_http_response`

Helpers must **not** assert.

For example:

```python
# Clean data mode
customer = customer_helper.get_customer_by_id(customer_id)

# Response mode
response = customer_helper.get_customer_by_id(
    customer_id,
    return_http_response=True,
)
```

The Helper decides which representation to return; the test or Validator decides how the returned data should be validated.

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

> Each business entity owns its own smoke, integration, regression, and performance tests. `tests/shared/` is reserved exclusively for framework-level test suites (see §13).

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

 **3. Test type**

| Marker | Meaning |
|---|---|
| `integration` | API + DB validation |
| `contract` | API contract and transport validation, including schema validation |
| `negative` | Invalid input tests |
| `e2e` | Multi-step workflow |
| `graphql` | GraphQL API tests |
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

GitHub Actions executes these marker groups through dedicated
workflows (Smoke, Integration, Regression, Performance,
Contract, Security and Preflight).

**Big picture:**

- Domain → `customers`, `orders`, etc.
- Execution → `smoke`, `sanity`, `regression`
- Type → `integration`, `contract`, `negative`, `e2e`, `graphql`
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

The framework also contains shared tests that validate framework infrastructure, API contracts, security, and environment-related behavior **before** entity-specific tests run. These execute once for the whole framework rather than once per entity — where a suite must cover every entity (Contract, Security), it discovers entities dynamically and iterates internally, so CI reports show **Scope: Shared Framework** rather than an entity name, and adding a new entity extends coverage automatically without touching the tests.

```
tests/shared/
    preflight/
        test_logging_globals.py
    security/
        test_authentication_matrix.py
        test_authentication_success.py
    contracts/
           rest/
              test_api_connectivity.py
              test_response_format.py
           graphql/
              test_graphql_connectivity.py
              test_product_mutation_schema.py
```

**Preflight** — verifies the test harness itself before the full suite runs:
logging configuration, correlation/nodeid propagation, structured logging,
pytest configuration, markers, CLI flags, and other framework-level checks.
Preflight must **not** call live APIs or require Docker, OAuth credentials,
WooCommerce, or a database.

**Contract** — validates API contracts and transport behavior:
connectivity, HTTP status, response format, content-type, schema,
serialization, and GraphQL schema/transport contracts. Entities are
discovered automatically where applicable.

GraphQL contract tests therefore belong to the shared Contract suite,
while GraphQL business behavior remains under the corresponding entity's
`graphql/` directory.


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
3. Validators validate response/data — they don't fetch data or own HTTP status assertions
4. Tests validate the HTTP status of the operation under test and verify business logic
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
