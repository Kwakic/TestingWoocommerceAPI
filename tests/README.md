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

---

## 🧪 Shared Framework Tests

`tests/shared/` contains framework-level test suites that validate behaviour common to every entity.

Examples include:

- Preflight checks
- REST contract validation
- GraphQL contract validation
- Security validation

Contract tests are separated by protocol:

```text
tests/shared/contracts/
├── rest/
└── graphql/
```

REST contract tests validate REST response contracts.

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
