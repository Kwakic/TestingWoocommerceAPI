# API Testing Standards & Guidelines --- TestEcommerceAPI 🚀

This document defines how to write consistent, maintainable,
enterprise-grade API tests.

------------------------------------------------------------------------

# 🧠 Core Principles

-   ✅ Test layer owns validation
-   ✅ Fixtures act as Gatekeepers (validate + normalize)
-   ❌ Transport layers (RequestUtility / API) DO NOT validate
-   ✅ Keep tests clean, readable, and business-focused
-   ✅ Fail fast on transport errors

------------------------------------------------------------------------

# 🧱 Framework Layers

  Layer            Responsibility
  ---------------- --------------------------------------------
  HttpClient       Sends raw HTTP requests (requests library)
  RequestUtility   Wraps HTTP calls and returns HttpResponse
  HttpResponse     Parsed + normalized response object
  API Layer        Endpoint mapping (thin, no logic)
  Helper           Orchestration + optional abstraction
  Fixture          ✅ Validates + returns clean dict
  Test             Business assertions

------------------------------------------------------------------------

# 🧠 Mental Model

requests.Response (raw) ↓ HttpResponse (parsed + structured) ↓ Fixture
(validated dict) ↓ Test (business assertions)

------------------------------------------------------------------------

# 🟢 Positive Tests (Recommended)

Use fixtures → clean, validated dict

``` python
customer = create_valid_customer()

assert customer["id"]
assert customer["email"]
```

✔ No HTTP noise\
✔ Always valid data\
✔ Safe for juniors

------------------------------------------------------------------------

# 🔵 Advanced Validation (When Needed)

Use helper with HttpResponse

``` python
response = customer_helper.create_customer(return_response=True)

assert response.status_code == 201
assert response.json["id"]
```

Use this when: - debugging failures - checking headers - validating
timing / metadata

------------------------------------------------------------------------

# 🔴 Negative Tests

Use raw API or helper in response mode

``` python
response = customer_helper.create_customer(
    email="invalid",
    return_response=True
)

assert response.status_code == 400
```

✔ Required for error scenarios\
✔ Do NOT use fixtures here

------------------------------------------------------------------------

# ⚠️ Core Rules

## Rule 1 --- Fixtures are STRICT

Fixtures like `create_valid_customer`:

-   ALWAYS return dict
-   ALWAYS return valid data
-   NEVER return HttpResponse
-   NEVER return invalid objects

------------------------------------------------------------------------

## Rule 2 --- Validation Order (MANDATORY)

Always follow:

1.  status_code (transport)
2.  JSON extraction
3.  schema validation
4.  business assertions

------------------------------------------------------------------------

## Rule 3 --- Do NOT mix abstraction levels

❌ WRONG:

``` python
customer = create_valid_customer()
assert customer.status_code == 201
```

✔ CORRECT:

``` python
response = customer_helper.create_customer(return_response=True)
assert response.status_code == 201
```

------------------------------------------------------------------------

## Rule 4 --- Use the right tool

  Scenario                Use
  ----------------------- ----------------------------
  Happy path              Fixture
  Need status / headers   Helper (response mode)
  Negative testing        Raw API / helper(response)

------------------------------------------------------------------------

# 🧪 Fixtures (Factory Pattern)

Fixtures act as **Gatekeepers**:

✔ Call helper\
✔ Validate status\
✔ Extract JSON\
✔ Validate schema\
✔ Register cleanup\
✔ Return clean dict

------------------------------------------------------------------------

# 🧠 Why this works (Enterprise Pattern)

-   Separation of concerns
-   Fail-fast validation
-   Clean test code
-   Reusable setup
-   Prevents flaky tests

------------------------------------------------------------------------

# 🚀 Summary

✔ Fixtures → validated dict\
✔ Helpers → optional HttpResponse\
✔ Tests → business logic\
✔ No hidden validation in transport\
✔ Clear, predictable behavior

------------------------------------------------------------------------

# 👨‍💻 For Juniors

Start with:

``` python
customer = create_valid_customer()
```

Only use advanced mode when needed.

------------------------------------------------------------------------

**End of Document**
