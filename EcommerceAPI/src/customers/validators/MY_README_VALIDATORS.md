Your validator layer becomes:

    structure validation
          ↓
    API validation
          ↓
    business validation
          ↓
    DB validation



## What senior frameworks do

They create a single validation function that performs the entire verification pipeline.

Example:

`assert_customer_integrity()`

It performs:

    API fetch
    ↓
    API validation
    ↓
    DB fetch
    ↓
    DB validation

------------------------------------------------------------------
In enterprise test frameworks the usual rule is:
    - Validators should NOT fetch data.
    - Validators should only validate.
------------------------------------------------------------------

Tests / helpers responsible for:
    fetching
    orchestration
    workflow

Validators responsible for:
    data validation
    business rules
    consistency checks
------------------------------------------------------------------

The correct architecture is:

    TEST / HELPER
         ↓
    FETCH DATA (API / DAO)
         ↓
    VALIDATORS
         ↓
    SCHEMAS (Pydantic)

------------------------------------------------------------------

Flow:

    TEST
     ↓
    HELPER
     ↓
    API CLIENT
     ↓
    HttpResponse
     ↓
    VALIDATORS
     ↓
    PYDANTIC
     ↓
    DB VALIDATORS

------------------------------------------------------------------
The validator file should contain:

    STRUCTURE
    ---------
    assert_valid_customer_response

    API VALIDATION
    --------------
    assert_valid_customer_in_api
    assert_customer_exists_and_matches_api

    ERROR VALIDATION
    ----------------
    assert_customer_creation_failed
    assert_customer_not_found_error
    assert_customer_retrieved_successfully

------------------------------------------------------------------

POST /customers            → schema validation
GET /customers/{id}        → schema validation
GET /customers?filters     → identity + DB validation

That is exactly what enterprise QA frameworks do.

------------------------------------------------------------------

Tests should NOT orchestrate API + DB + validators manually.
Helpers should provide a single verification entrypoint.

The test should not orchestrate DB + API together.
Helper should e.g. def assert_customer_exists_and_matches_db(self, email: str, dao)
------------------------------------------------------------------
Your framework becomes:

Transport validation
    ↓
HttpResponse

Validator layer
    ↓
assert_customer_retrieved_successfully()

Structure validation
    ↓
CustomerModel (Pydantic)

Business validation
    ↓
assert_customer_identity()

Integration validation
    ↓
assert_customer_exists_and_matches_db()

------------------------------------------------------------------
# 🧠 Final clean architecture (THIS IS YOUR STANDARD)
# RequestUtility  → HttpResponse
# CustomersApi    → HttpResponse
# CustomersHelper → dict OR HttpResponse
# Fixture         → ALWAYS dict (validated)
# Validators      →
# Test            → business validators