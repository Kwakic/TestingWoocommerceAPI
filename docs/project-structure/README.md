# 📁 Project Structure at a Glance

Quick reference for navigating the project. For detailed guides, see the [main README](../../README.md).

---

## 🗺️ Visual Map

```
TestEcommerceAPI/
├── 📚 docs/              ← Documentation
├── 🔧 EcommerceAPI/      ← Shared Framework
├── 🧪 tests/             ← Test Suites
├── 📊 reports/           ← Test Results
├── ⚙️  .github/          ← CI/CD Workflows
└── 📦 Root Config        ← pytest.ini, Makefile, etc.
```

---

## 📚 **docs/** — Where to Find What

| Need | Find Here |
|------|-----------|
| **Getting started** | `getting-started/` |
| **Writing tests** | `development/README_TEST_DEVELOPMENT_GUIDE.md` ⭐ |
| **Domain conventions** | `development/team-guides/README_{DOMAIN}.md` |
| **Framework internals** | `framework/` |
| **CI/CD setup** | `ci/` |

---

## 🔧 **EcommerceAPI/** — Shared Framework

```
EcommerceAPI/
├── plugins/          ← pytest fixtures (one per domain)
├��─ src/auth/         ← Authentication implementations
├── src/core/         ← HTTP transport layer
├── src/clients/      ← API client
├── src/{domain}/     ← Domain code (customers, products, orders, coupons)
├── src/shared/       ← Reusable helpers & assertions
├── src/utils/        ← Generic utilities
└── pyproject.toml    ← Package metadata
```

**When to edit:** Adding shared utilities, new domains, fixtures, or auth schemes.

---

## 🧪 **tests/** — Test Suites

```
tests/
├── customers/        ← Domain tests (same structure as others)
│   ├── api/          ← Test files
│   ├── performance/  ← Performance tests
│   ├── data/         ← Test payloads
│   └── conftest.py   ← Domain fixtures
├── products/         ← Domain tests
├── orders/           ← Domain tests
├── coupons/          ← Domain tests
├── shared/           ← Framework-level tests (contracts, security, preflight)
└── conftest.py       ← Shared root fixtures
```

**When to edit:** Adding or updating domain tests.

---

## 📊 **reports/** — Test Artifacts

```
reports/
├── allure-report/    ← Interactive HTML report (open index.html)
├── allure-results/   ← Raw JSON test results
└── logs/             ← Structured test logs by domain
```

**How to use:** Open `allure-report/index.html` in browser after test runs.

---

## ⚙️ **.github/** — CI/CD

| Directory | Purpose |
|-----------|---------|
| `workflows/` | GitHub Actions pipelines (smoke, integration, performance, etc.) |
| `actions/` | Custom actions (setup, cleanup, Docker) |

---

## 🚀 Quick Navigation by Role

### 👤 QA Developer — Writing Tests
- **Edit:** `tests/{domain}/api/test_*.py`
- **Data:** `tests/{domain}/data/`
- **Read:** `docs/development/TEAM_GUIDES/README_{DOMAIN}.md`

### 🛠️ Framework Maintainer — Adding Features
- **Edit:** `EcommerceAPI/src/`
- **Fixtures:** `EcommerceAPI/plugins/`
- **Read:** `docs/framework/README_PLUGINS_REFERENCE.md`

### 🔄 DevOps — CI/CD Pipelines
- **Edit:** `.github/workflows/` and `.github/actions/`
- **Read:** `docs/ci/README_CI_ARCHITECTURE.md`

### 🔍 Debugging Test Failures
- **View:** `reports/allure-report/index.html`
- **Logs:** `reports/logs/{domain}/test/`

---

## 📋 Root Configuration Files

| File | Purpose |
|------|---------|
| `Makefile` | Common commands (`make run`, `make test`) |
| `pytest.ini` | pytest configuration |
| `conftest.py` | Shared root fixtures |
| `.env` / `.env.example` | Environment variables |
| `docker-compose.matrix.yml` | Container setup |
| `Dockerfile` | CI/CD container image |

---

## 🎯 Common Tasks

**Running tests:** `pytest tests/{domain}`  
**Full setup:** `make run`  
**View report:** Open `reports/allure-report/index.html`  
**Add domain test:** Create `tests/{domain}/api/test_*.py`  
**Add shared utility:** Add to `EcommerceAPI/src/utils/`

---

**👉 For detailed info, see [docs structure](./domain-driven-microservice-framework-architecture.txt) or [main README](../../README.md)**
