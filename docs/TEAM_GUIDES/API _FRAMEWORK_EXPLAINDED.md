# API Testing Framework -- Response Flow Explained

## 🔷 Core Concept

Your framework now separates responsibilities cleanly:

-   HttpClient → sends HTTP request (NO parsing)
-   HttpResponse = parses response
-   RequestUtility → wraps response into HttpResponse
-   API layer → returns `.json`
-   Helper layer → returns dict (business-ready)
-   Tests → validate

------------------------------------------------------------------------

## 🔷 HttpClient (LOW LEVEL)

``` python
class HttpClient:
    """
    Responsibilities:
    ✔ Sends HTTP request
    ✔ Returns raw requests.Response

    Does NOT:
    ✘ Parse JSON
    ✘ Validate response
    ✘ Perform assertions
    """
```

👉 Important: - `json=` in request → means "send JSON payload" - NOT
parsing response

------------------------------------------------------------------------

## 🔷 HttpResponse (WRAPPER)

``` python
HttpResponse(
    status_code,
    headers,
    json,
    text,
    url,
    elapsed
)
```

👉 JSON parsing happens HERE:

``` python
json_data = response.json()
```

------------------------------------------------------------------------

### 🧠 KEY DISTINCTION (VERY IMPORTANT)

| Concept                 | Where it happens                 |
| ----------------------- | -------------------------------- |
| ✅ Send JSON (request)   | HttpClient (`json=payload`)      |
| ✅ Parse JSON (response) | HttpResponse (`response.json()`) |

------------------------------------------------------------------------

## 🔷 Flow (IMPORTANT)

### ✅ Positive flow

    test
     ↓
    fixture
     ↓
    helper
     ↓
    API
     ↓
    RequestUtility
     ↓
    HttpResponse
     ↓
    helper extracts .json
     ↓
    test receives dict

👉 Tests DO NOT see HttpResponse

------------------------------------------------------------------------

### ❌ Negative / raw flow

    test
     ↓
    raw_customer_api
     ↓
    RequestUtility
     ↓
    HttpResponse
     ↓
    test uses:
        .status_code
        .json

------------------------------------------------------------------------

## 🔷 RULES

  Layer            Returns
  ---------------- -------------------
  HttpClient       requests.Response
  RequestUtility   HttpResponse
  API              HttpResponse
  Helper           dict
  Raw tests        HttpResponse

------------------------------------------------------------------------

## 🔷 Best Practices

### Transport validation

    assert_status_code(http_response, 400)

### Business validation

    assert_customer_creation_failed(response_dict)

------------------------------------------------------------------------

## 🔷 Common Mistake

❌ Mixing types:

    response = http_response.json
    assert response.status_code

✅ Correct:

    assert_status_code(http_response, 400)
    response = http_response.json

------------------------------------------------------------------------

## 🔷 Final Mental Model

-   HttpResponse = transport
-   dict = business

------------------------------------------------------------------------

## 🔷 Summary

✔ HttpClient → send only\
✔ HttpResponse → normalize response\
✔ Helpers → return clean dict\
✔ Tests → validate
