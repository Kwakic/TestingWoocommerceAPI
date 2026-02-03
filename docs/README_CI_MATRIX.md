# TestEcommerceAPI CI/CD Overview

This document explains the **GitLab CI/CD setup** for the TestEcommerceAPI framework.
It includes details about **dynamic matrix testing**, **environment fan-out**, **preflight checks**, and **enterprise governance** (manual approvals, prod protection, secrets, GitLab Environments UI).

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Stages in GitLab CI](#stages-in-gitlab-ci)
3. [Dynamic Matrix Testing](#dynamic-matrix-testing)
4. [Environment Fan-Out](#environment-fan-out)
5. [Shared Preflight and Performance Tests](#shared-preflight-and-performance-tests)
6. [GitLab Environments UI Integration](#gitlab-environments-ui-integration)
7. [Manual Approvals and Prod Protection](#manual-approvals-and-prod-protection)
8. [Secrets Management](#secrets-management)
9. [Pipeline Examples](#pipeline-examples)
10. [Best Practices](#best-practices)
11. [CI/CD Changes Summary](#ci-cd-changes-summary)

---

## Architecture Overview

The CI/CD pipeline is designed to scale with multiple **entities** (orders, customers, products, coupons) and multiple **environments** (test, staging, prod).

**Pipeline Flow:**

1. Shared preflight tests (run once, hard gate)
2. Deploy to environment (manual approval)
3. Discover entity test suites dynamically
4. Generate `matrix.yml` child pipeline (entity × environment)
5. Run tests in parallel
6. Optional environment verification / performance tests

```
shared_preflight → deploy → discover → matrix → verify
```

---

## Stages in GitLab CI

| Stage     | Purpose                                                       |
| --------- | ------------------------------------------------------------- |
| preflight | Run shared lightweight tests to validate pipeline sanity      |
| deploy    | Manual deployment to target environment (test/staging/prod)   |
| discover  | Dynamically detect entity test suites and generate matrix.yml |
| test      | Run parallel tests for each entity × environment              |
| verify    | Environment verification / performance tests (manual)         |

---

## Dynamic Matrix Testing

### Are `TEAM` and `ENV` hardcoded?

❌ **No — they are generated dynamically, not hardcoded.**

In the generated `matrix.yml` you will see jobs like:

```yaml
variables:
  TEAM: customers
  ENV: test
```

Although these look static, they are **produced automatically** by the discovery logic in `gitlab-ci.yml`.

They come from this nested loop in the `discover_services` job:

```bash
for env in $TARGET_ENVS; do
  for s in $services; do
```

**Where the values come from:**

| Variable | Source                                                        |
| -------- | ------------------------------------------------------------- |
| `TEAM`   | Directory name under `tests/` (e.g. `customers`, `orders`)    |
| `ENV`    | Environment being deployed/tested (`test`, `staging`, `prod`) |

This means:

* Adding a new entity = create a new folder under `tests/`
* Adding a new environment = add a new deploy job (or include it in `TARGET_ENVS`)
* **No manual edits** to `matrix.yml` are required

---

* The **child pipeline** (`matrix.yml`) is generated dynamically.
* For each entity and each environment in `TARGET_ENVS`, a job is created:

Example (dynamic):

```yaml
customers_test:
  stage: test
  image: python:3.11
  variables:
    TEAM: customers
    ENV: test
  script:
    - pip install --upgrade pip
    - pip install -e './EcommerceAPI[dev]'   # NEW STEP
    - pytest tests/customers
```

* **Scales automatically** when new entities are added.
* No manual updates needed for `matrix.yml`.

---

## Environment Fan-Out

* `TARGET_ENVS` is a space-separated variable controlling which environments to test:

```yaml
variables:
  TARGET_ENVS: "test staging"
```

* Jobs are generated for each entity × environment combination:

| TARGET_ENVS  | Generated Jobs                          |
| ------------ | --------------------------------------- |
| test         | customers_test, orders_test, etc.       |
| staging      | customers_staging, orders_staging, etc. |
| test staging | All combinations                        |

* Can be overridden per pipeline run in GitLab UI, schedule, or API.

---

## Shared Preflight and Performance Tests

### Preflight

* Runs once per pipeline (`shared_preflight`)
* Hard failure blocks the pipeline
* Validates pipeline setup and shared sanity
* Uses **pip install -e './EcommerceAPI[dev]'** to install the framework in editable mode
* ⚠ **Requires credentials**: `WC_KEY` and `WC_SECRET` must be set as environment variables or in `.env` for WooCommerce API access

### Performance / Verify

* Runs **once per pipeline**, manually approved
* Only runs when **all entities are selected**
* Ensures stability of the environment

---

## GitLab Environments UI Integration

* Each job is assigned an **environment**:

```yaml
environment:
  name: $ENV
```

* GitLab shows:

  * Last deployment / test history
  * Timeline per environment
  * Job details per environment

* Makes QA, release, and audit easier.

---

## Manual Approvals and Prod Protection

* `deploy_*` jobs are **manual** to enforce human approval before environment deployment
* `prod` deployment:

  * Only triggers on **protected tags**
  * Requires **maintainer approval**
  * Prevents accidental production changes

```yaml
deploy_prod:
  extends: .deploy_template
  environment:
    name: prod
  only:
    - tags
```

* `verify_environment` can also be **manual**, giving full control over costly performance tests.

---

## Secrets Management

* Environment-specific secrets scoped in **GitLab CI/CD → Variables**
* Examples:

  * `API_BASE_URL`
  * `DB_PASSWORD`
  * `AUTH_TOKEN`
  * `WC_KEY` (WooCommerce)
  * `WC_SECRET` (WooCommerce)
* Automatically injected per environment via `$ENV` and `$CI_ENVIRONMENT_NAME`

---

## Pipeline Examples

### Run test only

```bash
TARGET_ENVS="test" SERVICE="customers" gitlab-runner exec docker ...
```

### Full regression

```bash
TARGET_ENVS="test staging" gitlab-runner exec docker ...
```

### Production deployment

```bash
git tag v1.0.0
TARGET_ENVS="prod" git push origin v1.0.0
```

* Prod requires manual approval if using protected tags.

---

## Best Practices

1. **Never duplicate CI files per environment** — dynamic matrix handles fan-out.
2. **Preflight is your hard gate** — catches setup errors early.
3. **Performance / verify tests are expensive** — run manually or nightly.
4. **Manual approvals for staging/prod** — enforce governance.
5. **Use environment-scoped secrets** — avoid hardcoding credentials.
6. **Leverage GitLab Environments UI** — traceability and auditing.

---

## CI/CD Changes Summary

* **New pip install step**:

```bash
pip install -e './EcommerceAPI[dev]'
```

* Ensures framework is installed **editable** for CI runs
* **WooCommerce credentials are required** (`WC_KEY` and `WC_SECRET`)
* Framework imports remain **as-is** to avoid breaking the pipeline
* Preflight and matrix tests now correctly **initialize the shared framework**
