
# 🚀 ARCHITECTURE QUICK START — TestEcommerceAPI

This document gives a **fast 3‑minute overview** of how the TestEcommerceAPI framework works.

It is designed for:
- New QA engineers
- Developers integrating new API tests
- Contributors trying to understand the framework quickly

For deeper explanations see:

- README_API_FRAMEWORK_EXPLAINED.md
- README_ARCHITECTURE.md
- README_VALIDATORS.md
- README_API_TESTING_STANDARDS.md
- FRAMEWORK_OVERVIEW.md


------------------------------------------------------------------
# 🧠 What This Framework Is

TestEcommerceAPI is a **modular API testing framework** for validating:

- Customers API
- Orders API
- Coupons API
- Products API

It provides:

✔ shared test utilities
✔ reusable helpers
✔ consistent validation patterns
✔ structured logging
✔ Allure reporting
✔ CI matrix execution


------------------------------------------------------------------
# 🧱 Core Framework Layers

The framework uses a shared HTTP transport layer with
protocol-specific API clients.

REST and GraphQL share the same low-level HTTP transport,
but each protocol has its own request orchestration and
response model.

```text
                         ┌── REST ──────→ APIClient ──────→ HttpResponse
                         │
HttpClient ──────────────┤
                         │
                         └── GraphQL ───→ GraphQLClient ──→ GraphQLResponse
```

Above these protocol layers, tests remain organized by
business entity.

```
REST / GraphQL clients
          ↓
   Entity-specific tests
          ↓
     Business assertions
```

The REST and GraphQL clients therefore share infrastructure
without forcing both protocols into the same client or
response abstraction.

So the final architecture story becomes:
```
                    TestEcommerceAPI
                          │
              ┌───────────┴───────────┐
              │                       │
            REST                   GraphQL
              │                       │
          APIClient              GraphQLClient
              │                       │
        HttpResponse          GraphQLResponse
              │                       │
              └───────────┬───────────┘
                          │
                     HttpClient
                          │
                   requests.Session
                          │
                       Server
```


------------------------------------------------------------------
# 🔄 REST End-to-End Execution Flow

The following flow describes the REST API execution path.
GraphQL uses the same low-level `HttpClient` transport but
has its own `GraphQLClient` and `GraphQLResponse` layers.

Typical positive test execution:

```
pytest
 │
 ▼
Test
 │
 ▼
Fixture (factory pattern)
 │
 ▼
Helper
 │
 ▼
API Layer
 │
 ▼
APIClient
 │
 ▼
HttpClient
 │
 ▼
requests.Session
 │
 ▼
🌐 Server
 │
 ▼
requests.Response
 │
 ▼
HttpResponse
 │
 ▼
Validators
 │
 ▼
Pydantic Model
 │
 ▼
Business Assertions
```


------------------------------------------------------------------
# 📦 Key Framework Components

## HttpClient
Lowest layer.

Responsibilities:

- Send HTTP request
- Return raw `requests.Response`

Does NOT:

- parse JSON
- validate responses
- retry requests


------------------------------------------------------------------
## APIClient

Orchestrates the full request lifecycle.

Responsibilities:

- build URL
- apply retry/backoff
- structured logging
- convert raw response → HttpResponse


------------------------------------------------------------------
## HttpResponse

Safe wrapper around `requests.Response`.

Provides:

- `.status_code`
- `.json`
- `.text`
- safe JSON parsing
- normalized interface


------------------------------------------------------------------
## API Layer

Example:

```
CustomersApi
OrdersApi
ProductsApi
```

Responsibilities:

- map endpoints
- call APIClient

Does NOT:

- validate business logic
- perform assertions


------------------------------------------------------------------
## Helper Layer

Example:

```
CustomersHelper
OrdersHelper
```

Responsibilities:

- orchestrate API calls
- simplify common workflows
- prepare data for tests

Helpers may:

- fetch API data
- fetch DB data
- call validators


------------------------------------------------------------------
# 🧪 Validation Architecture

Validation is performed in **multiple layers**.

```
Structure validation
      ↓
API validation
      ↓
Business validation
      ↓
Database validation
```


------------------------------------------------------------------
# 🔍 Structure Validation

Structure validation uses **Pydantic models**.

Example:

```
customer_model = CustomerModel(**response.json)
```

Benefits:

- strong typing
- validation errors
- IDE support
- easier debugging


------------------------------------------------------------------
# 🧠 Validator Responsibilities

Validators **ONLY validate data**.

They must NOT:

❌ fetch API data
❌ query database
❌ orchestrate workflows

Correct architecture:

```
TEST / HELPER
     ↓
FETCH DATA (API / DAO)
     ↓
VALIDATORS
     ↓
PYDANTIC MODELS
```


------------------------------------------------------------------
# 🧪 Test Pattern (Recommended)

Example positive test flow:

