# Schema Validation Guide

A short, practical guide for the suite's schema smoke tests and for how schema validation is applied across the entire test suite: what it does, where schemas live, how to add/maintain schemas, and how to run & debug the checks used in preflight and in individual tests.

This guide references the actual test logic used by the suite (see `tests/shared/preflight/test_schema_validation_smoke.py`) and the schema examples under `tests/<service>/schemas/`.

---

## Key point — schema validation runs in every test

Important: schema validation is not limited to the preflight smoke tests. The framework enforces schema validation at multiple levels:

- The shared `RequestUtility` supports a `schema=` argument on request calls (e.g. `api.get(..., schema=my_schema)`) — many helpers and tests use this to validate responses immediately after an API call.
- Helper layers (for example `CustomersHelper`) call schema validators as part of their positive-flow logic:
  - `CustomersHelper.create_customer()` returns the parsed response and helper code or fixtures often call `assert_valid_customer_response()` to assert the created entity conforms to the schema.
- The `create_valid_customer` factory fixture validates responses by default (`validate_response=True`).
- The preflight smoke test (`test_schema_validation_smoke.py`) provides a fast, centralized sample-per-endpoint check, but per-test validation (via RequestUtility and helpers) provides stronger, test-level guarantees.

Consequence: if a response violates the declared schema in any test, that test will fail (not only the preflight job). This makes failures faster-to-diagnose and ensures contract compliance across the suite.

---

## Purpose & scope

- Preflight smoke tests are lightweight, early-warning checks that verify core endpoints return responses matching expected JSON schemas.
- Per-test validation is used broadly to ensure each test asserts the API response structure as part of the test's behavior — not just in preflight.
- Together they help detect schema drift, serialization bugs, and environment misconfiguration quickly.

Markers used by tests:
- `@pytest.mark.preflight` — the preflight job marker.
- `@pytest.mark.schema` — schema-related tests.

Run preflight smoke only:
```bash
pytest -m preflight -q -r s
```

---

## Where schemas live

Follow the existing layout:
- `tests/<service>/schemas/*.py` — module per entity/service.
  - Example: `tests/customers/schemas/customer.py` (exports `customer_schema`)
  - Imported in tests like:
    ```python
    from tests.customers.schemas.customer import customer_schema
    ```

Naming convention
- File: `<entity>.py` inside a `schemas` package.
- Variable: `<entity>_schema` (snake_case), e.g. `customer_schema`, `order_schema`.

---

## How schema validation is applied in tests

There are three common places schema validation occurs:

1. Request-level validation (RequestUtility)
   - Usage example:
     ```python
     products = api.get("products", expected_status_code=200, schema={"type": "array"})
     api.get(f"products/{product_id}", expected_status_code=200, schema=product_schema)
     ```
   - `RequestUtility` will raise a `jsonschema.ValidationError` (or a wrapped `SchemaValidationError`) when validation fails.

2. Helper-layer validation (CustomersHelper/others)
   - Helpers call schema validators for positive flows:
     - `CustomersHelper.validate_customer_response_schema(customer)`
     - `CustomersHelper.assert_valid_customer_response(customer)`
   - Tests that use helper factories (e.g., `create_valid_customer`) get validated responses by default.

3. Preflight smoke tests
   - `tests/shared/preflight/test_schema_validation_smoke.py` samples one item per endpoint and validates both the list and the single-entity response.
   - Useful as a quick guard before the full test matrix runs.

---

## Example places in the codebase (from attached files)

- Per-test factory validating by default:
  - `tests/shared/api_fixtures.py` — `create_valid_customer(..., validate_response=True)` calls the helper and validates the response.

- Helper validation:
  - `tests/customers/helpers/customers_helper.py` (or `EcommerceAPI/tests/...` helper file) — `assert_valid_customer_response()` and `validate_customer_response_schema()` performed in happy-path flows.

- Preflight smoke:
  - `tests/shared/preflight/test_schema_validation_smoke.py` — parametrized smoke test that:
    - `GET /<endpoint>` expecting array schema
    - if non-empty: `GET /<endpoint>/<id>` and validate against `item_schema`

- Test example showing helper usage:
  - `tests/customers/api/test_create_customer_single.py` — uses `create_valid_customer()` which validates and registers entity for cleanup.

---

## Design recommendations for schema checks

- Per-test validation is preferred for correctness: validate responses where they matter (create/update/get) rather than only in preflight.
- Use permissive top-level schemas (`additionalProperties: true`) to avoid breaking on non-critical fields added by the API — tighten nested domain objects (billing/shipping) as needed.
- Use the helper assertion methods for domain-level checks (IDs, email formats, DB consistency). Helpers centralize and standardize validations.

---

## Adding a new schema & wiring it into tests

1. Create schema module:
   - `tests/<service>/schemas/<entity>.py`
   - Provide `<entity>_schema` and optional `<entity>_error_schema`.

2. Use the schema in helpers and tests:
   - In helper `create_*` methods or test call sites:
     ```python
     api.get("entity", schema={"type":"array"})
     api.get(f"entity/{id}", schema=entity_schema)
     helper.assert_valid_entity_response(entity)
     ```

3. (Optional) Add to preflight smoke test parametrize list to get a quick sample-check:
   - Edit `tests/shared/preflight/test_schema_validation_smoke.py` add `("newentity", newentity_schema)` to the param list.

---

## Debugging schema failures

- `ValidationError` indicates which property or type failed; check the failure message and the actual response (Allure/structured logs).
- For per-test failures:
  - The test should include either RequestUtility logs or helper-level logs showing the API response and the failing schema path.
- To reproduce locally:
  - Ensure editable install: `pip install -e './EcommerceAPI[dev]'`
  - Run the test with verbose output and without `-q`:
    ```bash
    pytest tests/customers/api/test_create_customer.py::test_create_single_customer_with_email_and_password_only -q -vv
    ```

---

## Best practices & notes

- Validate responses in the test that exercised the API call: it increases signal-to-noise and reduces debugging time.
- Keep preflight smoke tests fast and light; per-test validation provides deeper coverage.
- Document schema intent when making them more permissive or strict, and reference that rationale in PRs.

---

## Quick commands

- Run tests with per-test validation (default behavior):
  ```bash
  pytest -q
  ```
- Run preflight only:
  ```bash
  pytest -m preflight -q -r s
  ```
- Debug a single failing schema:
  ```bash
  pytest path/to/test_file.py::test_name -q -vv
  ```

---

If you want, I can:
- Add a short template schema file (lenient and strict variants) to speed adding schemas, or
- Produce a small helper that records a sample response to disk to assist schema development.

Which would you like next?