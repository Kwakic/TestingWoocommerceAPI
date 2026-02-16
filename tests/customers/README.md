# 📘 Customers Microservice Test Suite

*(Matrix-aligned, framework-compatible, and future-proof)*

This directory contains all automated API tests, data models, schemas, fixtures, and plugins dedicated to the Customers microservice.  
It follows the unified test framework architecture, enables CI autodiscovery, and is structured for maximum coverage and future extensibility.

---

## ✅ Status: **Complete, Future-Proof, and CI-Ready**

- Covers full CRUD, edge cases, search, pagination, schema validation, and DAO assertions for the `/customers` entity.
- Defensive: negative and edge testing included.
- Maintainable: clear structure, data-driven, extensible for new features.
- **CI autodiscovery:** Easily integrates with matrix-style pipelines.
- **Future-proof testing:** Utilities and test skeletons prepared for rate limiting, auth changes, and user/role-based access.

---

## 1. 📁 Directory Structure

```
├── tests/                                         ← The test suite root - Each team got its own file
│     ├── customers/                               ← customers-specific
│     │     ├── configs/
│     │     │     └── config_customers.py          ← storing API_HOSTS
│     │     ├── data/
│     │     │     └── create_customer_payload.json
│     │     ├── .gitlab-ci-template.yml
│     │     ├── __init__.py
│     │     ├── conftest.py
│     │     ├── README.md
│     │     └── api/
│     │           └── test_debug.log
│     │           └── test_suite_summary.MD
│     │           └── test_create_customer.py
│     │           └── test_customer_deletion.py
│     │           └── test_customer_filters.py
│     │           └── test_customers_auth.py
│     │           └── test_get_all_customers_smoke.py
│     │           └── test_get_customer.py
│     │           └── test_soft_deleted_customer_handling.py
│     │           └── test_update_custom
│     │           └── __init__.py
│     ├── shared/
│     │     ├── schemas/
│     │     │       ├── coupon.py
│     │     │       ├── customers.py
│     │     │       ├── order.py.py
│     │     │       └── product.py.py
│     │     ├── contract/
│     │     │       ├── test_schema_validation_smoke.py
│     │     │       ├── __init__.py
│     │     │       └── README_CONTRACT.md
│     │     ├── performance/
│     │     │       ├── test_basic_response_times.py
│     │     │       └── __init__.py
│     │     └── preflight/
│     │             ├── test_logging_globals.py
│     │             ├── test_config_contract.py
│     │             ├── test_pytest_bootstrap.py
│     │             ├── __init__.py
│     │             └── README_PREFLIGHT.md
│     │
│     ├── orders/..                                ← orders-specific
│     ├── coupons/..                               ← coupons-specific
│     └── products/..                              ← products-specific
│
└── conftest.py           # registers Customers-specific plugins
```

This folder is fully isolated, supporting clean per-domain plugins, independent reporting, and targeted CI runs.

---

## 2. 🧪 Test Coverage Summary & Checklist

### ✔️ CRUD Operations
- [x] Create (single, bulk, with/without metadata)
- [x] Read (by ID, list, filters, search)
- [x] Update (partial, full, ignores immutable fields)
- [x] Delete (via API & DB/DAO layer)

### ✔️ Negative/Edge Testing
- [x] Missing required fields
- [x] Invalid input formats (email, timestamps)
- [x] Update deleted entities
- [x] Duplicate emails/entities
- [x] Invalid/extra fields ignored
- [x] Invalid search terms
- [x] Invalid update keys

### ✔️ Timestamps & Filters
- [x] ISO 8601 parsing
- [x] `after` / `before` filtering
- [x] Field & timestamp consistency

### ✔️ Search / Pagination / Sorting
- [x] Search by `email`, `first_name`, `last_name` (exact/partial, case-insensitive)
- [x] Pagination (`per_page`, `page`)
- [x] Sorting (asc, desc)

### ✔️ Schema Validation & DB Assertions
- [x] Schema: POST, GET, PUT response shape/type/required fields
- [x] Ensures no system-managed fields mutated
- [x] API response = DB/DAO state

