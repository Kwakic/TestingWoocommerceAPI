# 🧪 Test Suite

This directory contains all automated tests for the TestEcommerceAPI framework.

The test suite follows a **domain-driven** structure: each business entity owns its own tests, while framework-level validation lives in a shared area. This organisation promotes clear ownership, scalable growth, and independent CI execution.

---

## 📁 Directory Structure

```text
tests/
├── customers/
│   ├── api/                    ← REST API behaviour
│   ├── graphql/                ← GraphQL behaviour
│   └── performance/
├── products/
│   ├── api/
│   ├── graphql/
│   └── performance/
├── orders/
│   ├── api/
│   ├── graphql/
│   └── performance/
├── coupons/
│   ├── api/
│   ├── graphql/
│   └── performance/
├── shared/
│   ├── unit_tests/              ← Isolated framework unit tests
│   ├── preflight/              ← Environment/framework checks
│   ├── contracts/
│   │   ├── rest/               ← REST contract tests
│   │   └── graphql/            ← GraphQL contract tests
│   └── security/               ← Authentication/security tests
└── conftest.py
```

## 🧩 Domain Test Suites

Each business entity owns its own test suite.

Typical responsibilities include:

- REST API tests
- GraphQL API tests
- Smoke tests
- Integration tests
- Regression tests
- Performance tests
- Entity-specific fixtures
- Test data
- Domain configuration

REST and GraphQL behaviour remain under the same business domain:

```text
products/
├── api/              ← REST behaviour
├── graphql/          ← GraphQL behaviour
└── performance/      ← performance tests
```

GraphQL tests are therefore not a separate top-level test domain. They belong
to the entity they exercise.

Each entity also has its own Team Guide under:

```text
docs/development/TEAM_GUIDES/
```

Examples:

- README_CUSTOMERS.md
- README_PRODUCTS.md
- README_ORDERS.md
- README_COUPONS.md

## Pytest marker policy

Markers describe separate dimensions and should be combined intentionally:

- **Execution lane:** `pr`, `smoke`, `regression`, and `preflight` help CI
  select tests for a run. `pr` means a test is included in the focused PR
  validation selection; it does not describe the kind of test.
- **Test type:** `unit`, `integration`, `contract`, `ui`, and `performance`
  describe what the test exercises. These can overlap with an execution lane.
- **Test traits:** `negative`, `bulk`, `e2e`, `security`, and `graphql` describe
  scenario characteristics and can overlap with both type and lane markers.

### What the `pr` marker means

The `pr` marker opts a test into a focused set of checks run for pull requests.
CI combines it with a test-type marker to select a particular lane:

| PR lane | Marker expression | Selection |
| --- | --- | --- |
| Unit | `unit and pr` | Unit tests opted into PR validation |
| Preflight | `preflight and pr` | Framework/environment checks opted into PR validation |
| Smoke | `smoke and pr` | Critical API/UI health cases opted into PR validation |
| Integration | `integration and pr and not smoke` | Curated API/database cases not already selected as smoke tests |
| UI (informational) | `ui and pr` | UI cases run on trusted PRs, outside the required gate |
| Contract (informational) | `contract` | Contract workflow selects this marker; it does not use `pr` |

Marking a test `pr` does **not** create a GitHub check or make the test a merge
blocker by itself. It only makes the test eligible for a workflow whose pytest
filter includes `pr`. The central **PR Quality Gate** determines the required
test results for merging; GitHub branch protection determines whether that
gate is required.

### How to decide whether a test belongs in the PR selection

Add `pr` when the test:

1. Catches a meaningful regression that should be found before merge.
2. Is reliable and repeatable, with isolated test data and no known flakiness.
3. Can run within the PR feedback-time and CI-resource budget.
4. Adds useful coverage beyond an already selected smoke or PR test.

Leave `pr` off when a test is broad, costly, flaky, or better suited to full
post-merge/manual coverage. A slow test can still merit `pr` when its risk
coverage justifies the cost; make that a deliberate team decision. Do not add
`pr` to every test or every module just to make it run on PRs.

