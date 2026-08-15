# 📘 API Client Architecture & Request Flow

## 🧠 Overview

This framework provides a **clean, layered architecture** for API testing.

Goals:

- ✅ Junior-friendly
- ✅ Best-practice grade
- ✅ Clear separation of concerns
- ✅ Easy debugging & observability

---

# 🧱 Architecture

The framework uses a shared HTTP transport with protocol-specific API clients.

```text
                         API Tests
                            │
              ┌─────────────┴─────────────┐
              │                           │
            REST                       GraphQL
              │                           │
          APIClient                 GraphQLClient
              │                           │
          HttpResponse             GraphQLResponse
              │                           │
              └───────────┬───────────────┘
                          │
                     HttpClient
                          │
                  requests.Session
                          │
                       Server
```

### 🧾 Protocol responsibilities

| Protocol | Client | Response |
|---|---|---|
| REST | `APIClient` | `HttpResponse` |
| GraphQL | `GraphQLClient` | `GraphQLResponse` |

Both protocols reuse `HttpClient` for low-level HTTP transport.

### 🔗 Shared by REST and GraphQL

`HttpClient` is protocol-agnostic.

It does not know whether a request belongs to REST or GraphQL. It only
provides the low-level HTTP transport used by both clients.

---

# 🔹 1. HttpClient — Transport Layer

## 🎯 Responsibility

Send HTTP requests to the server.

```python
response = self.session.request(...)
```

## ✔ What it does

- Uses `requests.Session`
- Sends HTTP requests
- Returns the raw `requests.Response`

## ❌ What it does NOT do

- No retries
- No logging
- No parsing
- No validation

Think:

```text
"Just send the request and give me the raw response"
```

---

# 🔹 2. APIClient — REST Orchestration Layer

## 🎯 Responsibility

Manage the full lifecycle of a REST request.

```python
response = APIClient.get("customers")
```

## ✔ What it does

- Builds URLs (`_build_url`)
- Applies retry logic (`_request_with_backoff`)
- Logs request/response activity
- Converts the raw response into `HttpResponse`

## ❌ What it does NOT do

- No schema validation
- No business logic
- No assertions

Think:

```text
"Prepare the REST request properly and handle its response"
```

## 🌍 Endpoint Resolution

`APIClient` does not hardcode API URLs.

The active base URL is resolved from the framework environment configuration:

```text
API_ENV
   ↓
config_<entity>.py
   ↓
APIClient
```

This keeps authentication, infrastructure selection, and request execution
separated.

For more information see:

`docs/framework/README_ENVIRONMENT_CONFIG_GUIDE.md`

```text
APIClient
 ├── _build_url()
 ├── _request_with_backoff()
 └── HttpResponse
```

---

# 🔹 3. GraphQLClient — GraphQL Orchestration Layer

GraphQL uses the same low-level HTTP transport as REST but has a different
request and response contract.

```text
GraphQLClient
      ↓
HttpClient
      ↓
requests.Session
      ↓
GraphQL endpoint
```

## 📑 Responsibility

`GraphQLClient`:

- accepts the GraphQL endpoint;
- executes GraphQL queries and mutations;
- builds the GraphQL JSON payload;
- delegates HTTP transport to `HttpClient`;
- measures request duration;
- converts the raw HTTP response into `GraphQLResponse`.

## ❌ It does NOT

- validate GraphQL schemas;
- perform test assertions;
- contain business logic;
- implement entity-specific behavior;
- determine whether a response satisfies a particular test.

`GraphQLClient` is therefore an infrastructure/orchestration component.

For GraphQL-specific response semantics and testing patterns, see:

`docs/development/README_GRAPHQL_TESTING_GUIDE.md`

---

# 🔹 4. Response Abstractions

## 4.1 HttpResponse — REST

### 🎯 Responsibility

Provide a safe, structured REST response object.

```python
response.status_code
response.json
response.text
```

### ✔ What it does

- Safe JSON parsing
- Normalized structure
- Consistent interface

### ❌ What it does NOT do

- No HTTP calls
- No retries

Think:

```text
"Clean, safe version of the REST response"
```

### 🧠 Key distinction

| Concept | Where it happens |
|---|---|
| Send JSON | `HttpClient` (`json=payload`) |
| Parse JSON | `HttpResponse` |

---

## 4.2 GraphQLResponse — GraphQL

GraphQL uses a dedicated response abstraction because GraphQL success cannot
be determined from HTTP status alone.

A GraphQL response may return HTTP 200 while containing GraphQL errors.

```text
HTTP response
     ↓
GraphQLResponse
     ├── status_code
     ├── data
     ├── errors
     └── ok
```

Unlike REST, **HTTP 200 does not necessarily mean that the GraphQL operation
succeeded**.

---

# 🔄 REST Request Flow

