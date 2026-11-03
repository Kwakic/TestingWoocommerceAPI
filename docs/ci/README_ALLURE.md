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

Playwright tracing can be enabled locally for failed tests or for every test:

```bash
# Keep traces only for failed tests
pytest -m ui --browser chromium --tracing retain-on-failure --output reports/playwright

# Keep a trace for every test
pytest -m ui --browser chromium --tracing on --output reports/playwright
```

For a local run, the failed test's Allure result includes its trace ZIP as an
attachment. Download it from the test's Attachments section and inspect it with:

```bash
playwright show-trace path/to/trace.zip
```

The session-persistence test launches persistent browser profiles directly, so
its custom contexts use the same trace mode and output directory through the
`trace_custom_context` fixture.



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
     └── failure-only Playwright traces (opt-in Actions artifact)
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

Failed UI test results include trace evidence without embedding trace contents
in the published Allure report. GitHub Actions uploads the trace ZIPs as
browser-specific `ui-<browser>-playwright-traces` artifacts with seven-day
retention when `PLAYWRIGHT_TRACE_ARTIFACT_ENABLED` is true. CI sets it to
`false` by default in `.github/actions/configure-ci-env/action.yml`; change it
to `true` to enable uploads. When enabled, the Allure result links to the
workflow run. If disabled, Allure explains how to reproduce the trace locally.
In a public repository, enabled artifacts are publicly accessible, so only
enable uploads when trace contents are safe for public access. The local value
is kept in `.env` and `.env.example` for configuration consistency.

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
ui-chromium-playwright-traces  (opt-in, failed tests only; 7 days)

ui-firefox-allure-results
ui-firefox-structured-logs
ui-firefox-junit-results
ui-firefox-playwright-traces  (opt-in, failed tests only; 7 days)

ui-webkit-allure-results
ui-webkit-structured-logs
ui-webkit-junit-results
ui-webkit-playwright-traces  (opt-in, failed tests only; 7 days)
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

**Last updated:** 2026-11-03
