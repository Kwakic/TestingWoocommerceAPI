
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

TestEcommerceAPI is a **modular enterprise API testing framework** for validating:

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

The framework follows a **clean layered architecture**.

```
HttpClient        → transport
APIClient         → request orchestration
HttpResponse      → structured response object
API Layer         → endpoint mapping
Helper Layer      → workflow orchestration
Validators        → data validation
Pydantic Models   → structure validation
Tests             → business assertions
```


------------------------------------------------------------------
# 🔄 End‑to‑End Execution Flow

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
.env / CI variables
       ↓
plugins/_config.py
       ↓
framework runtime behavior
```

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

```
HttpClient      → send request
APIClient       → manage request lifecycle
HttpResponse    → safe response
Helper          → orchestrate workflows
Validator       → validate data
Test            → assert behavior
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
|-----|-----|
Send HTTP request | HttpClient |
Manage request | APIClient |
Wrap response | HttpResponse |
Call endpoints | API layer |
Orchestrate workflow | Helper |
Validate data | Validators |
Assert behaviour | Tests |


------------------------------------------------------------------
# 🚀 Final Takeaway

The framework follows **enterprise QA architecture patterns** used by large engineering teams.

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