```text
pytest
 │
 ▼
Test
 │
 ▼
CustomersApi / Helper
 │
 ▼
APIClient.get/post
 │
 ▼
_request_with_backoff
 │
 ▼
HttpClient.request
 │
 ▼
requests.Session.request
 │
 ▼
🌐 HTTP CALL → Server
 │
 ▼
requests.Response (RAW)
 │
 ▼
HttpResponse.from_http_requests
 │
 ▼
HttpResponse (CLEAN)
 │
 ▼
Test assertions
```

## 🧠 REST flow in more detail

```text
pytest
│
▼
Test File (e.g. test_create_customer.py)
│
▼
Fixture (e.g. create_valid_customer / raw_customer_api)
│
▼
CustomersHelper (business-friendly layer)
│
▼
CustomersApi (API layer)
│
▼
APIClient
│
├── _request()
│   ├── _build_url()
│   └── _request_with_backoff()
│       │
│       ▼
│   HttpClient.request()
│       │
│       ▼
│   requests.Session.request()
│       │
│       ▼
│   🌐 HTTP CALL → Server
│       │
│       ▼
│   requests.Response ← RAW RESPONSE
│
▼
_handle_response()
│
├── HttpResponse.from_http_requests()
│   │
│   ▼
│   HttpResponse (parsed + structured)
│
├── Logging
│
▼
CustomersApi returns HttpResponse
│
▼
CustomersHelper (optional)
│   └── extracts response.json → dict
│
▼
Validators
│
▼
TEST ASSERTIONS ✅
```

---

# 🔄 GraphQL Request Flow

GraphQL currently uses a deliberately thinner path than the REST business
layer.

```text
pytest
 │
 ▼
GraphQL test
 │
 ▼
graphql_client fixture
 │
 ▼
GraphQLClient
 │
 ▼
HttpClient
 │
 ▼
requests.Session
 │
 ▼
🌐 GraphQL endpoint
 │
 ▼
requests.Response (RAW)
 │
 ▼
GraphQLResponse
 │
 ├── status_code
 ├── data
 ├── errors
 └── ok
 │
 ▼
Test assertions
```

The GraphQL client does not introduce a GraphQL-specific business helper or
entity API layer at this stage. Entity-specific GraphQL behavior is tested
directly through the shared `graphql_client` fixture.

---

# 🚨 Environment Validation (Framework-Level)

The API client is used by a session-scoped pytest fixture that performs a
one-time environment validation before tests run.

This is not part of the request lifecycle itself. It is a framework-level
safety mechanism that prevents tests from running against an invalid or
incomplete environment.

---

# 🧪 Validation Layer

After a protocol-specific response object is returned, validation happens
outside the transport layer.

## REST

```text
HttpResponse
     ↓
Validators
     ↓
Pydantic Models
     ↓
DB Validators
```

## GraphQL

GraphQL first distinguishes HTTP-level success from GraphQL-level errors.

```text
GraphQLResponse
     ↓
GraphQL error handling
     ↓
Schema / domain validation
     ↓
Business assertions
```

The protocol clients themselves do not perform test assertions or business
validation.

---

# 🧪 Shared Test Suites (Framework-Level Tests)

The framework also contains shared tests that validate infrastructure,
security, and environment behavior before or independently of
entity-specific tests.

Directory structure:

```text
tests/shared/
├── preflight/
│   └── test_logging_globals.py
├── security/
│   ├── test_authentication_matrix.py
│   └── test_authentication_success.py
└── contracts/
    ├── rest/
    │   ├── error_schema.py
    │   ├── test_response_format.py
    │   └── test_api_connectivity.py
    └── graphql/
        ├── test_graphql_connectivity.py
        └── test_product_mutation_schema.py
```

## Preflight tests

Verify the test environment and framework configuration before executing the
full test suite.

Examples:

- API connectivity
- logging configuration
- environment validation

## Security tests

Validate authentication and access-control behavior.

Example matrix:

```text
4 entities
× 4 HTTP methods
× 3 invalid credential cases
= 48 security tests
```

## Contract tests

Validate the API contracts exposed by the framework.

Contract tests are organized by API protocol:

```text
tests/shared/contracts/
├── rest/
│   ├── error_schema.py
│   ├── test_response_format.py
│   └── test_api_connectivity.py
└── graphql/
    ├── test_graphql_connectivity.py
    └── test_product_mutation_schema.py
```

REST contract tests validate the HTTP/REST response contract, including
response format, connectivity, and error structure.

GraphQL contract tests validate the GraphQL transport and schema contract,
including endpoint connectivity and the schema required by GraphQL operations.

Contract tests are framework-level tests. They do not belong to a specific
business entity and are executed separately from entity-specific API tests.

When adding a new API protocol, its contract tests should be placed under the
corresponding protocol directory.

---

# 💡 Key Concept

The framework separates HTTP transport from protocol-specific request and
response handling.

### REST

```text
Server
  ↓
requests.Response
  ↓
HttpResponse
  ↓
Test
```

### GraphQL

```text
GraphQL endpoint
  ↓
requests.Response
  ↓
GraphQLResponse
  ↓
Test
```

