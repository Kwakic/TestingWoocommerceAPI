# 📊 Allure Reporting Guide

A quick guide to understanding how Allure works in this framework.

---

## 🚀 What is Allure?

``` text
pytest
  ↓
reports/allure-results
  ↓
Allure CLI
  ↓
HTML report
```

`pytest.ini` configures:

``` ini
addopts = --alluredir=reports/allure-results
```

so every local run and CI workflow writes results to the same location.

---

## 💻 Local development

### Run tests

``` bash
pytest -m customers
```

The plugin automatically:
- 🧹 Cleans previous results
- 📝 Writes new Allure results
- 🌍 Creates `environment.properties`
- 🏷️ Creates `categories.json`

---

### Preview report (recommended)

``` bash
allure serve reports/allure-results
```

This generates a temporary HTML report, starts a local server and opens
your browser.

---

### Generate a permanent report

``` bash
allure generate reports/allure-results -o reports/allure-report --clean
```

Open it with:

``` bash
allure open reports/allure-report
```
---

## ⚙️ AUTO_ALLURE_REPORT

Set:

``` text
AUTO_ALLURE_REPORT=true
```

The framework automatically runs:

``` text
allure generate reports/allure-results -o reports/allure-report --clean
```

after pytest finishes.

If disabled, only `reports/allure-results` is generated.

---

## 🤖 CI

GitHub Actions automatically:

-   Execute pytest
-   Collect Allure results
-   Generate HTML
-   Publish reports to GitHub Pages
-   Preserve report history

No manual steps are required.

## 📁 Folder structure

``` text
reports/
├── allure-results/
└── allure-report/
```

---

## 🔧 Requirements

-   allure-pytest
-   Allure CLI
-   Java

---

## 📝 Quick Reference


| Task | Command |
| :--- | :--- |
| Run tests | `pytest -m customers` |
| Preview report | `allure serve reports/allure-results` |
| Generate HTML | `allure generate reports/allure-results -o reports/allure-report --clean` |
| Open report | `allure open reports/allure-report` |

💡 **Recommendation:** During development simply run:

``` bash
allure serve reports/allure-results
```

It is the fastest way to inspect your latest test execution.
