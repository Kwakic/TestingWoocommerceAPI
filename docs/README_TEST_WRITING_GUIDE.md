# 🧪 TEST WRITING GUIDE --- TestEcommerceAPI (ENTERPRISE VERSION)

This document explains **how to write tests correctly in the
TestEcommerceAPI framework**.

It is intended for:

-   QA engineers\
-   Developers adding API tests\
-   New contributors

This guide combines: ✔ original framework philosophy\
✔ real test examples\
✔ enterprise QA best practices\
✔ CI execution strategy

------------------------------------------------------------------------

# 🧠 Core Philosophy

Tests should be:

✔ readable\
✔ stable\
✔ focused on business behavior

Tests should **NOT**:

❌ orchestrate complex workflows\
❌ validate response structure manually\
❌ call low‑level transport code

The framework already provides helpers and validators to handle this.

------------------------------------------------------------------------

# 🧱 Architecture Overview

    HttpClient → APIClient → HttpResponse → API → Helpers → Validators → Tests

### Responsibilities

  Layer          Responsibility
  -------------- -------------------------------
  HttpClient     transport + timeout
  APIClient      retry, logging, orchestration
  HttpResponse   normalization
  API            endpoint definition
  Helpers        workflows
  Validators     assertions
  Tests          business validation

------------------------------------------------------------------------

# 📁 Test Structure (MANDATORY)

    tests/
       customers/
       orders/
       products/
       coupons/
       shared/

✔ Domain-driven (matches microservices)\
✔ Enables team ownership\
✔ Scales easily

❌ DO NOT reorganize by smoke/regression folders

------------------------------------------------------------------------

# 🏷️ Marker Strategy (STANDARDIZED)

## 1. Domain (auto-applied via conftest)

    customers, orders, products, coupons, shared

------------------------------------------------------------------------

## 2. Execution Tier

  Marker       Meaning
  ------------ -------------------------
  smoke        critical API health
  sanity       quick functional checks
  regression   full coverage

------------------------------------------------------------------------

## 3. Test Type

  Marker        Meaning
  ------------- ---------------------
  integration   API + DB validation
  contract      schema validation
  negative      invalid input tests
  e2e           multi-step workflow

------------------------------------------------------------------------

## 4. Specialized

    performance
    security
    preflight
    bulk

------------------------------------------------------------------------

# 🚨 Marker Rules

✔ Max 2--3 markers per test (excluding domain)\
✔ Domain markers should NOT be manually added\
✔ Use consistent naming (negative NOT negative_test)

### Example

``` python
pytestmark = [
    pytest.mark.integration,
    pytest.mark.regression
]
```
### Big Picture

✅ Domain → customers, orders, etc.

✅ Execution → smoke, sanity, regression

✅ Type → integration, contract, negative, e2e

✅ Special → performance, security, preflight, bulk

------------------------------------------------------------------------

# 🤖 CI Strategy (STANDARD)

## Fast pipeline (PR / commit)

    pytest -m "smoke or sanity or preflight"

------------------------------------------------------------------------

## Full validation

    pytest -m "not performance and not security"

------------------------------------------------------------------------

## Nightly

    pytest -m regression

------------------------------------------------------------------------

## Scheduled

    pytest -m performance
    pytest -m security

------------------------------------------------------------------------

# 🧪 Test Structure

    Arrange → Act → Assert

### Example

``` python
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

------------------------------------------------------------------------

# 📦 Fixtures (Factory Pattern)

Fixtures must:

✔ create resource\
✔ validate response\
✔ register cleanup\
✔ return dictionary

Example:

``` python
customer = create_valid_customer()
```

❌ Fixtures must NOT return HttpResponse

------------------------------------------------------------------------

# 🔴 Negative Tests

Use helper or raw API:

``` python
response = customer_helper.create_customer(
    payload={"email": "invalid"},
    return_http_response=True
)

assert response.status_code == 400
```

✔ validate error schema\
✔ validate business rules

------------------------------------------------------------------------

# 🧠 Helpers

Responsibilities:

-   call APIs\
-   orchestrate workflows\
-   combine API + DB logic

❌ DO NOT assert inside helpers

------------------------------------------------------------------------

# 🔍 Validators

Responsibilities:

-   validate structure\
-   validate business logic\
-   validate DB consistency

❌ DO NOT fetch data

Pattern:

    fetch → validate

------------------------------------------------------------------------

# 🧪 Integration Tests

If test uses DAO:

    API → DB validation

Then it is:

    pytest.mark.integration

------------------------------------------------------------------------

# 📊 Validation Pipeline

    Transport validation
          ↓
    Schema validation
          ↓
    Business validation
          ↓
    Database validation

------------------------------------------------------------------------

# ⚠️ Common Mistakes

❌ Mixing abstraction layers

❌ Manual JSON validation

❌ Overusing helpers for negative tests

------------------------------------------------------------------------

# 🧼 Cleanup Strategy

✔ automatic via fixtures\
✔ avoid leftover data

------------------------------------------------------------------------

# 📊 Observability

Already included:

✔ structured logging\
✔ request duration\
✔ error logging

❌ No need for metrics system

------------------------------------------------------------------------

# 🔁 Retry & Timeout

✔ HttpClient → timeout\
✔ APIClient → retry/backoff

------------------------------------------------------------------------

# 🧪 Shared Test Suites

    tests/shared/
       preflight/
       security/
       performance/
       contracts/

### Preflight

-   API connectivity\
-   response format

### Security

-   authentication matrix

### Performance

-   response time checks

------------------------------------------------------------------------

# 🚫 What NOT to do

❌ No ResponseAdapter\
❌ No metrics layer\
❌ No extra abstraction\
❌ No folder restructuring\
❌ No over-tagging

------------------------------------------------------------------------

# 🧠 Golden Rules

1.  Fixtures return validated data\
2.  Helpers orchestrate\
3.  Validators validate\
4.  Tests verify business logic\
5.  Keep tests simple

------------------------------------------------------------------------

# 🚀 Final Advice

Ask:

"Does this help me write better tests faster?"

If not → skip it.

------------------------------------------------------------------------

# 🏁 Conclusion

This framework is:

✔ enterprise-ready\
✔ scalable\
✔ cleanly designed

👉 Focus now on writing tests, not refactoring framework.