Both paths share `HttpClient`.

---

# 🧠 Design Philosophy

## Transport layer responsibilities

- Send HTTP requests
- Receive raw responses
- Provide protocol-agnostic HTTP transport

## Protocol client responsibilities

### REST — `APIClient`

- Manage REST request lifecycle
- Resolve URLs
- Apply REST retry behavior
- Produce `HttpResponse`

### GraphQL — `GraphQLClient`

- Build GraphQL request payloads
- Execute queries and mutations
- Produce `GraphQLResponse`

## Validation layer responsibilities

- Validate response structure
- Validate schemas and models
- Validate business rules
- Validate API/DB consistency

## Tests responsibilities

- Verify expected behavior
- Perform business assertions

---

# 🔍 REST: requests.Response vs HttpResponse

| Feature | `requests.Response` | `HttpResponse` |
|---|---|---|
| Source | `requests` library | Your framework |
| JSON access | `response.json()` | `response.json` |
| Safe parsing | ❌ No | ✅ Yes |
| Intended usage | Debugging / low-level access | Standard REST testing |

---

# 🔬 request_raw() — REST Debugging Tool

## 🎯 Purpose

Low-level access to a raw REST response while still using framework
infrastructure.

```python
resp, elapsed = APIClient.request_raw(...)
```

## ⚠️ Important

- Returns `requests.Response`
- Skips `HttpResponse`
- JSON parsing may fail
- Provides no response abstraction

---

# 🧪 Real Debugging Examples

## 🔹 Debug unexpected API error

```python
resp, _ = raw_customer_api.request_raw(
    method="post",
    endpoint="customers",
    payload={"email": "bad"}
)

print("STATUS:", resp.status_code)
print("BODY:", resp.text)

assert resp.status_code == 400
```

## 🔹 Inspect request details

```python
resp, _ = raw_customer_api.request_raw(
    method="post",
    endpoint="customers",
    payload={"email": "bad"}
)

print("REQUEST URL:", resp.request.url)
print("REQUEST HEADERS:", resp.request.headers)
print("REQUEST BODY:", resp.request.body)
```

## 🔹 Handle non-JSON response

```python
resp, _ = raw_customer_api.request_raw(
    method="get",
    endpoint="customers?invalid_param=%%%"
)

print("RAW TEXT:", resp.text)

try:
    data = resp.json()
except Exception:
    print("Response is NOT valid JSON")
```

## 🔹 Compare raw vs wrapped

```python
raw_resp, _ = raw_customer_api.request_raw("get", "customers")
wrapped_resp = raw_customer_api.get("customers")

print("RAW json():", raw_resp.json())
print("WRAPPED json:", wrapped_resp.json)

assert raw_resp.status_code == wrapped_resp.status_code
```

---

# ⚠️ When NOT to use request_raw()

- ❌ Normal tests
- ❌ Validation
- ❌ Schema checks
- ❌ Helpers

Use the normal framework client for standard REST testing.

---

# ✅ Recommended REST Usage

```python
response = customer_api.get("customers")

assert response.status_code == 200
assert response.json
```

---

# 🔥 HttpClient vs request_raw vs get/post

| Method | Purpose |
|---|---|
| `HttpClient.request` | Low-level transport |
| `request_raw` | REST debugging |
| `APIClient.get/post` | Standard REST usage |

Both `HttpClient.request()` and `request_raw()` ultimately reach the
`requests` layer, but they operate at different abstraction levels.

| | `request_raw()` | `HttpClient.request()` |
|---|---|---|
| Layer | APIClient | HttpClient |
| URL handling | Builds endpoint → full URL | Expects full URL |
| Auth | Uses APIClient configuration | Handled internally |
| Retries | Yes, via APIClient backoff | No |
| Logging | Minimal / none | None |
| Intended use | Testing/debugging | Transport only |

---

# ✅ Best Practices

## Transport validation

```python
assert response.status_code == 200
```

## Business validation

```python
assert data["id"]
```

Keep transport, protocol orchestration, validation, and business assertions
separate.

---

# 🧠 Mental Model

```text
                         ┌── APIClient ───── HttpResponse
                         │
HttpClient ──────────────┤
                         │
                         └── GraphQLClient ─ GraphQLResponse

Helper → business/domain operations
Test   → validation + assertions
```

The important rule is:

> `HttpClient` transports. Protocol clients orchestrate. Response objects
> represent protocol-specific results. Tests validate behavior.

---

# 🚀 Summary

- `HttpClient` provides shared low-level HTTP transport.
- `APIClient` orchestrates REST requests.
- `GraphQLClient` orchestrates GraphQL operations.
- `HttpResponse` represents REST responses.
- `GraphQLResponse` represents GraphQL responses.
- REST and GraphQL share transport but have different request/response
  contracts.
- `request_raw()` is a REST debugging tool.
- Validation and business assertions remain outside the transport layer.
- Keep protocol-specific responsibilities separate.
