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

Performance tests measure API response time with sequential requests. The
customer benchmark sends 3 warm-up requests, excludes those timings, and then
measures 30 customer-list requests by default. It reports the average and an
approximate P95 against configured thresholds.

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
WooCommerce, a database, or network access. GitHub Actions and GitLab CI run
this suite before preflight.

Run the unit tests locally with:

```bash
pytest tests/shared/unit_tests -m unit -v
```

Run both fast checks in CI order with:

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
