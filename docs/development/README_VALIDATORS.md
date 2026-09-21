# 📘 Validators Architecture Guide

## 🎯 Purpose

This document explains how validation is structured in the EcommerceAPI test framework.

The goal is to keep validation:

- ✅ Clear for newcomers
- ✅ Maintainable for teams
- ✅ Consistent across entities
- ✅ Scalable as the framework grows

The framework uses **Pydantic models for response structure validation** and
entity-specific validator modules for API, business, error, and integration
validation.

---

## 🧠 Core Principle

Validators validate **data that has already been fetched**.

They do **not**:

- call APIs
- query the database
- create or delete test data
- orchestrate workflows
- own the HTTP status assertion for the API operation under test

Data fetching and orchestration belong to the test, helper, API layer, or DAO,
depending on the operation.

### The rule

> **Tests own HTTP status assertions. Validators own response-body/data validation.**

There is one important fixture exception:

> A `create_valid_<entity>` fixture validates the `201 Created` status of the
> POST it performs because that POST is fixture setup, not the operation under
> test.

---

# 🏗️ Current Validation Architecture

The current framework is organized around three practical areas:

```text
Pydantic Models
      ↓
Entity Validators
      ↓
DB Validators
```

These are **validation responsibilities**, not necessarily a mandatory
sequence that every test must execute.

A test may use only structure validation, or it may combine API data,
business rules, and database data depending on what the test is verifying.

---

## 1. 🧱 Pydantic Models — Structure Validation

Pydantic models define the expected structure and types of an API entity.

Example:

```python
CustomerModel
ProductModel
CouponModel
```

### Responsibilities

Pydantic validation checks things such as:

- required fields
- field types
- field formats
- nested structures
- domain-specific model constraints

Example:

```python
customer_model = assert_valid_customer_response(customer)
```

The validator creates the Pydantic model and returns the validated model when
the caller needs typed access to the validated data.

### Important

Pydantic models validate **data**.

They do not:

- call APIs
- access the database
- assert HTTP transport status
- create test resources

---

# 2. 🧪 Entity Validators

Entity validators live with their domain, for example:

```text
EcommerceAPI/src/customers/validators/
    customer_validators.py
    customer_db_validators.py

EcommerceAPI/src/products/validators/
    product_validators.py
    product_db_validators.py

EcommerceAPI/src/coupons/validators/
    coupon_validators.py
    coupon_db_validators.py
```

The exact entity set may grow as the framework grows.

Entity validators contain validation logic that is specific to that domain.

Typical responsibilities include:

- response structure validation
- dataset validation
- error-response validation
- business-rule validation
- API/DB consistency validation when both datasets are supplied

---

## 2.1 Structure Validation

A structure validator normally delegates to the entity's Pydantic model.

Example:

```python
def assert_valid_customer_response(customer: dict) -> CustomerModel:
    return CustomerModel(**customer)
```

The test or fixture is responsible for obtaining the response data.

The validator is responsible for validating that data.

### Example

```python
customer = response.json

customer_model = assert_valid_customer_response(customer)
```

No HTTP request is made by the validator.

---

## 2.2 Dataset Validation

Dataset validators validate collections returned by list/filter endpoints.

Example:

```python
assert_single_customer_by_email(customers, email)
```

A dataset validator may:

1. inspect the supplied dataset
2. find the expected record
3. verify the expected number of matches
4. validate the selected record's structure

It must not fetch the dataset itself.

### Example

```python
customers = customer_helper.list_customers_paginated(email=email)

customer_model = assert_single_customer_by_email(
    customers,
    email,
)
```

### Important

The validator must receive the **complete relevant dataset**.

Do not truncate a dataset in the helper before a validator is expected to
verify uniqueness.

For example, this is dangerous:

```python
return [filtered_customers[0]]
```

because a validator checking:

```python
assert len(matches) == 1
```

can no longer detect duplicate records that were removed by the helper.

---

# 3. 🚨 Error Validators

Error validators validate the structure and content of an error response.

Typical WooCommerce error structure:

```json
{
    "code": "...",
    "message": "...",
    "data": {
        "status": 400
    }
}
```

A generic entity error validator should validate the common contract:

```python
assert_customer_error_response(response)
```

Typical checks include:

- response is a dictionary
- `code` exists and is non-empty
- `message` exists and is non-empty
- `data` exists
- `data.status` exists

---

## 3.1 Scenario-Specific Error Validators

When a scenario has a stable, meaningful domain contract, a more specific
validator may validate it.

For example:

```python
assert_customer_creation_failed(response)
```

may validate the known duplicate-email error returned by the Customers API.

However, do not copy a customer-specific error code/message into another
entity merely because the function names look similar.

For example, Products may have different creation failures:

```text
duplicate SKU
invalid product type
invalid product field
```

A product creation error validator should therefore validate the common
WooCommerce error contract unless a specific scenario has a documented,
stable error contract.

---

# 4. 💼 Business Validation

