
# 🧪 TEST WRITING GUIDE — TestEcommerceAPI

This document explains **how to write tests correctly in the TestEcommerceAPI framework**.

It is intended for:

- QA engineers
- Developers adding API tests
- New contributors

This guide focuses on **practical rules and patterns** used in the project.

For architecture details see:

- ARCHITECTURE_QUICK_START.md
- README_API_TESTING_STANDARDS.md
- README_API_FRAMEWORK_EXPLAINED.md
- README_VALIDATORS.md

------------------------------------------------------------------
# 🧠 Core Philosophy

Tests should be:

✔ readable  
✔ stable  
✔ focused on business behavior  

Tests should **NOT**:

❌ orchestrate complex workflows  
❌ validate response structure manually  
❌ call low‑level transport code  

The framework already provides helpers and validators to handle this.

------------------------------------------------------------------
# 🧱 Test Layers

A typical test interacts with these layers:

```
Test
 ↓
Fixture
 ↓
Helper
 ↓
API Layer
 ↓
APIClient
 ↓
HttpResponse
 ↓
Validators
 ↓
Pydantic Models
```

Tests should interact mainly with:

- **fixtures**
- **helpers**
- **validators**

------------------------------------------------------------------
# 🧪 Test Structure

Typical test structure:

```
Arrange → Act → Assert
```

Example:

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

------------------------------------------------------------------
# 📦 Fixtures (Factory Pattern)

Fixtures are responsible for **safe test data creation**.

Example fixture:

```
create_valid_customer
```

Responsibilities:

✔ call helper  
✔ validate response  
✔ register cleanup  
✔ return clean dictionary  

Example usage:

```python
customer = create_valid_customer()
```

Returned object:

```
dict
```

Fixtures **never return HttpResponse**.

------------------------------------------------------------------
# 🧠 Helpers

Helpers simplify workflows.

Example:

```
CustomersHelper
```

Responsibilities:

- call API endpoints
- orchestrate workflows
- optionally combine API + DB checks

Example:

```python
response = customer_helper.update_customer(
    customer_id,
    payload=payload,
    return_http_response=True
)
```

Helpers **do not perform assertions**.

------------------------------------------------------------------
# 🔍 Validators

Validators perform **data validation only**.

They may validate:

- response structure
- API correctness
- business rules
- database consistency

Validators **must NOT fetch data**.

Correct pattern:

```
Test / Helper fetches data
        ↓
Validator validates it
```

------------------------------------------------------------------
# 🔧 Positive Tests

Use fixtures whenever possible.

Example:

```python
customer = create_valid_customer()

assert customer["id"]
assert customer["email"]
```

Why:

- fixtures return validated data
- avoids HTTP complexity
- keeps tests readable

------------------------------------------------------------------
# 🔴 Negative Tests

Negative tests usually require **direct helper usage**.

Example:

```python
response = customer_helper.create_customer(
    payload={"email": "invalid"},
    return_http_response=True
)

assert response.status_code == 400
```

Then validate the error payload.

------------------------------------------------------------------
# 🧪 Database Validation

Some tests must verify API ↔ DB consistency.

Example:

```python
customer_helper.assert_customer_exists_and_matches_db(
    email,
    customers_dao
)
```

Use DB validation when:

- updating records
- deleting records
- validating uniqueness
- ensuring data persistence

------------------------------------------------------------------
# 📊 Validation Pipeline

Typical validation flow:

```
Transport validation
      ↓
Structure validation (Pydantic)
      ↓
Business validation
      ↓
Database validation
```

Example:

```python
customer_model = assert_customer_retrieved_successfully(response)

assert_customer_identity(customer_model, expected_id, expected_email)

assert_customer_matches_db(customer_model, db_customer)
```

------------------------------------------------------------------
# ⚠️ Common Mistakes

❌ Mixing abstraction levels

Wrong:

```python
customer = create_valid_customer()
assert customer.status_code == 201
```

Correct:

```python
response = customer_helper.create_customer(return_http_response=True)
assert response.status_code == 201
```

---

❌ Manual structure validation

Wrong:

```
assert "id" in response
assert "email" in response
```

Correct:

```
CustomerModel(**response)
```

------------------------------------------------------------------
# 🧠 Golden Rules

1️⃣ Fixtures return validated dictionaries  
2️⃣ Helpers orchestrate workflows  
3️⃣ Validators validate data only  
4️⃣ Tests assert business behavior  
5️⃣ Transport layers never perform validation  

------------------------------------------------------------------
# 🚀 Final Advice

When writing a test, ask:

- Do I need a fixture?
- Do I need a helper?
- Do I need a validator?

If you follow these patterns, tests will remain:

✔ maintainable  
✔ readable  
✔ stable


------------------------------------------------------------------
# 🧪 Shared Test Suites (Framework-Level Tests)

The framework also contains shared tests that validate infrastructure,
security, and environment behavior before running entity-specific tests.

Directory structure:

tests/shared/

    preflight/
        test_api_connectivity.py
        test_response_format.py
        test_logging_globals.py

    security/
        test_authentication_matrix.py
        test_authentication_success.py

    performance/
        test_basic_response_times.py

Purpose of each category:

Preflight tests
---------------
Verify the test environment and framework configuration before executing
the full test suite.

Examples:
- API connectivity
- logging configuration
- response format validation

Security tests
--------------
Validate authentication and access control behavior.

Example matrix:

4 entities
× 4 HTTP methods
× 3 invalid credential cases
= 48 security tests

Performance tests
-----------------
Provide lightweight baseline response time checks to detect regressions
in API responsiveness.

------------------------------------------------------------------
