# 📊 Allure Reporting Guide

A quick guide to understanding how Allure works in this framework.

---

## 🚀 What is Allure?

```text
pytest
  ↓
reports/allure-results
  ↓
Allure CLI
  ↓
HTML report
```

`pytest.ini` configures:

```ini
addopts = --alluredir=reports/allure-results
```

so test execution produces raw Allure results that can be rendered into an
interactive HTML report.

---

## 💻 Local development

### Run API tests

```bash
pytest -m customers
pytest -m "products and graphql"
```

### Run UI tests

```bash
pytest -m ui --browser chromium
pytest -m ui --browser firefox
pytest -m ui --browser webkit
```

The UI tests use the same Allure integration as the API tests.



### Preview a report

```bash
allure serve reports/allure-results
```

This generates a temporary HTML report, starts a local server and opens it in
your browser.

### Generate a permanent report

```bash
allure generate reports/allure-results -o reports/allure-report --clean
allure open reports/allure-report
```

The plugin automatically:
- 🧹 Cleans previous results
- 📝 Writes new Allure results
- 🌍 Creates `environment.properties`
- 🏷️ Creates `categories.json`

---

## ⚙️ AUTO_ALLURE_REPORT

Set:

```text
AUTO_ALLURE_REPORT=true
```

The framework automatically generates:

```text
reports/allure-report
```

after pytest finishes.

When disabled, pytest still produces:

```text
reports/allure-results
```

---

## 🤖 CI Reporting Architecture

GitHub Actions separates test execution from report generation.

```text
Test workflow
     │
     ▼
reusable-test-runner.yml
     │
     ├── Allure raw results
     ├── JUnit XML
     └── structured logs
     │
     ▼
reusable-allure-report.yml
     │
     └── generated HTML report
     │
     ▼
dashboard-publisher.yml
     │
     ▼
GitHub Pages QA Portal
```

### API entity reports

API suites are generated independently per entity and suite:

```text
report-customers-smoke
report-products-integration
report-orders-regression
...
```

The dashboard organizes them as:

```text
/customers/smoke/
/products/integration/
/orders/regression/
```

### UI / Playwright report

UI is a standalone testing domain.

The browser matrix produces:

```text
ui-chromium-allure-results
ui-firefox-allure-results
ui-webkit-allure-results
```

The reusable Allure workflow merges the available browser result sets and
generates one report:

```text
report-ui
```

The QA Portal exposes it at:

```text
/ui/
```

The portal displays the UI report as:

```text
🎭 UI / Playwright    TIER: CRITICAL
    └── Allure Report
```

The UI tier is supplied by the UI workflow (`tier: critical`) rather than by
the API entity metadata registry.

---

## 🌐 Public vs internal reports

Not every CI workflow is published to GitHub Pages.

| Suite | Allure | GitHub Pages |
|---|---|---|
| Smoke | ✅ | ✅ |
| Integration | ✅ | ✅ |
| Regression | ✅ | ✅ |
| Performance | ✅ | ✅ |
| UI / Playwright | ✅ | ✅ |
| Preflight | ✅ raw artifacts | ❌ |
| Contract | ✅ raw artifacts | ❌ |
| Security | ✅ raw artifacts | ❌ |

Security, Contract and Preflight remain artifact-only so internal diagnostic
information is not exposed through the public portal.

---

## 📦 CI artifacts

API entity jobs use predictable artifacts such as:

```text
customers-smoke-allure-results
customers-smoke-structured-logs
customers-smoke-junit-results
```

UI browser jobs use:

```text
ui-chromium-allure-results
ui-chromium-structured-logs
ui-chromium-junit-results

ui-firefox-allure-results
ui-firefox-structured-logs
ui-firefox-junit-results

ui-webkit-allure-results
ui-webkit-structured-logs
ui-webkit-junit-results
```

The browser-specific UI Allure results are merged before HTML generation.

---

## 📈 Persistent Allure History

Public reports preserve Allure history between executions.

Conceptually:

```text
Previous report
     │
     ▼
history/
     │
     ▼
New Allure results
     │
     ▼
Allure generate
     │
     ▼
Updated report
```

This enables:

- 📈 Pass/fail trends
- ⏱ Duration evolution
- 🔁 Retry history
- ⚠️ Flaky test visibility
- 📊 Historical execution analytics

---

## 🔧 Requirements

- `allure-pytest`
- Allure CLI for local HTML generation
- Java for the Allure CLI

CI installs the required Allure CLI and Java runtime during report generation.

---

## 📝 Quick Reference

| Task | Command |
| :--- | :--- |
| Run API tests | `pytest -m customers` |
| Run UI on Chromium | `pytest -m ui --browser chromium` |
| Run UI on Firefox | `pytest -m ui --browser firefox` |
| Run UI on WebKit | `pytest -m ui --browser webkit` |
| Preview report | `allure serve reports/allure-results` |
| Generate HTML | `allure generate reports/allure-results -o reports/allure-report --clean` |
| Open report | `allure open reports/allure-report` |

💡 **Recommendation:** During development, use:

```bash
allure serve reports/allure-results
```

It is the fastest way to inspect the latest local execution.

---

**Last updated:** 2026-09-13