Business validators validate domain rules that go beyond basic structure.

Example:

```python
assert_customer_identity(customer, expected_email, expected_username)
```

Typical business validation includes:

- expected identity
- field relationships
- domain invariants
- allowed combinations of values
- uniqueness where the supplied dataset allows it to be verified

Business validators receive data and expected values.

They do not fetch either one.

---

# 5. 🔗 API + Database Integration Validation

When a test needs to verify that API data matches the database, the test
orchestrates the two data sources.

### Correct architecture

```text
TEST
 ├── API fetch
 │      ↓
 │   API data
 │
 ├── DAO fetch
 │      ↓
 │   DB data
 │
 └── Validator(API data, DB data)
```

Example:

```python
api_customers = customer_helper.list_customers_paginated(
    email=email
)

db_customer = customers_dao.get_customer_by_email(
    email=email
)

assert_customer_exists_and_matches_api(
    api_customers,
    email,
    db_customer,
)
```

The validator compares the already-fetched API and database data.

### Validators must not do this

```python
# ❌ Wrong
def assert_customer_matches_db(email):
    api_customer = customer_helper.get_customer(email)
    db_customer = customers_dao.get_customer_by_email(email)
    ...
```

That mixes:

- API access
- database access
- orchestration
- validation

and makes the validator difficult to reuse and test.

---

# 6. 🗄️ Database Validators

Database validators contain reusable comparison logic for database-backed
validation.

Example:

```python
assert_customer_matches_db(api_customer, db_customer)
```

They compare supplied API/domain data with supplied database data.

They do not query the database themselves.

### Correct

```python
db_customer = customers_dao.get_customer_by_email(email)

assert_customer_matches_db(
    api_customer,
    db_customer,
)
```

### Incorrect

```python
# ❌ Validator should not fetch the DB record itself
assert_customer_matches_db(email)
```

The DAO owns database access.

The test owns orchestration.

The validator owns comparison.

---

# 7. 🌐 HTTP Status Codes vs Validators

This distinction is important.

## Tests own the HTTP status

The test should assert the status of the API operation it is testing.

### GET

```python
response = customer_helper.get_customer(
    customer_id,
    return_http_response=True,
)

assert response.status_code == 200, (
    f"Expected 200, got {response.status_code}. "
    f"Response: {response.text}"
)

customer_model = assert_valid_customer_response(response.json)
```

### Negative GET

```python
response = customer_helper.get_customer(
    customer_id,
    return_http_response=True,
)

assert response.status_code == 404, (
    f"Expected 404, got {response.status_code}. "
    f"Response: {response.text}"
)

assert_customer_not_found_error(response.json)
```

### Negative POST

```python
http_response = customer_api_raw.post(
    endpoint="customers",
    payload=payload,
)

assert http_response.status_code == 400, (
    f"Expected 400, got {http_response.status_code}. "
    f"Response: {http_response.text}"
)

assert_customer_creation_failed(http_response.json)
```

The validator then validates the **body/data contract**.

---

## 7.1 Why Validators Should Not Own HTTP Status

Avoid this pattern:

```python
# ❌ Avoid
def assert_customer_retrieved_successfully(response):
    assert response.status_code == 200
    ...
```

That couples the validator to the transport layer.

Prefer:

```python
# Test
assert response.status_code == 200

# Validator
assert_valid_customer_response(response.json)
```

This keeps the responsibilities explicit:

```text
HTTP status → Test
Response body → Validator
```

---

# 8. 🧪 Fixtures and Validation

The `create_valid_<entity>` fixture is intentionally different from a normal
validator.

Its purpose is to establish a valid precondition for a test.

Typical flow:

```text
Fixture
   ↓
Helper
   ↓
POST API
   ↓
Assert 201
   ↓
Validate response body
   ↓
Register cleanup
   ↓
Return clean dict
```

Example:

```python
response = product_helper.create_product(
    return_http_response=True,
    **kwargs,
)

assert response.status_code == 201

product = response.json

assert_valid_product_response(product)

register("products", product["id"])

return product
```

### Why the fixture checks 201

The fixture itself performed the POST.

Therefore, it must guarantee:

> "I successfully created a valid resource for the test."

This does not change the general rule that the test owns the status code of the
operation it is actually testing.

---

# 9. 🧩 Helpers and Validators

Helpers and validators have different responsibilities.

## Helpers

Helpers:

- generate or prepare domain data
- call domain API methods
- orchestrate workflows
- provide convenient API operations
- optionally return `HttpResponse` when the caller needs transport details

Helpers do **not** own assertions.

## Validators

Validators:

- validate data
- validate response contracts
- validate domain rules
- compare supplied API and DB data

Validators do **not** fetch data.

### Separation

```text
TEST
 │
 ├── Helper → API operation
 │             ↓
 │          Response/data
 │
 ├── DAO → DB data
 │
 └── Validator → validate supplied data
```

---

# 10. 🧭 Choosing the Right Validation

