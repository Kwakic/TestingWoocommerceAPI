# 🚀 API Testing Framework — COMPLETE Architecture Guide

---

# 🧠 OVERVIEW

This framework follows a **clean, layered, enterprise architecture** designed for:

- ✅ Clarity
- ✅ Maintainability
- ✅ Debuggability
- ✅ Junior-friendly onboarding

---

# 🧱 CORE ARCHITECTURE (3 LAYERS)

```
HttpClient        → LOW LEVEL (transport)
APIClient         → MIDDLE (orchestration)
HttpResponse      → HIGH LEVEL (structured response)
```

---

# 🔹 1. HttpClient (Transport Layer)

### 🎯 Purpose
Send HTTP request to server.

### ✔ Responsibilities
- Sends request using requests.Session
- Returns raw `requests.Response`

### ❌ Does NOT
- Parse JSON
- Retry
- Log
- Validate

👉 Mental model:
```
"Just send request and return raw response"
```

---

# 🔹 2. APIClient (Orchestration Layer)

### 🎯 Purpose
Manage full request lifecycle

### ✔ Responsibilities
- Build URL
- Retry logic (backoff)
- Logging
- Convert → HttpResponse

### FLOW

```
_request()
   ↓
_request_with_backoff()
   ↓
HttpClient.request()
   ↓
_handle_response()
```

---

# 🔹 3. HttpResponse (Abstraction Layer)

### 🎯 Purpose
Provide safe, structured response

### ✔ Features
- Safe JSON parsing
- Consistent interface
- Clean structure

---

# 🔄 FULL EXECUTION FLOW (END-TO-END) FOR POSITIVE TEST

```
pytest
 │
 ▼
Test
 │
 ▼
Fixture
 │
 ▼
Helper
 │
 ▼
API Layer
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
🌐 SERVER
 │
 ▼
requests.Response (RAW)
 │
 ▼
HttpResponse.from_requests
 │
 ▼
HttpResponse (SAFE)
 │
 ▼
Helper extracts .json
 │
 ▼
Test assertions
```

---

# 🔍 RESPONSE FLOW SIMPLIFIED

```
Server
  ↓
requests.Response (raw)
  ↓
HttpResponse (parsed)
  ↓
dict (business)
  ↓
Test
```
# 🔄 FULL EXECUTION FLOW (END-TO-END) FOR NEGATIVE TEST
```
test
 ↓
raw_customer_api (fixture)
 ↓
APIClient.post()
 ↓
_request()
 ↓
_request_with_backoff()
 ↓
HttpClient.request()
 ↓
requests.Session.request()
 ↓
🌐 SERVER
 ↓
requests.Response (RAW)
 ↓
_handle_response()
 ↓
HttpResponse
 ↓
returned to test
```
---

# 🔍 requests.Response vs HttpResponse

| Feature | requests.Response | HttpResponse |
|--------|------------------|-------------|
| JSON | response.json() | response.json |
| Safe | ❌ No | ✅ Yes |
| Use | Debugging | Standard |

---

# 🔬 request_raw() — DEBUG TOOL

### 🎯 Purpose
Low-level debugging access

```
resp, elapsed = APIClient.request_raw(...)
```

### ⚠️ Important
- Returns raw `requests.Response`
- Skips HttpResponse
- JSON parsing may fail

---

# 🧪 DEBUGGING EXAMPLES

## 🔹 Debug API error

```
resp, _ = APIClient.request_raw("post", "customers", payload)

print(resp.status_code)
print(resp.text)
```

---

## 🔹 Inspect request

```
print(resp.request.url)
print(resp.request.headers)
print(resp.request.body)
```

---

## 🔹 Compare raw vs wrapped

```
raw_resp, _ = APIClient.request_raw("get", "customers")
wrapped = APIClient.get("customers")

print(raw_resp.json())
print(wrapped.json)
```

---

# ⚠️ WHEN NOT TO USE request_raw

❌ Normal tests  
❌ Validation  
❌ Business logic  

---

# 📊 LAYER CONTRACTS

```
HttpClient        → requests.Response
APIClient         → HttpResponse
API               → HttpResponse
Helper            → dict
Test              → assertions
Debug             → requests.Response
```

---

# 🧠 MENTAL MODEL

```
HttpClient      → send request
APIClient       → manage request
HttpResponse    → safe response
Helper          → business data
Test            → validate
```

---

# ⚠️ COMMON MISTAKE

❌ Wrong:
```
response = http_response.json
assert response.status_code
```

✅ Correct:
```
assert http_response.status_code == 200
data = http_response.json
```

---

# ✅ BEST PRACTICES

## Transport validation
```
assert response.status_code == 200
```

## Business validation
```
assert data["id"]
```

---

# 🚀 FINAL SUMMARY

✔ HttpClient → raw transport  
✔ APIClient  → orchestration  
✔ HttpResponse → safe abstraction  
✔ Helpers → clean business data  
✔ Tests → validation  
✔ request_raw → debugging only  

---

# 🔥 FINAL TAKEAWAY

```
HttpClient → raw
APIClient  → controlled
HttpResponse → safe
Helper → business
Test → validation
```