```
customer = create_valid_customer()

response = customer_helper.get_customer_by_id(
    customer["id"],
    return_http_response=True
)

customer_model = assert_customer_retrieved_successfully(response)

assert_customer_identity(customer_model, customer["id"], customer["email"])

customer_helper.assert_customer_exists_and_matches_db(
    customer["email"],
    customers_dao
)
```


------------------------------------------------------------------
# 🧱 Fixture Responsibilities

Fixtures act as **gatekeepers**.

They:

✔ call helpers
✔ validate status codes
✔ validate response structure
✔ register cleanup
✔ return safe data to tests


------------------------------------------------------------------
# 🔧 Plugin Architecture

The framework uses **pytest plugins** located in:

```
EcommerceAPI/plugins/

api/
    shared_api.py
    shared_graphql.py
    customers.py
    orders.py
    products.py
    coupons.py

config_pytest.py
logging_plugin.py
entities.py
entity_metadata.py
reporting.py
allure_autogen.py
db_fixtures.py
```

Examples:

- logging_plugin.py
- reporting.py
- allure_autogen.py
- api_fixtures.py
- db_fixtures.py


Plugins handle:

- logging
- reporting
- entity discovery
- configuration
- fixture registration


------------------------------------------------------------------
# 📊 Reporting & Observability

Framework produces:

### Allure reports

Test results are written as:

```
reports/<service>/allure-results
```

CI converts them into HTML reports.

### Structured Logs

JSONL logs stored in:

```
reports/logs/
```

These logs are useful for:

- debugging CI failures
- log ingestion pipelines
- analytics


------------------------------------------------------------------
# 🧠 Configuration Model

Configuration follows a **single source of truth**.

```
    API_ENV
      │
      ▼
config_<entity>.py
      │
      ▼
   API_HOSTS
      │
      ▼
   APIClient
```

>Authentication credentials (WC_KEY / WC_SECRET) are generated independently during the bootstrap process and are intentionally kept separate from endpoint selection.

Rules:

- env vars parsed once
- values frozen at startup
- plugins consume resolved constants


------------------------------------------------------------------
# 🧪 CI Architecture

CI runs tests in **matrix mode**.

Each microservice runs independently:

```
customers
orders
products
coupons
```

Benefits:

✔ parallel execution
✔ faster feedback
✔ failure isolation


------------------------------------------------------------------
# 🧠 Mental Model

```text
HttpClient       → send HTTP request
APIClient        → manage REST request lifecycle
GraphQLClient    → manage GraphQL request lifecycle
HttpResponse     → represent REST response
GraphQLResponse  → represent GraphQL response
Helper           → orchestrate REST workflows
Validator        → validate data
Test             → assert behaviour
```


------------------------------------------------------------------
# 📌 Golden Rules

1️⃣ Tests own validation logic
2️⃣ Validators only validate data
3️⃣ Helpers orchestrate workflows
4️⃣ Transport layers never perform validation
5️⃣ Structure validation happens via Pydantic models


------------------------------------------------------------------
# 👥 For New Contributors

If you are unsure where code belongs:

| Task | Location |
|------|----------|
| Send HTTP request | HttpClient |
| Manage REST request | APIClient |
| Manage GraphQL request | GraphQLClient |
| Wrap REST response | HttpResponse |
| Wrap GraphQL response | GraphQLResponse |
| Call REST endpoints | API layer |
| Orchestrate REST workflow | Helper |
| Validate data | Validators |
| Assert behaviour | Tests |


------------------------------------------------------------------
# 🚀 Final Takeaway

The framework follows **QA architecture patterns** used by large engineering teams.

Key goals:

✔ clear separation of concerns
✔ maintainable validation logic
✔ readable tests
✔ reliable CI execution


------------------------------------------------------------------
# 📚 Recommended Reading

For deeper understanding:

- README_ARCHITECTURE.md
- README_API_FRAMEWORK_EXPLAINED.md
- README_API_TESTING_STANDARDS.md
- README_VALIDATORS.md
- QA_DEVELOPER_ONBOARDING.md


------------------------------------------------------------------
# 🧪 Shared Test Suites (Framework-Level Tests)

The framework also contains shared tests that validate infrastructure,
security, and environment behavior before running entity-specific tests.

Directory structure:


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

Purpose of each category:

Preflight tests
---------------
Verify the test environment and framework configuration before executing
the full test suite.

Examples:
- API connectivity
- logging configuration
- response format validation

---

Security tests
--------------
Validate authentication and access control behavior.

Example matrix:

4 entities
× 4 HTTP methods
× 3 invalid credential cases
= 48 security tests

---

Contract tests
------------------
Contract tests validate the expected API response structure.

REST contract tests validate REST response contracts.

GraphQL contract tests validate GraphQL schema-level expectations,
such as the availability of required GraphQL types and mutation
fields.

GraphQL contract tests do not replace entity-specific GraphQL tests.
They validate the GraphQL API contract at framework level, while
tests under `tests/<entity>/graphql/` validate business behaviour.

------------------------------------------------------------------
