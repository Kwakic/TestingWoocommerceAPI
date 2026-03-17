# 📘 API Client Architecture & Request Flow

## 🧠 Overview

This framework provides a **clean, layered architecture** for API testing.

Goals:
- ✅ Junior-friendly
- ✅ Enterprise-grade
- ✅ Clear separation of concerns
- ✅ Easy debugging & observability

---

# 🧱 Architecture — 3 Core Layers

```
HttpClient        → LOW LEVEL (transport)
APIClient    → MIDDLE (orchestration)
HttpResponse      → HIGH LEVEL (structured response)
```

---

# 🔹 1. HttpClient (Transport Layer)

### 🎯 Responsibility
Send HTTP requests to the server.

```python
response = self.session.request(...)
```

### ✔ What it does
- Uses `requests.Session`
- Sends HTTP request
- Returns **raw `requests.Response`**

### ❌ What it does NOT do
- No retries
- No logging
- No parsing
- No validation

👉 Think:
```
"Just send the request and give me raw response"
```

---

# 🔹 2. APIClient (Orchestration Layer)

### 🎯 Responsibility
Manage the full lifecycle of a request.

```python
response = APIClient.get("customers")
```

### ✔ What it does
- Builds URL (`_build_url`)
- Applies retry logic (`_request_with_backoff`)
- Logs request/response
- Converts → `HttpResponse`

### ❌ What it does NOT do
- No schema validation
- No business logic
- No assertions

👉 Think:
```
"Prepare request properly + handle response"
```

---

# 🔹 3. HttpResponse (Abstraction Layer)

### 🎯 Responsibility
Provide a safe, structured response object.

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

👉 Think:
```
"Clean, safe version of response"
```

### 🧠 KEY DISTINCTION (VERY IMPORTANT)

| Concept                 | Where it happens                 |
| ----------------------- | -------------------------------- |
| ✅ Send JSON (request)   | HttpClient (`json=payload`)      |
| ✅ Parse JSON (response) | HttpResponse (`response.json()`) |

---

# 🔄 FULL REQUEST FLOW

```
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

### 🧠 More in detail

```
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
APIClient (transport orchestrator)
│
├── _request()
│     │
│     ├── _build_url()
│     │
│     ├── _request_with_backoff()
│     │       │
│     │       ▼
│     │   HttpClient.request()
│     │       │
│     │       ▼
│     │   requests.Session.request()
│     │       │
│     │       ▼
│     │   🌐 HTTP CALL → Server
│     │       │
│     │       ▼
│     │   requests.Response  ← RAW RESPONSE
│     │
│     ▼
│   _handle_response()
│       │
│       ├── HttpResponse.from_http_requests()
│       │       │
│       │       ▼
│       │   HttpResponse (parsed + structured)
│       │
│       ├── Logging (status, duration, payload)
│       │
│       ▼
│   return HttpResponse
│
▼
CustomersApi returns HttpResponse
│
▼
CustomersHelper (optional)
│   └── extracts response.json → dict
│
▼
Validators (schema + assertions)
│
▼
TEST ASSERTIONS ✅
```

---

# 🧠 Key Concept

```
Server → requests.Response → HttpResponse → dict → test
```

---

# 🔍 requests.Response vs HttpResponse

| Feature | requests.Response | HttpResponse |
|--------|------------------|-------------|
| Source | requests library | Your framework |
| JSON access | response.json() | response.json |
| Safe | ❌ No | ✅ Yes |
| Usage | Debugging | Standard |

---

# 🔬 request_raw() — Debugging Tool

## 🎯 Purpose

Low-level access to raw response while still using framework infrastructure.

```python
resp, elapsed = APIClient.request_raw(...)
```

---

## ⚠️ Important

- Returns `requests.Response`
- Skips HttpResponse
- JSON parsing may fail
- No abstraction

---

# 🧪 Real Debugging Examples

---

## 🔹 Debug unexpected API error

```python
resp, _ = APIClient.request_raw(
    method="post",
    endpoint="customers",
    payload={"email": "bad"}
)

print(resp.status_code)
print(resp.text)
```

---

## 🔹 Inspect what was sent

```python
print(resp.request.url)
print(resp.request.headers)
print(resp.request.body)
```

---

## 🔹 Non-JSON response

```python
try:
    data = resp.json()
except Exception:
    print("Not JSON")
```

---

## 🔹 Compare raw vs wrapped

```python
raw_resp, _ = APIClient.request_raw("get", "customers")
wrapped = APIClient.get("customers")

print(raw_resp.json())
print(wrapped.json)
```
## 🔥 Test real examples:

### 🔹 Example 1 — Debug unexpected error
```
def test_debug_create_customer(raw_customer_api):
    payload = {"email": "test@test.com"}  # missing required fields

    resp, _ = raw_customer_api.request_raw(
        method="post",
        endpoint="customers",
        payload=payload
    )

    print("STATUS:", resp.status_code)
    print("BODY:", resp.text)

    assert resp.status_code == 400
```
### 🔹 Example 2 — Inspect request details
```
def test_debug_request_details(raw_customer_api):
    resp, _ = raw_customer_api.request_raw(
        method="post",
        endpoint="customers",
        payload={"email": "bad"}
    )

    print("REQUEST URL:", resp.request.url)
    print("REQUEST HEADERS:", resp.request.headers)
    print("REQUEST BODY:", resp.request.body)
```
### 🔹 Example 3 — Handle non-JSON response
```
def test_debug_non_json(raw_customer_api):
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
### 🔹 Example 4 — Compare raw vs HttpResponse
```
def test_compare_raw_vs_wrapped(raw_customer_api):
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

---

# ✅ Recommended Usage

```python
response = customer_api.get("customers")

assert response.status_code == 200
assert response.json
```

---

# 🔥 HttpClient vs request_raw vs get/post

| Method | Purpose |
|------|--------|
| HttpClient.request | Transport only |
| request_raw | Debugging |
| get/post | Standard |

Both ultimately hit requests and return requests.Response

|              | `request_raw()`              | `HttpClient.request()` |
| ------------ | ---------------------------- | ---------------------- |
| Layer        | APIClient (mid-level)   | HttpClient (low-level) |
| URL handling | ✅ builds endpoint → full URL | ❌ expects full URL     |
| Auth         | ✅ already configured         | ✅ handled internally   |
| Retries      | ✅ YES (via backoff)          | ❌ NO                   |
| Logging      | ❌ minimal / none             | ❌ none                 |
| Intended use | testing/debugging            | transport only         |
---

# 🧠 Mental Model

```
HttpClient → send request
request_raw → debug safely
get/post → normal usage
```

---

# 🚀 Summary

- Use HttpResponse for 99% of cases
- Use request_raw only for debugging
- Keep layers clean and separate