Use the smallest validator set that proves the behaviour being tested.

### Simple happy-path response

```python
response = customer_helper.get_customer(
    customer_id,
    return_http_response=True,
)

assert response.status_code == 200

customer_model = assert_valid_customer_response(response.json)
```

### Dataset test

```python
customers = customer_helper.list_customers_paginated(
    email=email
)

assert_single_customer_by_email(customers, email)
```

### Business-rule test

```python
customer_model = assert_valid_customer_response(customer)

assert_customer_identity(
    customer_model,
    expected_email=email,
)
```

### API/DB integration test

```python
api_customers = customer_helper.list_customers_paginated(
    email=email
)

db_customer = customers_dao.get_customer_by_email(
    email=email
)

assert_customer_exists_and_matches_api(
    api_customers,
    email,
    db_customer,
)
```

### Negative test

```python
response = customer_helper.update_customer(
    customer_id,
    invalid_payload,
    return_http_response=True,
)

assert response.status_code == 400

assert_customer_error_response(response.json)
```

---

# 11. 🚫 What Validators Must NOT Do

### ❌ Do not call the API

```python
def assert_customer_exists(email):
    customer_helper.get_customer(email)
```

The validator should receive the customer data.

---

### ❌ Do not query the database

```python
def assert_customer_matches_db(email):
    customers_dao.get_customer_by_email(email)
```

The DAO should fetch the record.

---

### ❌ Do not create test data

```python
def assert_valid_product():
    create_valid_product()
```

Fixtures/helpers create test data.

---

### ❌ Do not delete test data

Cleanup belongs to the fixture/resource cleanup mechanism.

---

### ❌ Do not orchestrate workflows

A validator should not decide:

```text
GET API
→ GET DB
→ update API
→ GET API again
```

That belongs in the test or helper.

---

### ❌ Do not own HTTP status assertions

```python
# ❌ Avoid
assert response.status_code == 200
```

inside a normal body/data validator.

The test owns the transport assertion.

---

# 12. 📁 Recommended Entity Structure

For an entity such as Customers:

```text
EcommerceAPI/
└── src/
    └── customers/
        ├── api/
        │   └── customers_api.py
        │
        ├── dao/
        │   └── customers_dao.py
        │
        ├── models/
        │   └── customer_model.py
        │
        └── validators/
            ├── customer_validators.py
            └── customer_db_validators.py
```

The same pattern can be applied to Products, Coupons, Orders, and future
entities.

---

# 13. 🧠 Validation Flow at a Glance

```text
                 TEST
                   │
          ┌────────┴────────┐
          │                 │
       API/Helper          DAO
          │                 │
          ▼                 ▼
       API data           DB data
          │                 │
          └────────┬────────┘
                   ▼
              VALIDATORS
                   │
          ┌────────┼────────┐
          │        │        │
       Pydantic  Business   DB
        model     rules   comparison
```

For transport:

```text
API operation
     ↓
HttpResponse
     ↓
TEST → assert status_code
     ↓
VALIDATOR → validate response.json
```

---

# 14. 🏆 Golden Rules

1. **Validators validate data; they do not fetch it.**
2. **Tests own the HTTP status assertion for the operation under test.**
3. **Pydantic models own response structure and type validation.**
4. **Entity validators own domain-specific validation.**
5. **DAO classes own database access.**
6. **DB validators compare supplied API/domain data with supplied DB data.**
7. **Helpers orchestrate; they do not assert.**
8. **Fixtures establish valid setup and may assert their own setup POST status.**
9. **Negative tests should validate both the expected HTTP status and the
   returned error body.**
10. **Do not create another abstraction layer unless the existing validation
    responsibilities genuinely cannot express the requirement.**
11. **Keep validation close to the entity it belongs to.**
12. **Prefer simple, readable validation over unnecessary abstraction.**

---

# 15. 👥 For New Contributors

If you are unsure where validation belongs, ask these questions:

### "Am I checking HTTP status?"

Put the assertion in the **test**.

### "Am I checking response structure or field types?"

Use the entity's **Pydantic model / structure validator**.

### "Am I checking an entity-specific rule?"

Use an **entity validator**.

### "Am I comparing API data with database data?"

Fetch both in the **test/DAO/helper as appropriate**, then use an
**integration/DB validator**.

### "Am I fetching data?"

You are **not writing a validator**.

Use the appropriate:

- API/helper layer
- DAO
- fixture

---

## 💬 Final Takeaway

The validation architecture is intentionally simple:

```text
Fetch → Test owns transport → Validator owns data
```

With database verification:

```text
API data + DB data → Validator → comparison
```

And with valid fixture setup:

```text
Fixture POST → assert 201 → validate → cleanup → return data
```

The framework does not need separate `*_schema_validator.py`,
`*_assertions.py`, or `base_validators.py` layers merely for the sake of
having more layers.

The current entity-based `*_validators.py` and `*_db_validators.py` structure,
together with Pydantic models, is the validation architecture used by the
framework.
