# API Testing Standards — TestEcommerceAPI ✅

A concise, practical standard for writing API tests in this repo.  
Covers test purpose, structure, naming, fixtures, validation, failure handling, cleanup, and CI expectations. Use this for new tests, PR reviews, and cross-team guidance.

Related docs
- Developer setup & onboarding: [DEVELOPER_ONBOARDING.md](./DEVELOPER_ONBOARDING.md)  
- Schema guidance: [SCHEMA_VALIDATION_GUIDE.md](../tests/shared/schemas/SCHEMA_VALIDATION_GUIDE.md)  
- Environment & CI: [README_ENV_AND_CI.md](README_ENV_AND_CI.md)  
- High-level overview: [FRAMEWORK_OVERVIEW.md](./FRAMEWORK_OVERVIEW.md)  
- Changelog policy: [CHANGELOG_GUIDELINES.md](./CHANGELOG_GUIDELINES.md)

---

## Purpose
- Ensure API behavior matches contract (schema + domain rules).
- Keep tests reliable, fast, and maintainable.
- Provide clear signals for regressions in CI (preflight + per-service matrix).

---

## Principles (short)
- Validate schema in every test where responses matter — not only in preflight. Use `schema=` on `RequestUtility` or helper validation methods.
- Keep tests deterministic and idempotent: tests should clean up created data.
- Prefer small, focused tests that assert one behavior.
- Use fixtures & helpers — avoid duplicating API logic in tests.
- Fail fast and include actionable logs and Allure attachments.

---

## Test organization & markers
- Path: `tests/<service>/api/test_<feature>.py`
- Naming:
  - Files: `test_*.py`
  - Functions: `test_*`
  - Classes: `Test*`
- Markers (use as appropriate): `@pytest.mark.preflight`, `@pytest.mark.schema`, `@pytest.mark.api`, `@pytest.mark.smoke`, `@pytest.mark.regression`, `@pytest.mark.integration`, `@pytest.mark.performance`.
- Add a short docstring at top of test file explaining scope.

Example file header:
```python
pytestmark = [pytest.mark.customers, pytest.mark.api]
```

---

## Use fixtures & helpers (do this)
- Use `request_utility` (session-scoped) for raw API ops and schema support.
- Use helper classes (e.g., `CustomersHelper`) to perform common flows.
- Use factory fixtures (e.g., `create_valid_customer`) for happy-path creation — they validate by default and register cleanup.
- For negative tests that expect error responses, use the `raw_*` fixtures (e.g., `raw_customer_api`) or call helper with `expected_status_code` and inspect returned error JSON.

Do NOT:
- Instantiate helpers or DAOs directly in tests if a fixture provides them.
- Query DB directly without using DAO fixtures in tests (use `customers_dao` etc. provided by fixtures).

---

## Schema validation (required)
- Validate responses with JSON Schema for all positive flows:
  - Either pass `schema=` to `RequestUtility.get/post/...` which will raise `SchemaValidationError` on mismatch
  - Or call helper validation functions, e.g. `CustomersHelper.assert_valid_customer_response()`
- Keep top-level schemas permissive (see SCHEMA guide) and stricter for critical nested objects.
- Add or update schema files under: `tests/<service>/schemas/` and export `<entity>_schema`.

---

## Positive vs Negative tests
- Positive tests: use helpers/factories; assert schema + domain fields + DB consistency where applicable.
- Negative tests: use `raw_*` fixtures or `return_raw=True` to inspect raw `requests.Response`; assert expected status, error schema (`error_schema`) and messages.

Example negative test pattern:
```python
resp = raw_customer_api.post("customers", payload=bad_payload, expected_status_code=400, return_raw=True)
assert resp.status_code == 400
assert validate_error_schema(resp.json())
```

---

## Assertions & readability
- Prefer clear, specific assertions (avoid many chained assertions in a single line).
- Name important values for clarity (e.g., `customer_id = resp["id"]`).
- Avoid asserting on non-deterministic fields (timestamps) unless normalized.

---

## Timeouts, retries & flakiness
- Tests use `RequestUtility` which has retry/backoff — do not reimplement retries in tests.
- Keep external waits minimal. If testing eventual consistency, use short poll loops with timeboxed retries.
- If a test is flaky, fix the root cause (test or system). Do not silence flakes with sleeps. Mark flaky only as last resort and document mitigation.

---

## Test data & cleanup (must)
- Register created resources with the shared cleanup registry (factories do this by default).
- Default behavior: tests should clean up created data. Use `skip_cleanup=True` only when intentionally keeping data (document in test).
- Use deterministic test data when possible (unique email generators are ok).
- For DB verification, use DAO fixtures (e.g., `customers_dao`) and assert mapping between API and DB.

---

## Logging, diagnostics & Allure
- Tests and helpers log structured info via `custom_logger`. Include meaningful messages; avoid leaking secrets.
- Attach important artifacts to Allure (response bodies, request payloads, last structured log) when helpful.
- Use `--alluredir` in CI to collect results. CI should install Allure CLI to produce HTML if `AUTO_ALLURE_REPORT=true`.

---

## CI-specific expectations
- Preflight: fast smoke checks (`@pytest.mark.preflight`) run before the full matrix.
- Matrix jobs: one microservice per job; each job writes results to `reports/<service>/allure-results`.
- CI should run tests with editable install: ` - pip install -e './EcommerceAPI[dev]'` to ensure extras are available.
- CI should set `REQUIRE_ENV=true` (fail fast for missing env) and `FAIL_ON_EMPTY_LIST=true` for strict preflight.

---

## Security & secrets
- Never hard-code secrets in tests.
- Use `.env` for local convenience (copy from `.env.example`) — do not commit `.env`.
- Use CI secret stores for sensitive values (WC keys, DB credentials).
- Keep `REDACT_SENSITIVE_FIELDS=true` and `LOG_PAYLOADS=false` in CI.

---

## PR checklist for tests
- [ ] Test name and file follow conventions.
- [ ] Use fixtures/helpers (no raw logic duplication).
- [ ] Response schema validated (either via `schema=` or helper).
- [ ] Created resources are registered for cleanup.
- [ ] No secrets or sensitive data in assertions/logs.
- [ ] New markers (if added) documented in `pyproject.toml` under `[tool.pytest.ini_options].markers`.
- [ ] Update CHANGELOG under `Unreleased` if behavior or CI is impacted.

---

## Example test template

```python
"""
Test creating a minimal customer and validating API + DB.
"""

import pytest
logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.customers, pytest.mark.api]

def test_create_minimal_customer(create_valid_customer, customer_helper, customers_dao):
    # Create (factory validates schema by default)
    cust = create_valid_customer()
    assert isinstance(cust["id"], int)

    # DB check via DAO helper
    customer_helper.validate_customer_exists_and_matches(email=cust["email"], dao=customers_dao)
```

---

## Troubleshooting tips
- "0 tests collected": run `pytest --collect-only -q tests/` and check `pyproject.toml` / `conftest.py`.
- "No Allure results": ensure `--alluredir` used and `AUTO_ALLURE_REPORT` / Allure CLI handling in CI.
- "Warnings or import-order issues": run without `--disable-warnings`; check for early imports and prefer lazy imports or `pytest.register_assert_rewrite()` in plugin code.

---
