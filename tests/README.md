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

- **Execution lane:** `pr`, `smoke`, `regression`, and `preflight` describe when
  a test is selected. Add `pr` only to stable, high-signal cases intended for
  the focused pull-request checks.
- **Test type:** `unit`, `integration`, `contract`, `ui`, and `performance`
  describe what the test exercises. These can overlap with an execution lane.
- **Test traits:** `negative`, `bulk`, `e2e`, `security`, and `graphql` describe
  scenario characteristics and can overlap with both type and lane markers.

Use module-level markers only when every test in that module shares the
classification. Use function-level markers to select individual cases. The
`integration` marker means the test uses the live application/API environment;
it does not by itself mean that the test belongs in the PR lane. Full integration
coverage runs on pushes to `main` and manual runs, while the PR Integration Gate
selects only tests marked `integration` and `pr` that are not already smoke tests.

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