The entity/domain marker is inferred from the `tests/<entity>/` path, so do not
add it manually. For example, a module can declare its test type once, while
opting only one stable case into the PR integration subset:

```python
import pytest

pytestmark = pytest.mark.integration


@pytest.mark.pr
def test_create_order_persists_order(order_factory):
    ...


def test_large_order_with_many_line_items():
    ...
```

The first test matches `integration and pr and not smoke`; the second remains
part of the broader Integration suite but is not selected by that PR filter.
If a test is already marked `smoke`, the Integration PR expression excludes it;
the Smoke lane selects it when it also has `pr`.

Use module-level markers only when every test in that module shares the
classification. Use function-level markers when only selected cases should be
in the PR lane. The `integration` marker means the test requires a running test
API and may verify database persistence; it does not by itself put the test in
the PR lane or imply that it uses a production/remote environment.

Preview the selected tests locally before adding or changing markers:

```bash
pytest --collect-only -q tests/orders -m "integration and pr and not smoke"
```

All marker names and descriptions live in [`pytest.ini`](../pytest.ini). Strict
marker validation is enabled, and required PR lanes fail when their marker
filter collects no tests.

## Performance tests

Performance tests live under each entity's `performance/` directory and use
sequential requests. Customers, Products, Orders, and Coupons each send 3
excluded warm-up requests and measure 30 requests by default. Their summaries
report the average, approximate P95, minimum, and maximum against entity-owned
thresholds. Current scenarios cover customer and product lists, processing
orders, and coupon search.

This is useful for spotting broad response-time changes between runs. It does
not measure how many simultaneous users the API can handle or its throughput;
use a dedicated load-testing tool for that. The `PERF_ITERATIONS` environment
variable or `--perf-iterations` option can intentionally override the measured
request count for all performance tests.

---

## 🧪 Shared Framework Tests

`tests/shared/` contains framework-level test suites that validate behaviour common to every entity.

Examples include:

- Isolated unit tests
- Preflight checks
- REST contract validation
- GraphQL contract validation
- Security validation

### Unit tests

`tests/shared/unit_tests/` contains tests for framework logic that runs without
WooCommerce, a database, or network access. In pull-request validation,
GitHub Actions runs Unit and Preflight as independent jobs; the PR Quality Gate
requires both to succeed.

The shared unit suite also checks that the **Manual Entity Tests** dropdown
matches the framework registry and that its matrix selects the requested entities.

Run the unit tests locally with:

```bash
pytest tests/shared/unit_tests -m unit -v
```

To run both fast checks locally in sequence:

```bash
pytest tests/shared/unit_tests -m unit -v && pytest -m preflight -v
```

Contract tests are separated by protocol:

```text
tests/shared/contracts/
├── rest/
└── graphql/
```

The shared REST checks verify successful collection responses and their JSON
transport format. They call the live WooCommerce API and require its URL and
credentials to be configured; they are not part of preflight.

Run the shared REST contract tests with:

```bash
pytest tests/shared/contracts/rest -v
```

GraphQL contract tests validate framework-level GraphQL schema expectations,
such as required types, fields, and mutation structure.

Entity-specific GraphQL behaviour remains under:

```text
tests/<entity>/graphql/
```

These shared suites execute once for the framework and automatically discover
supported entities where appropriate.

---

## 🏗️ Design Philosophy

```text
Business Domain
      │
      ▼
customers/
products/
orders/
coupons/

Each domain owns:

• REST behaviour
• GraphQL behaviour
• smoke
• integration
• regression
• performance
```

GraphQL does not create a separate business domain. It is another API
protocol used by the existing business domains.

Framework-level protocol contracts remain in `tests/shared/contracts/`.

This organisation:

- keeps ownership clear
- scales naturally as new entities are added
- enables independent CI execution
- mirrors the framework architecture

---

## 🚀 Running Tests

### Choose the environment and test selection

`API_ENV` chooses which application and credentials pytest uses. The test path
or `-m` marker expression chooses which tests pytest collects. `-n auto` runs
the selected tests across the available physical CPU cores.

