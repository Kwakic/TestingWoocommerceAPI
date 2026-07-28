# 🧪 Test Suite

This directory contains all automated tests for the TestEcommerceAPI framework.

The test suite follows a **domain-driven** structure: each business entity owns its own tests, while framework-level validation lives in a shared area. This organisation promotes clear ownership, scalable growth, and independent CI execution.

---

## 📁 Directory Structure

```text
tests/
├── customers/
├── products/
├── orders/
├── coupons/
├── shared/
│   ├── preflight/
│   ├── contract/
│   └── security/
└── conftest.py
```

## 🧩 Domain Test Suites

Each business entity owns its own test suite.

Typical responsibilities include:

- Smoke tests
- Integration tests
- Regression tests
- Performance tests
- Entity-specific fixtures
- Test data
- Domain configuration

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
- Contract validation
- Security validation

These suites execute once for the framework and automatically discover supported entities where appropriate.

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

• smoke
• integration
• regression
• performance
```

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

Run the complete suite:

```bash
pytest
```

For marker-based execution, see the Test Development Guide.

---

## 📚 Related Documentation

- `docs/development/README_TEST_DEVELOPMENT_GUIDE.md` — How to write tests
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