### ✔️ Metadata
- [x] Create with meta-fields
- [x] Retrieve metadata
- [x] Absence validated when meta absent

### ✔️ Future-Proof (Prepared/skipped)
- [x] Rate limiting (429): utility exists, tests ready but skipped unless enabled
- [x] Auth/token (valid/invalid/expired): utility exists
- [ ] User/role-based isolation: test skeleton, not yet supported

---

## 3. 🔌 Plugins & Fixtures

- **Location:** `tests/customers/plugins/`
    - `api_fixtures.py`: Factories, clients, request helpers
    - `entities.py`: Domain objects & builders
    - `_config.py`: Plugin config, lifecycle hooks
- Register in `conftest.py`:
    ```python
    pytest_plugins = [
        "tests.customers.plugins.api_fixtures",
        "tests.customers.plugins.entities",
        "tests.customers.plugins._config",
    ]
    ```

---

## 4. 📦 Payloads & Scenario Data

| Path                               | Use case                   |
|-------------------------------------|----------------------------|
| `data/create_customer_payload.json` | common create ops/flows    |
| `data/customers_scenarios.json`     | E2E and error permutations |
| `data/customer_update_payload.json` | update flows               |

Reusable for E2E, regression, and data-driven scenario tests.

---

## 5. 📐 Schemas

Validate every response using Pydantic/models in `schemas/`:

- `customers_general.py`, `customers_filters.py`, `customers_patch.py`, etc.
- Validators include: field/type checks, required logic, pagination, metadata format

---

## 6. 🧪 Typical Test Categories

- Create customer
- Update customer
- Get customer(s)
- List/pagination/sorting
- Filtering & search
- Timestamp logic & validation
- Metadata creation/retrieval
- Authentication & authorization
- Soft delete / recovery
- Negative and error scenarios
- Schema validation (with `FAIL_ON_EMPTY_LIST` support)
- DAO/DB assertions

---

## 7. ➕ Adding New Tests/Features (Team Workflow)

- Add/update schema in `schemas/` if needed
- Add new/edited payloads in `data/`
- Add helpers into `helpers/` (optional)
- Update/add fixtures in `plugins/`
- New/updated tests go in `api/`
- Run full suite locally:  
  `pytest tests/customers -vv`
- Update `CHANGELOG.md` (required for CI+docs)

---

## 8. ▶️ Running Customers Tests

**Quick Run:**  
```bash
pytest tests/customers -q
```

**Verbose:**  
```bash
pytest tests/customers -vv
```

**HTML Report + Structured Logs:**  
```bash
pytest tests/customers --auto-html-report --log-cli-level=INFO
```

**Override environment in CI-style:**  
```bash
ENABLE_STRUCTURED_LOGS=true LOG_PAYLOADS=false pytest tests/customers --auto-html-report
```

---

## 9. 🧱 CI Integration (Matrix-Ready)

- Folder is auto-detected via matrix/glob in CI pipelines.
- Example rule (GitLab):
    ```yaml
    rules:
      - exists:
          - tests/customers/
    ```
- Example matrix expansion:
    ```yaml
    matrix:
      - SERVICE: "customers"
      - SERVICE: "orders"
      - SERVICE: "billing"
    ```
- CI passes: environment, logging, report dirs, flags; all test suites run in parallel, report independently.

---

## 10. 👥 Ownership

| Role              | Person           | Notes                     |
|-------------------|------------------|---------------------------|
| QA Owner          | Your Name        | Primary maintainer        |
| Developer Owner   | TBD              | Customers backend lead    |
| Test Framework    | Automation Guild | Maintains shared utilities|

---

## 11. 🧰 Utilities Included

- `utils/rate_limit.py`: endpoint hammering, test throttling
- `utils/auth_tokens.py`: various token state simulations
- `get_auth_header()`: universal request auth header

---

## 12. ℹ️ Notes

✔ Matrix-compliant, future-proof  
✔ Defensive & thorough coverage  
✔ CI-ready, HTML/log artifact support  
✔ Standardized with all microservices  
✔ Actively maintained, test utilities provided  
✔ Rate limiting/auth isolation: test-ready for future endpoint features