Run the commands from the repository root with the development dependencies
installed in the project virtual environment. `make run` creates/prepares that
environment as part of Docker-backed setup; WAMP users can install the package
with `python -m pip install -e './EcommerceAPI[dev]'` without starting Docker.

| Run mode | Setup and command | What it runs against |
|---|---|---|
| Docker-backed local development (recommended) | First run `make run`; later use `make test` for the full suite or `API_ENV=test pytest -m "orders and smoke" -n auto` for Orders smoke tests. | Pytest runs on the host; WordPress, WooCommerce, and MySQL run in Docker Compose. |
| Existing WAMP site | Copy `.env.wamp.example` to `.env.wamp`, fill in its REST and DB settings, then run `API_ENV=local pytest -m orders -n auto`. | Pytest runs on the host against the existing WAMP installation. REST tests only are supported. |
| Dockerized test runner | Build with `docker build -t ecommerceapi-test-runner .`, then run `make test-docker`; pass selectors with `PYTEST_ARGS='-m "orders and smoke" -n auto'` or a test path/node ID. Use `DOCKER_INFRA=reuse` to keep an existing provisioned stack running. | Pytest runs inside the test-runner container. Managed mode owns and cleans up the Compose application it starts; reuse mode restores the WordPress URLs and leaves infrastructure running. Both persist reports and UI artifacts on the host. |
| GitHub Actions on demand | Choose a suite for one entity or `all` under **Actions → Manual Entity Tests**. [Run an entity suite and open its Allure report](../docs/ci/README_CI_ARCHITECTURE.md#run-an-entity-suite-on-demand) | Each entity job gets its own WooCommerce environment with `API_ENV=ci`. |

**Docker reuse and data:** `DOCKER_INFRA=reuse` retains the running
WordPress/MySQL environment, **not every test-created record**. Pytest cleanup
still runs and may delete owned customers, products, orders or coupons; seeded
data is intended to persist. See the
[Docker Infrastructure Guide](../docs/ci/README_DOCKER_INFRASTRUCTURE.md)
for details.

For WAMP, Bash/Git Bash accepts the inline environment assignment above. In
PowerShell, use:

```powershell
$env:API_ENV = "local"
.\.venv\Scripts\python.exe -m pytest -m orders -n auto
Remove-Item Env:API_ENV
```

`-m orders` runs all collected items with the Orders marker. Add a path such as
`tests/orders/api` when you need to restrict collection to that directory.
WAMP does not support the GraphQL or Playwright UI suites. For the profile
files and endpoint mapping, see the [Environment & CI Guide](../docs/ci/README_ENV_AND_CI.md).

GitHub Actions is the supported CI platform for this repository. The local
`make test-ci` target only runs pytest with clean Allure results; it does not
launch or simulate a CI workflow. See the
[CI Architecture Guide](../docs/ci/README_CI_ARCHITECTURE.md) for CI marker
selections and workflow behavior.

`make run`, direct host pytest and `make test-docker` share a local execution
lock to prevent concurrent test runs against the same mutable WooCommerce
environment. See the [Docker Infrastructure Guide](../docs/ci/README_DOCKER_INFRASTRUCTURE.md)
for managed/reuse behavior, artifact locations and stale-lock recovery.

### When test records are deleted

Look for **🧹 API CLEANUP SUMMARY** at module teardown or **🧹 UI CLEANUP SUMMARY** at test teardown. Each banner names the module or test and shows the deletion outcomes for its registered IDs.

| How the record was created | Who tracks it | When cleanup runs |
|---|---|---|
| REST `create_valid_coupon`, `create_valid_customer`, `create_valid_order`, `create_valid_product` (including calls from UI tests) | The function-scoped creation fixture validates the response and registers the returned ID in `shared_api_resources`, unless `skip_cleanup=True`. | At teardown of that **module fixture on that worker**. Several tests can contribute to one summary. |
| GraphQL product creation | Calling `graphql_resources(databaseId)` adds the product to the same module registry. | At the same module teardown, using the WooCommerce REST DELETE endpoint. |
| Browser creation registered with `ui_resources`, such as a newly registered customer | A separate list of explicit IDs belongs to that **one UI test**. | At function teardown, including after a later assertion fails. Closing a browser context by itself only cleans up browser state. |
| Seed scripts, raw API calls, browser actions and direct provisioner calls | Creation alone adds no ID to either registry. Some deletion tests explicitly delete their own record. | Only an explicit registration or a separate delete covers that record. |

Each API banner covers **one module fixture on one worker**. A UI banner covers **one test**. At the end of pytest, **🧹 SESSION CLEANUP SUMMARY** combines the completed API and UI teardowns into one terminal table. With xdist, the controller prints it once after receiving the workers’ reports. For example, if the creation module registers and deletes 22 coupons and the retrieval module registers and deletes three more, the session’s coupons row shows 25 registered and 25 deleted. The performance test only reads coupons.

| Session column | What it measures |
|---|---|
| Registered | Distinct IDs for that entity reported by teardown. Repeated registration across fixtures or workers counts once. |
| Deleted | Teardown DELETE calls that returned HTTP 200 or 204. |
| Missing | Teardown DELETE calls that returned HTTP 404. |
| Failed | Other DELETE responses and request exceptions. |
| Skipped | Registrations explicitly marked deleted before teardown, or registrations with no configured entity cleanup. |

The outcome columns count fixture actions. If the same ID reaches two fixtures, one may delete it and the other may skip it. The table appears after passing runs and ordinary test failures when there are registered resources to report. If a worker exits without sending its report, the controller names that worker and labels the available totals **partial**. Unregistered records are outside all of these counts.

Read the registered count separately from the DELETE outcomes. An ID explicitly marked deleted is skipped. A successful DELETE response (HTTP 200 or 204) counts as deleted. HTTP 404 is reported separately, and other unconfirmed responses or request exceptions are logged as failures. The helper continues through the remaining IDs. These cleanup errors are logged and can accompany a passing pytest result. Older images used the label **Created during test run** and could count an HTTP error response as a deletion. Check the individual responses when reading an older report.

Both Docker modes run these same fixtures. Use reuse mode to inspect the surviving database. See the [read-only inspection steps](../docs/ci/README_DOCKER_INFRASTRUCTURE.md#inspect-test-data-after-a-run) and [known gaps in registration](../docs/development/README_TEST_DATA_ARCHITECTURE.md#cleanup-coverage-and-limits).

### Common pytest selections

Run a single domain:

```bash
pytest tests/customers
```

Run shared framework tests:

```bash
pytest tests/shared
```

Run an entity's GraphQL tests:

```bash
pytest tests/products/graphql -v
```

Run shared GraphQL contract tests:

```bash
pytest tests/shared/contracts/graphql -v
```

Run the complete suite:

```bash
pytest
```

Run the complete suite in parallel:

```bash
pytest -n auto
```

`pytest-xdist[psutil]` is installed through the development dependencies.
`-n auto` uses the available physical CPU cores. Tests must create and clean up
their own mutable data so their result does not depend on worker order.

For marker-based execution, see the Test Development Guide.

---

## 📚 Related Documentation

- `docs/development/README_TEST_DEVELOPMENT_GUIDE.md` — How to write tests
- `docs/development/README_GRAPHQL_TESTING_GUIDE.md` — GraphQL testing, authentication, fixtures, and contracts
- `docs/development/README_ARCHITECTURE.md` — Framework architecture
- `docs/ci/README_CI_ARCHITECTURE.md` — CI workflows
- `docs/framework/README_PLUGINS_REFERENCE.md` — Plugin system
- `docs/development/TEAM_GUIDES/` — Entity-specific conventions

---

## 🎯 Key Principles

- Business entities own their own tests.
- Shared framework tests validate common infrastructure.
- Team Guides document entity-specific conventions.
- The Test Development Guide documents framework-wide testing practices.
- Respect domain boundaries.

---

Happy testing! 🚀
