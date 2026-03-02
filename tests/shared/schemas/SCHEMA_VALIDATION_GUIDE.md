# Schema Validation Guide

A short, practical guide for the suite's schema smoke tests and for how schema validation is applied across the entire test suite: what it does, where schemas live, how to add and maintain schemas, and how to run and debug the checks used in **contract tests** and in **individual tests**.

This guide reflects the current architecture where **schema validation is a shared contract concern**, not a preflight responsibility.

---

## Key principle — schema validation runs everywhere

Schema validation is **not limited to contract or smoke tests**. The framework enforces schema validation at multiple layers:

- **APIClient**
  - Supports a `schema=` argument on request calls:
    ```python
    api.get("products", expected_status_code=200, schema=product_schema)
    ```
  - Raises `jsonschema.ValidationError` (wrapped when appropriate).

- **Helper / DAO layers**
  - Helpers validate positive flows:
    - `assert_valid_customer_response(customer)`
    - `validate_order_schema(order)`
  - Factory fixtures validate responses by default.

- **Shared contract tests**
  - `tests/shared/contract/test_schema_validation_smoke.py`
  - Provide a fast, centralized sample-per-endpoint verification.

**Result:** any schema violation fails the test that exercised the API — not just a single smoke job.

---

## Purpose & scope

Schema validation ensures:
- API responses conform to documented contracts
- Serialization bugs are caught early
- Backward-incompatible changes surface immediately
- Tests fail close to the source of the problem

This applies equally to:
- Feature tests
- Regression tests
- Shared contract validation

---

## Test markers

| Marker | Meaning |
|------|--------|
| `@pytest.mark.schema` | Any test performing schema validation |
| `@pytest.mark.contract` | Shared, cross-entity contract checks |

Run contract-only schema checks:
```bash
pytest tests/shared/contract -q -r s
```

---

## Where schemas live (authoritative layout)

Schemas are domain-owned, not centralized artificially.

```
tests/
├── customers/
│   └── schemas/
│       ├── customer.py
│       └── error_schema.py
├── orders/
│   └── schemas/
├── products/
│   └── schemas/
└── coupons/
    └── schemas/
```

### Why this layout

- **Schemas evolve with their domain** — changes stay near the code that uses them
- **Helpers, tests, and fixtures stay colocated** — easier navigation and maintenance
- **Avoids a monolithic schemas/ dumping ground** — cleaner organization

Shared contract tests import schemas, they do not own them.

**Example:**
```python
from tests.customers.schemas.customer import customer_schema
```

---

## Naming conventions

- **File:** `<entity>.py`
- **Exported variable:** `<entity>_schema`
- **Error schemas:** `<entity>_error_schema`

**Example:**
```
customer_schema
customer_error_schema
```

---

## How schema validation is applied

### 1. Request-level validation

```python
api.get("customers", schema={"type": "array"})
api.get(f"customers/{cid}", schema=customer_schema)
```

### 2. Helper-layer validation

Helpers enforce schema correctness for happy paths:

```python
CustomersHelper.assert_valid_customer_response(customer)
```

### 3. Shared contract tests

Contract tests sample one entity per endpoint:

- Validate list response shape
- Validate single-entity schema

They do not replace per-test validation.

---

## Contract tests vs preflight tests

| Category | Purpose | Network dependency |
|----------|---------|-------------------|
| Preflight | Framework & config sanity | None |
| Contract | API schema correctness | Yes |
| Feature tests | Business logic | Yes |

Schema validation belongs to contract tests, not preflight.

---

## Adding a new schema

1. **Create schema module:**
   ```python
   # tests/<service>/schemas/<entity>.py
   ```

2. **Export `<entity>_schema`**

3. **Use it in:**
   - Helpers
   - Feature tests
   - Contract tests (optional but recommended)

4. **Add to contract smoke test parametrization if applicable**

---

## Debugging schema failures

1. **Look for ValidationError messages**
2. **Check structured logs / Allure attachments**
3. **Re-run failing test locally:**
   ```bash
   pytest path/to/test.py::test_name -vv
   ```

**Common causes:**
- Missing required fields
- Type mismatch
- Unexpected nulls
- Breaking API changes

---

## Best practices

✅ Validate where the API call happens

✅ Keep schemas permissive at the top level

✅ Be strict on nested domain objects

✅ Avoid duplicating schemas across services

✅ Document intentional schema looseness in PRs

---

## Quick commands

**Run everything:**
```bash
pytest -q
```

**Run contract schema validation only:**
```bash
pytest tests/shared/contract -q -r s
```

**Debug one test:**
```bash
pytest path/to/test.py::test_name -vv
```

---

## Summary

Schema validation is a first-class contract enforcement mechanism in this framework.

✔️ Domain-owned schemas

✔️ Validation at request, helper, and contract levels

✔️ Fast feedback, precise failures

✔️ CI-safe and locally reproducible

**If schema breaks, tests break — by design.

