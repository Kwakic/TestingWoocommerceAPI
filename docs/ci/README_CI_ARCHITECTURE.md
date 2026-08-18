# 📚 CI/CD Architecture & Allure Reporting Guide

Your framework has evolved beyond a "simple pytest project." You now have:

- ✅ Layered REST + GraphQL API testing
- ✅ Segmented CI/CD pipelines
- ✅ Dockerized test environments
- ✅ Structured logging
- ✅ Allure reporting with history tracking
- ✅ GitHub Pages publishing
- ✅ Performance & contract testing
- ✅ Smoke validation & security testing
- ✅ Trend/history preservation

Your custom Allure integration implements many advanced reporting concepts.

---

# 🎯 1. CI/CD Philosophy

Your pipelines should answer **one specific question each**:

| Workflow | Question | Purpose |
|----------|----------|---------|
| **preflight.yml** | Can the framework start safely? | Ultra-fast validation; fast feedback |
| **smoke.yml** | Are critical business flows healthy? | Deployment gate; powers badge |
| **contract.yml** | Did the REST/GraphQL API contract or schema change? | Contract validation; diagnostics |
| **integration.yml** | Does API state match DB state? | End-to-end integration validation |
| **regression.yml** | Did we break anything? | Full coverage; trends & history |
| **performance.yml** | Is the system getting slower? | Latency tracking; SLA validation |
| **security.yml** | Are auth/permission rules still safe? | Auth boundaries; internal audit |



## 🚨 Environment Gate (Runtime Validation)

All test workflows that use the API rely on shared **environment validation** performed by the API client fixtures.

This validation runs at the start of the relevant pytest session when API client fixtures are required:

- API is reachable
- Credentials are valid
- Environment is correctly configured

If validation fails:

- The job exits immediately
- No tests are executed
- Exit code `10` is used to distinguish infra failures from test failures

### Why this design

- Avoids adding a dedicated CI stage
- Eliminates redundant checks
- Reduces CI runtime cost
- Prevents noisy test failures

### CI Observability

CI systems can detect environment failures via exit code:

```bash
if [ $? -eq 10 ]; then
  echo "🚨 Environment failure"
fi
```

### Why Segmentation Matters

Splitting pipelines by intent because:

- **⚡ Faster feedback** — Developers get PR results in 1–3 min, not 20+ min
- **📊 Cleaner dashboards** — Each workflow has its own Allure + GitHub Pages view
- **📈 Stable trends** — Regression always runs the same tests (not mix of preflight + smoke + contract)
- **👥 Easier ownership** — Each team owns specific workflow
- **💰 Lower CI costs** — Don't run heavy tests on every PR
- **🔍 Clearer debugging** — Failed job = clear root cause

---

# 2. Recommended Workflow Architecture

## 🏛️ Repository Architecture

```text
.github/
│
├── actions/
│      configure-ci-env
│      docker-cleanup
│      ...
│
├── workflows/
│      smoke.yml
│      integration.yml
│      ...
│
├── scripts/
│      generate_matrix.py
│
EcommerceAPI/
│
└── plugins/
       entities.py
       entity_metadata.py
       entity_discovery.py
```

---

# 🌍 Environment Selection

The framework supports multiple execution environments. The selected environment determines which API endpoint is used during test execution.

| Execution Context | `API_ENV` | Description |
|-------------------|-----------|-------------|
| Local development (Docker Desktop) | `test` | Tests run on the host, WordPress runs in Docker (`localhost:8888`) |
| Local development (no Docker) | `local` | Tests and WordPress both run locally |
| Tests running inside Docker | `docker` | Uses the Docker network (`wordpress`) |
| GitHub Actions | `ci` | GitHub runner communicates with Docker services (`localhost:8080`) |
| Shared development server | `dev` | Shared development environment |
| Staging | `staging` | Pre-production environment |
| Production | `prod` | Production environment |

All GitHub Actions workflows obtain their environment
configuration exclusively through the reusable
configure-ci-env composite action.

This guarantees consistent `API_ENV` selection across
Smoke, Integration, Regression, Performance,
Contract, Security and Preflight workflows.

---

### Why `.env` no longer contains `WC_API_URL`

Previous framework versions stored the API endpoint in `.env`.

The framework now resolves the endpoint dynamically from
`API_ENV` and the entity configuration (`config_<entity>.py`).

As a result:

- `.env` stores credentials only.
- Entity configuration owns endpoint mappings.
- Changing environments requires only changing `API_ENV`.

This removes duplicated configuration and keeps infrastructure
selection independent from authentication.

---


## 🌱 Local Bootstrap Architecture

The framework automatically provisions a complete WooCommerce testing
environment for local development.

The bootstrap process intentionally separates responsibilities so that
each component has a single, well-defined purpose.

### Bootstrap flow

```text
make run
    │
    ▼
Create .env (if missing)
    │
    ▼
Start Docker services
    │
    ▼
Bootstrap WordPress
    │
    ▼
Install WooCommerce
    │
    ▼
Generate fresh REST API credentials
    │
    ▼
write_env_credentials.sh
    │
    ▼
Update .env
    │
    ▼
pytest
```

### Component responsibilities

**Makefile**

- Creates `.env` from `.env.example` when necessary
- Starts Docker
- Orchestrates the complete bootstrap process

**setup.sh**

- Installs WordPress
- Installs WooCommerce
- Generates fresh WooCommerce REST API credentials
- Outputs credentials in a machine-readable format

**write_env_credentials.sh**

- Updates only `WC_KEY` and `WC_SECRET`
- Preserves all existing developer configuration
- Never modifies endpoint configuration

This separation allows the same bootstrap script to be reused unchanged by both local development and GitHub Actions.

---

### 🖥️ Windows (Git Bash)

Git Bash automatically rewrites Unix paths passed to Docker.

For WP-CLI commands this may transform

```
/var/www/html
```

into

```
C:/Program Files/Git/var/www/html
```

causing WordPress bootstrap to fail.

The framework automatically disables path conversion by setting

```
MSYS_NO_PATHCONV=1
```

before executing Docker Compose commands.

Linux, macOS and GitHub Actions are unaffected.

---

## 👉 Recommended Usage

| Where | `API_ENV` |
|-------|-----------|
| Local development | `test` |
| GitHub Actions | `ci` |
| Docker-native execution | `docker` |

> **Note**
> - All GitHub Actions workflows use `API_ENV=ci`.
> - Developers should normally use `API_ENV=test` when running tests locally.

---

## 🔗 Backward Compatibility

The framework primarily uses the `API_ENV` environment variable to select the execution environment.

For compatibility with older framework versions, the legacy `ENV` variable is still accepted as a fallback.

The active environment is resolved using:

```python
os.getenv("API_ENV") or os.getenv("ENV", "test")
```

New projects should always use `API_ENV`.

---

## 📊 Reporting Strategy

Public Allure reports are organized first by **entity** (customers, orders, products, coupons..) and then by **test suite** (smoke, integration, regression, performance).

This mirrors the framework's domain-driven architecture, allowing each microservice to own its own testing lifecycle while keeping GitHub Pages scalable as additional entities are introduced.

---

## 🔀 CI Flow

```text
                         GitHub Actions
                               │
              ┌────────────────┴────────────────┐
              │                                 │
       Entity workflows                   Shared workflows
              │                                 │
       entity discovery                 Preflight / Contract / Security
              │                                 │
       build entity matrix                    │
              │                                 │
       ┌──────┼──────┐                         │
       ▼      ▼      ▼                         │
     Smoke Integration Regression             │
       │      │      │                         │
       └──────┼──────┘                         │
              │                                 │
              └────────────┬────────────────────┘
                           ▼
                reusable-test-runner.yml
                           │
                ┌──────────┴──────────┐
                ▼                     ▼
       Entity Allure reports    Shared artifacts
                │
                ▼
       reusable-allure-report.yml
                │
                ▼
       dashboard-publisher.yml
                │
                ▼
            GitHub Pages

```
👉 The matrix includes optional ownership metadata (for example team). When omitted, the framework defaults the team to the entity name.

---

## 🤖 GitHub Pages limitation

GitHub Pages accepts only one deployment at a time.

If two report-producing workflows (for example Smoke and Integration)
finish simultaneously, GitHub may cancel one of the deployments.

This is a GitHub Pages platform limitation rather than a framework limitation.

For this project each workflow remains independently executable and
independently publishes its own report.

This keeps the CI architecture simple, reusable and easy to understand.

Environments commonly publish reports to dedicated artifact
repositories or static hosting platforms (Azure Storage, Amazon S3,
Artifactory, Nexus, internal web servers, etc.), where this limitation
does not exist.

1. [x] Framework owns discovery.
2. [x] Framework owns metadata.
3. [x] GitHub Actions consumes metadata.
4. [x] Deployment is independent.
5. [x] Reports are organized as:

```
customers/
    smoke/
    integration/
    regression/
    performance/
```

GitHub Pages deployments are serialized by GitHub.

If multiple workflows finish simultaneously,
one deployment may remain queued or be cancelled.

The generated artifacts are still preserved and
rerunning the workflow republishes the report.

This is a GitHub Pages limitation rather than
a framework limitation.

---
## 🎨 Design principles

The CI/CD platform follows six principles:

1. The framework is the single source of truth.
2. Framework entities are centrally registered.
3. GitHub Actions orchestrates, it does not own metadata.
4. Every workflow answers one specific quality question.
5. Workflows remain independently executable.
6. Public dashboards are reserved for operational test suites
   (Smoke, Integration, Regression and Performance).

---
## 🧬 Entity vs Shared Test Suites

The framework contains two categories of automated test suites.

### 1. Entity Suites

Entity suites execute independently for each discovered framework entity.

Examples:

- Smoke
- Integration
- Regression
- Performance

These workflows use framework entity registry and execute once for every supported entity (customers, orders, products, coupons, ...).

Each entity receives its own:

- workflow execution
- artifacts
- Allure history
- GitHub Pages report (when enabled)

This approach keeps reports isolated and allows every microservice to own its own quality metrics.

---

### 2. Shared Framework Suites

Shared Framework suites validate the testing framework or platform itself rather than individual business entities.

Examples:

- Preflight
- Contract
- Security

These workflows execute once for the entire framework.

These workflows intentionally do not use framework entity discovery because they validate the testing framework itself
rather than individual business domains.

Typical validations include:

- framework startup
- authentication
- API contracts
- schema validation
- environment configuration

For this reason, their workflow summary displays:

```text
Scope: Shared Framework
```

instead of:

```text
Entity: customers
```
---

### 📍 Missing Allure Artifacts

During framework development, some discovered entities may not yet contain
implemented tests.

In this situation, the reusable test runner intentionally skips test
execution for that entity, so no Allure results artifact is produced.

The reusable report workflow still attempts to download the expected
artifact. GitHub Actions may therefore display an **"Artifact not found"**
annotation before the workflow detects the missing artifact.

The workflow then converts this expected condition into a clean report
summary, for example:

```text
Report Summary

Entity: orders
Status: SKIPPED
Reason: No Allure results artifact found
```

This behaviour is expected and does **not** indicate a CI failure.

As additional entities gain test coverage, the corresponding Allure
artifacts will be generated automatically and the annotations will
disappear without requiring workflow changes.


---

## 2.1 preflight.yml ⚡

### Purpose
Ultra-fast validation before expensive infrastructure tests (it checks framework sanity).

### What It Tests
- Framework imports & boot
- Environment loading & configuration
- Fixture sanity checks
- Basic connectivity validation

### Typical Runtime
**1–3 minutes**

### Pytest Command
```bash
 pytest \
   -m "preflight" \
   -ra \
   -v \
   --maxfail=1 \
   --durations=5 \
   --clean-alluredir \
   --junitxml=reports/junit/results.xml \
   --alluredir=reports/allure-results
```

### Triggers
```yaml
on:
  pull_request:          # Every PR
  workflow_dispatch:     # Manual
```

### Allure Report?
❌ **NO** — Operationally low-value for dashboards

### GitHub Pages?
❌ **NO** — Skip report generation entirely

### Artifacts produced during runtime?
✅ **YES**
* `preflight-allure-results/` — Diagnostic raw data
* `preflight-structured-logs/` — Structured logs for troubleshooting
* `preflight-junit-results/` — A structured text file (XML) listing all tests and their results

### Key CI Variables
```yaml
# Minimal setup — no Docker needed
cache: pip  # Critical for speed
```

### Report Structure
- **Dashboard location:** `https://username.github.io/repo/`
  (Each implemented entity publishes its own report. As new entities are added to the framework, reports become
available automatically.)
- **Badge:** Shows last smoke run status

### Why This Configuration?
- **PR-only trigger** ensures developers get instant feedback
- **No Docker** means no infrastructure spin-up delays
- **No Allure** keeps dashboard clean (preflight is developer-focused, not operational)
- **`--maxfail=1`** stops immediately on first failure (fail-fast)

---

## 2.2 smoke.yml (Critical business validation) 🔥

### Purpose
Validate critical business paths. Powers README badge & deployment gate.

### What It Tests
- Customer creation/retrieval/update
- Login & authentication flows
- Order placement & retrieval
- Essential business endpoints

### Typical Runtime
**3–10 minutes**

### Pytest Command
```bash
pytest \
  -m "smoke" \
  -ra \
  --durations=10 \
  --maxfail=3 \
  --clean-alluredir \
  --junitxml=reports/junit/results.xml \
  --alluredir=reports/allure-results
```

### Triggers

```yaml
on:
  pull_request:
    branches: [ main ]    # PR quality gate

  push:
    branches: [ main ]    # Post-merge validation

  workflow_dispatch:      # Manual
```

### Trigger Strategy

Smoke tests run in two CI contexts:

* **Pull requests targeting `main`**
  * Validate critical business paths before merge
  * Act as a PR quality gate
  * Provide fast feedback on application changes

* **Pushes to `main`**
  * Validate the merged code
  * Provide deployment confidence
  * Power the README status badge

This ensures critical business flows are validated both before and after merge.

### Allure Report?
✅ **YES** — Publishes to GitHub Pages

### GitHub Pages?
✅ **YES** — Powers `README.md` badge

### Artifacts produced during runtime?
✅ **YES**
* `smoke-allure-reports/` — Interactive HTML dashboard
* `smoke-allure-results/` — Diagnostic raw data
* `smoke-structured-logs/` — Structured logs for troubleshooting
* `smoke-junit-results/` — A structured text file (XML) listing all tests and their results


### Key CI Variables
```yaml
AUTO_ALLURE_REPORT=false
ENABLE_STRUCTURED_LOGS=true
STRICT_ENTITY_DISCOVERY=true
SESSION_ID=${{ github.run_id }}
API_ENV=ci
```

### Report Structure
- **Dashboard location:** `https://username.github.io/repo/customers/smoke`
  - (Currently only the Customers entity publishes public reports. As additional entities are implemented, reports will be available under /orders/, /products/, /coupons/, etc.)
- **History:** Tracks run-to-run pass/fail trends
- **Badge:** Shows last smoke run status

### Why This Configuration?
- **Push to main only** ensures stable test population for trends
- **Allure + Pages** provides operational visibility & confidence signal
- **Maxfail=3** prevents cascading failures (stops after 3rd failure)
- **Structured logs** enable deep diagnostics on failures

---

## 2.3 integration.yml (API + Database validation) 🔗

### Purpose

Validate full API + database integration behavior across services.

**This suite verifies that:**

* API operations correctly persist data
* Database state matches API responses
* Cross-layer consistency is maintained
* End-to-end business flows work correctly

### What It Tests

* API + DB consistency validation
* DAO layer verification
* Timestamp synchronization
* CRUD lifecycle validation
* End-to-end entity workflows
* State persistence correctness

### Typical Runtime

**5–20 minutes**

### Pytest Command

```bash
pytest \
  -m "integration" \
  -ra \
  --durations=15 \
  --clean-alluredir \
  --junitxml=reports/junit/results.xml \
  --alluredir=reports/allure-results
```



### Triggers

```yaml
on:
  pull_request:
    branches: [ main ]    # PR integration validation

  push:
    branches: [ main ]    # Post-merge validation

  workflow_dispatch:      # Manual
```
### Trigger Strategy

Integration tests run on pull requests and pushes to `main`.

* **Pull requests**
  * Validate API + database consistency before merge
  * Detect persistence and cross-layer regressions early
  * Provide integration-level feedback during code review
* **Pushes to `main`**
  * Validate the merged code
  * Provide post-merge operational confidence
  * Maintain historical integration trends

This ensures critical business flows are validated both before and after merge.

Integration tests may be configured as a required or non-required
pull-request check through GitHub branch protection/rulesets.

For this project, the recommended production configuration is to make
integration tests a `required PR check` once the suite is stable.


### Allure Report?

✅ **YES** — Published to GitHub Pages

### GitHub Pages?

✅ **YES** — Separate dashboard at `/integration`

### Artifacts produced during runtime?

✅ **YES**

* `integration-allure-report/` — Interactive HTML dashboard
* `integration-allure-results/` — Raw Allure diagnostics
* `integration-structured-logs/` — Structured framework logs
* `integration-junit-results/` — JUnit XML results

### Key CI Variables

```yaml
AUTO_ALLURE_REPORT=false
ENABLE_STRUCTURED_LOGS=true
STRICT_ENTITY_DISCOVERY=true
SESSION_ID=${{ github.run_id }}
API_ENV=ci
```

### Report Structure

* **Dashboard location:** `https://username.github.io/repo/customers/integration`
* **History enabled** for trend analysis
* **Separate from smoke/regression** to avoid trend contamination

### Why This Configuration?

* Integration tests are heavier than smoke tests
* DB verification benefits strongly from Allure diagnostics
* Separate trends help isolate integration instability
* Structured logs provide API + DB correlation visibility


---
## 2.4 contract.yml 📋

### Purpose
Validate REST and GraphQL API contracts and response schemas before regression runs.

REST and GraphQL contract tests run through the same shared `contract.yml` workflow; GraphQL does not require a separate CI workflow.

### What It Tests
- REST API contract validation
- GraphQL API contract validation
- JSON schema validation
- GraphQL response and type validation
- Required/immutable field validation
- Response structure correctness
- API contract compatibility

### Typical Runtime
**5–15 minutes**

### Pytest Command
```bash
pytest \
 -m "contract" \
 -ra \
 --durations=10 \
 --clean-alluredir \
 --junitxml=reports/junit/results.xml \
 --alluredir=reports/allure-results
```

### Triggers

```yaml
on:
  pull_request:
    branches: [ main ]    # PR contract validation

  push:
    branches: [ main ]    # Post-merge validation

  workflow_dispatch:      # Manual
```
### Trigger Strategy

Contract tests run on both pull requests and pushes to main.

* Pull requests
  * Validate REST and GraphQL contracts before merge
  * Detect schema and response-structure changes early
  * Protect API compatibility
* Pushes to main
  * Validate the merged API contract
  * Maintain post-merge confidence
  * Preserve diagnostic artifacts for troubleshooting

Contract validation should be configured as a **required PR check.**

A contract failure indicates that an API change may be incompatible
with its consumers and should therefore prevent the pull request from
being merged.


### Allure Report?
⚠️ **Artifact only** — Contract validation remains internal and is intentionally not published to GitHub Pages.

### GitHub Pages?
❌ **NO** — Not for public dashboard

### Artifacts produced during runtime?
✅ **YES**
* `contract-allure-results/` — Diagnostic raw data
* `contract-structured-logs/` — Structured logs for troubleshooting
* `contract-junit-results/` — A structured text file (XML) listing all tests and their results

### Key CI Variables
```yaml
ENABLE_STRUCTURED_LOGS=true
API_ENV=ci
SESSION_ID=${{ github.run_id }}
```

### Report Structure
- **Dashboard location:** `https://username.github.io/repo/`
- **Badge:** Shows last smoke run status

### Why This Configuration?
- **Push trigger** catches REST and GraphQL contract changes early
- **No public Allure** keeps dashboard focused on operational metrics
- **Artifacts only** allow developers to debug REST and GraphQL contract failures
- **Structured logs** provide detailed request/response data

---

## 2.5 regression.yml (Full functional validation) 🔬

### Purpose
Full comprehensive testing. Powers historical trend analysis & nightly validation.

### What It Tests
- **All** CRUD operations (create, read, update, delete)
- Positive & negative scenarios
- Edge cases & error handling
- Database consistency checks
- Bulk operations
- Integration flows
- Contract validation
- Business rule validation

### Typical Runtime
**Long** (20–60 min depending on suite)

### Pytest Command
```bash
pytest \
  -m "regression" \
  -ra \
  --durations=20 \
  --clean-alluredir \
  --junitxml=reports/junit/results.xml \
  --alluredir=reports/allure-results
```

### Triggers
```yaml
on:
  schedule:
    - cron: "0 2 * * *"  # Daily 2 AM UTC
  workflow_dispatch:      # Manual
```

### Allure Report?
✅ **YES** — Historical dashboard critical for trends

### GitHub Pages?
✅ **YES** — Separate from smoke at `/regression`

### Artifacts produced during runtime?
✅ **YES**
* `regression-allure-reports/` — Interactive HTML dashboard
* `regression-allure-results/` — Diagnostic raw data
* `regression-structured-logs/` — Structured logs for troubleshooting
* `regression-junit-results/` — A structured text file (XML) listing all tests and their results


### Key CI Variables
```yaml
ENABLE_STRUCTURED_LOGS=true
SESSION_ID=${{ github.run_id }}
API_ENV=ci
```

### Report Structure
- **Dashboard location:** `https://username.github.io/repo/customers/regression`
- **History:** Full trend analysis enabled
- **Separate from smoke** to maintain distinct trend graphs
- **Badge:** Shows last smoke run status


### Why This Configuration?
- **Nightly schedule** keeps costs low while maintaining coverage
- **Separate destination_dir** prevents smoke/regression trends from mixing
- **Long timeout acceptable** (no developer waiting)
- **Allure + history** enables performance trending & flaky test detection

---

## 2.6 performance.yml (Performance trends) ⏱️

### Purpose
Track API latency & response times over time. Detect performance regressions early.

### What It Tests
- Endpoint response times (p50, p95, p99)
- Request duration validation
- Performance anomaly detection
- SLA compliance

### Typical Runtime
**Varies** (usually 10–30 min with iterations)

### Pytest Command
```bash
pytest \
  -m "performance" \
  -ra \
  --durations=20 \
  --clean-alluredir \
  --junitxml=reports/junit/results.xml \
  --alluredir=reports/allure-results
```

### Environment Variables
```yaml
PERF_ITERATIONS=5           # Run each test 5x for stats
ENABLE_STRUCTURED_LOGS=true
SESSION_ID=${{ github.run_id }}
API_ENV=ci
```

### Triggers
```yaml
on:
  schedule:
    - cron: "0 4 * * 0"  # Sunday 4 AM UTC
  workflow_dispatch:      # Manual
```

### Allure Report?
✅ **YES** — Trend graphs mandatory for performance

### GitHub Pages?
✅ **YES** — Separate dashboard at `/performance`

### Artifacts produced during runtime?
✅ **YES**
* `performance-allure-reports/` — Interactive HTML dashboard
* `performance-allure-results/` — Diagnostic raw data
* `performance-structured-logs/` — Structured logs for troubleshooting
* `performance-junit-results/` — A structured text file (XML) listing all tests and their results


### Report Structure
- **Dashboard location:** `https://username.github.io/repo/customers/performance`
- **Metrics tracked:** Response times, durations, outliers
- **History enabled** for SLA trending
- **Badge:** Shows last smoke run status

### Why This Configuration?
- **Weekly schedule** (Sunday) reduces costs while catching degradation
- **Iterations** enable statistical analysis (p95 detection)
- **Separate destination** keeps performance trends isolated
- **Structured logs** capture detailed request/response data

---

## 2.7 security.yml 🔒

### Purpose
Validate authorization & authentication boundaries. Internal audit only (no public dashboard).

### What It Tests
- Invalid credentials rejection
- Missing permissions enforcement
- Token expiration handling
- Auth bypass prevention attempts
- Role-based access control

### Typical Runtime
**5–20 minutes**

### Pytest Command
```bash
pytest \
  -m "security" \
  -ra \
  --durations=10 \
  --clean-alluredir \
  --junitxml=reports/junit/results.xml \
  --alluredir=reports/allure-results
```

### Triggers
```yaml
on:
  schedule:
    - cron: "0 3 * * 0"  # Sunday 3 AM UTC
  workflow_dispatch:      # Manual
```

### Allure Report?
⚠️ **Artifact only** — NOT published to GitHub Pages

### GitHub Pages?
❌ **NO** — Security data stays internal

### Artifacts produced during runtime?
✅ **YES**
* `security-allure-reports/` — Interactive HTML dashboard
* `security-structured-logs/` — Structured logs for troubleshooting
* `security-junit-results/` — A structured text file (XML) listing all tests and their results


### Key CI Variables
```yaml
ENABLE_STRUCTURED_LOGS=true
SESSION_ID=${{ github.run_id }}
API_ENV=ci
```
### Report Structure
- **Dashboard location:** `https://username.github.io/repo/`
- **History:** Tracks run-to-run pass/fail trends
- **Badge:** Shows last smoke run status

### Why This Configuration?
- **No public dashboard** prevents exposure of security test details
- **Artifacts only** allows team to audit without external visibility
- **Structured logs** provide evidence trail for security reviews
- **Sunday schedule** aligns with regression (other nightly tests)


## Pull Request Quality Gate

Every pull request targeting `main` executes the fast-to-medium
validation suites before merge:

```text
Pull Request
     │
     ├── Preflight
     │
     ├── Smoke
     │
     ├── Contract
     │
     └── Integration
            │
            ▼
      Required checks
            │
       ┌────┴────┐
       ▼         ▼
     FAIL       PASS
       │         │
       ▼         ▼
   Block PR    Merge

```

>Pull requests targeting main execute Preflight, Smoke, Contract, and Integration validation. These workflows are configured as required status checks, preventing merges when any required quality gate fails.


## Required PR Checks

| Suite       | Purpose                          | PR       |
| ----------- | -------------------------------- | -------- |
| Preflight   | Framework and environment sanity | Required |
| Smoke       | Critical business paths          | Required |
| Contract    | REST/GraphQL compatibility       | Required |
| Integration | API + database consistency       | Required |


Heavy suites are intentionally excluded from the PR gate:

| Suite       | Trigger | Reason                      |
| ----------- | ------- | --------------------------- |
| Regression  | Nightly | Long-running                |
| Performance | Weekly  | Stable environment required |
| Security    | Weekly  | Deeper security validation  |





---


# 3. Understanding Allure Reporting

Your custom Allure integration automatically:

- ✅ Generates environment metadata (framework, version, Git info)
- ✅ Injects CI metadata (job URL, run ID, branch)
- ✅ Tracks team ownership dynamically
- ✅ Creates `categories.json` for failure classification
- ✅ Attaches framework configuration
- ✅ Preserves deterministic session identity
- ✅ Maintains run summaries (pass/fail counts)
- ✅ Manages history for trend analysis

---

# 4. What Allure Stores

Allure captures comprehensive test execution data:

| Data Type | Example | Use Case |
|-----------|---------|----------|
| Test status | passed/failed/skipped | Overall health |
| Duration | 450ms, 2.5s | Performance trending |
| Logs & attachments | JSON payloads, screenshots | Failure debugging |
| Environment metadata | `ENV=ci`, `version=dev-local` | Run traceability |
| Git metadata | branch, commit SHA | Change correlation |
| CI metadata | job URL, run ID | CI linkage & artifacts |
| Categories | timeout, server error, schema | Failure classification |
| History | 100+ previous runs | Trend analysis & flakiness |
| Request/response | Full HTTP data | Audit trail |

---

# 5. Allure Environment Tab

Your plugin automatically generates:

```properties
ENV=ci
framework=EcommerceAPI
framework_version=dev-local
git_commit=abc123def456...
git_branch=main
ci_provider=github
ci_job_url=https://github.com/user/repo/actions/runs/12345
session_id=12345
run_timestamp=2026-05-08T15:30:00Z
```

**This powers:**
- Environment tab visibility
- Run traceability & CI linkage
- Deterministic session identity (reproducibility)
- Audit trail for security reviews

---

# 6. Structured Logs

Your framework supports structured JSONL logs (JSON Lines format).

**Logs typically contain:**
- Timestamps (ISO 8601)
- Endpoint calls (method, URL, params)
- Request/response payloads
- Request duration & status codes
- Correlation IDs & session IDs
- Failures & retries
- Database queries & state changes

**Why they're valuable:**
- 📍 Precise failure root cause analysis
- 🔗 Full request/response audit trail
- 📊 Performance metrics & bottleneck detection
- 🔐 Security audit trail (who accessed what)

---

# 7. Where to Find Artifacts

## GitHub Actions Interface

1. Navigate to: **Actions → Workflow Run → Artifacts**
2. Download:
   - `allure-results/` — Raw Allure data (for re-running reports)
   - `allure-report/` — Generated HTML dashboard
   - `structured-logs/` — JSONL files for debugging

## Programmatically

```bash
# Download a specific artifact
gh run download <RUN_ID> -n allure-results
```

---

# 8. Debugging Failures: Step-by-Step

### Step 1: Check Workflow Status
```
GitHub Actions → [Workflow Name] → View Details
```
Look for:
- Which job failed (test, report, deploy)
- Error message summary

### Step 2: Review pytest Output
```
Jobs → [Failed Job] → pytest output
```
Look for:
- Assert failures
- Exception messages
- Database connection errors

### Step 3: Download Artifacts
```
Artifacts → [artifact name] → Download
```
Examine:
- `allure-results/history/` — Trend data
- `structured-logs/` — Request/response details
- `allure-report/index.html` — Full dashboard

### Step 4: Analyze Allure Report
```
Open allure-report/index.html in browser
```
Navigate to:
- **Overview** — Pass/fail summary
- **Failures** — Failed test details
- **Environment** — CI metadata & config
- **Timeline** — Test execution order
- **Categories** — Failure classification

### Step 5: Check CI Metadata
In Allure report Environment tab:
- `ci_job_url` — Link to failed GitHub Actions run
- `git_commit` — Exact commit that failed
- `git_branch` — Branch being tested
- `session_id` — Correlation ID for logs

---

# 9. Understanding Allure History

**History enables critical analytics:**

- 📈 **Trend charts** — Pass/fail evolution, duration trends
- 🔄 **Flaky test detection** — Tests that pass/fail randomly
- 📉 **Duration evolution** — Performance regression detection
- 🎯 **Pass rate tracking** — Overall suite health trending

### How History Works

1. **First run** — Allure creates initial history
2. **Subsequent runs** — New results appended to `history/`
3. **Report generation** — Allure merges history into report
4. **Trend charts** — Shows last N runs

### Your Setup (Correct Pattern)

```yaml
# Restore history from gh-pages
cp -r gh-pages/history/. reports/allure-results/history/

# Generate report (includes history)
allure generate reports/allure-results -o reports/allure-report

# Publish back to gh-pages
deploy to: gh-pages (keep_files: true)
```

**This creates a virtuous cycle:**
- Run → Generate → Publish → **Next run inherits history** → Trend analysis works

---

# 10. Why Stable Test Suites Matter for Trends

**Problem: Mixed test suites create unstable trend graphs**

❌ **BAD** (don't do this):
```bash
pytest -m "preflight or smoke or contract"
# Run 1: 50 tests (preflight doesn't exist today, only smoke & contract)
# Run 2: 75 tests (preflight added midway)
# Trend chart shows sudden jump in test count (not a real degradation!)
```

✅ **GOOD** (do this):
```bash
# smoke.yml → Always runs same smoke tests
pytest -m "smoke"

# regression.yml → Always runs same regression tests
pytest -m "regression"

# performance.yml → Always runs same performance tests
pytest -m "performance"
```

**Result:**
- Each workflow has stable test population
- Trend charts show real performance (not test count artifacts)
- Apples-to-apples comparison across 100+ runs

---

# 11. Recommended Pytest Flags

### Smoke Tests
```bash
pytest \
  -m "smoke" \
  -ra \
  --durations=10 \
  --maxfail=3 \
  --clean-alluredir \
  --alluredir=reports/allure-results
```

- `-ra` — Show all summary (passed, failed, skipped, xfailed)
- `--durations=10` — Show 10 slowest tests
- `--maxfail=3` — Stop after 3 failures (prevent cascade)
- `--clean-alluredir` — Clear previous Allure results
- `--alluredir` — Generate fresh Allure data

### Regression Tests
```bash
pytest \
  -m "regression" \
  -ra \
  --durations=20 \
  --clean-alluredir \
  --alluredir=reports/allure-results
```

- `--durations=20` — Show 20 slowest tests (more detail for heavy suite)
- No `--maxfail` — Run all tests (comprehensive)

### Performance Tests
```bash
pytest \
  -m "performance" \
  -ra \
  --durations=20 \
  --clean-alluredir \
  --alluredir=reports/allure-results
```

- `PERF_ITERATIONS=5` — Run each test 5x for statistical confidence
- `--durations=20` — Identify slowest tests

### Contract Tests
```bash
pytest \
  -m "contract" \
  -ra \
  --alluredir=reports/allure-results
```

Contract tests cover both REST and GraphQL API contracts while remaining part of the same shared `contract.yml` workflow.

- `--maxfail=1` — Stop at the first contract failure (diagnostic-focused)

---

# 12. Recommended CI Triggers

| Workflow | Trigger | Reason |
|----------|---------|--------|
| **preflight** | `pull_request:` | Fast PR feedback (1–3 min) |
| **smoke** | `push: [main]` | Deployment gate; powers badge |
| **contract** | `push: [main]` + `workflow_dispatch:` | Catch schema changes; on-demand debug |
| **regression** | `schedule:` (nightly) + `workflow_dispatch:` | Full coverage; historical trends |
| **performance** | `schedule:` (weekly) + `workflow_dispatch:` | SLA tracking; trend analysis |
| **security** | `schedule:` (weekly) + `workflow_dispatch:` | Regular audit; on-demand validation |

---

# 13. Why Tests Failed: Correct Failure Flow

### ❌ WRONG: Using `continue-on-error: true`

```yaml
- name: Run tests
  run: pytest ...
  continue-on-error: true  # ← WRONG! Forces job to pass

- name: Upload artifacts
  uses: actions/upload-artifact@v4
```

**Result:**
- ✅ Job shows success (badge turns green)
- ❌ Tests actually failed (but hidden!)
- ❌ No one realizes framework is broken
- ❌ Artifacts uploaded, but workflow appears successful

---

### ✅ CORRECT: Proper failure handling

```yaml
- name: Run tests
  run: pytest ...
  # NO continue-on-error!

- name: Upload artifacts
  if: always()  # ← Run even on failure
  uses: actions/upload-artifact@v4

- name: Generate report
  if: always()  # ← Run even on failure
  run: allure generate ...
```

**Result:**
- 🔴 Job fails (badge stays red)
- ✅ Tests failed AND artifacts captured
- ✅ Report still generated for analysis
- ✅ Developers see the problem immediately

---

# 14. Correct Failure Flow

When tests fail, the proper sequence is:

```
1️⃣  Test execution fails
    ↓
2️⃣  Diagnostics collected (structured logs, tracebacks)
    ↓
3️⃣  Artifacts uploaded (if: always())
    ↓
4️⃣  Allure report generated (if: always())
    ↓
5️⃣  Report published to GitHub Pages (if: always())
    ↓
6️⃣  Workflow remains FAILED (badge is red)
    ↓
7️⃣  Developer sees red badge, checks report, debugs
```

**Key principle:** Failure visibility > Hidden problems

---

# 15. GitHub Pages Behavior

Your report deployment pattern:

```yaml
- name: Deploy to GitHub Pages
  uses: peaceiris/actions-gh-pages@v4
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    publish_dir: reports/allure-report/${{ inputs.entity }}/${{ inputs.suite_name }}
    publish_branch: gh-pages
    keep_files: true
```

### How It Works

- 📍 Workflow runs on: `main` branch
- 📍 Report published to: `gh-pages` branch
- 📍 Accessible at: `https://username.github.io/repo/[destination_dir]`
- 📝 `keep_files: true` preserves history (allows trend analysis)

### Result


```
main branch:  Your code & workflows
gh-pages/     Generated reports (indexed by destination_dir)
├── customers/
│   ├── smoke/ (latest smoke report)
│   ├── integration/ (latest integration report)
│   ├── regression/ (latest regression report)
│   └── performance/  (latest performance report)
│
├── orders/
├── products/
└── coupons/
```

### Note:

> Because GitHub Pages accepts only one deployment at a time,
> concurrent workflow executions may occasionally result in one
> deployment being cancelled. The generated reports and artifacts
> remain available in GitHub Actions. Running the affected
> workflow again republishes the report successfully.

---

# 16. Suggested Repository Structure

```text
.github/workflows/
├── preflight.yml        # PR — framework validation
├── smoke.yml            # PR + main — critical business paths
├── contract.yml         # PR + main — API contract validation
├── integration.yml      # PR + main — API + DB validation
├── regression.yml       # Nightly — full functional suite
├── performance.yml      # Weekly — latency & SLA trends
└── security.yml         # Weekly — security validation

docs/
└── portal/
    └── style.css

.github/
└── scripts/
    ├── generate_matrix.py
    └── generate_portal.py

site/                # Generated during deployment
├── index.html
├── style.css
├── customers/
├── products/
└── ...

```

---

# 17. Dashboard Recommendation

### Public Dashboards

Public reports are organized by **entity** and **test suite**.

Current public structure:

```
customers/
├── smoke/
├── integration/
├── regression/
└── performance/
```

As additional entities are implemented, the same structure will be extended to:

```
orders/
products/
coupons/
```

The README links directly to the public dashboards, while GitHub Actions badges provide the latest workflow status.

---

# 18. Common Questions & Answers

### Q: Should I run smoke on every PR?
**A:** Depends on team size & feedback speed goals.
- **Option 1** (fast feedback): smoke on push to main only, preflight on PR
- **Option 2** (catch early): smoke on both PR + push (slower PR feedback)
- **Recommendation for your project:** smoke on push to main only (faster PR flow)

### Q: Why is my trend chart empty?
**A:** History wasn't restored before report generation.
```yaml
- name: Restore history
  run: |
    cp -r gh-pages/history/. reports/allure-results/history/
```

### Q: Can I run regression manually?
**A:** Yes! Use `workflow_dispatch:` trigger.
```yaml
on:
  schedule: "0 2 * * *"
  workflow_dispatch:  # ← Enables manual trigger
```

### Q: How long should I keep history?
**A:** GitHub Pages has no storage limit for gh-pages branch. Keep indefinitely for trend analysis.

### Q: What if contract tests fail?
**A:** Check artifacts in GitHub Actions. Contract failures are diagnostic, not deployment-blocking (by design).

### Q: Should performance tests run nightly?
**A:** Recommend weekly (Sunday) to balance cost vs. trend data. Nightly if budget allows.

---

# 19. Framework Maturity

The framework is implementing best practice concepts:

✅ Full API + DB integration dashboards\
✅ Multi-dashboard GitHub Pages publishing\
✅ Segmented workflow ownership

✅ **Architecture**
- Layered test structure (API, DAO, validators)
- Segmented CI pipelines (intent-based)
- Structured observability (JSONL logs)

✅ **Observability**
- Deterministic session metadata
- Git/CI metadata injection
- Allure environment enrichment
- History preservation (trends)

✅ **Operations**
- Dockerized CI environment (reproducibility)
- API contract validation (REST + GraphQL schema checking)
- Performance telemetry (latency tracking)
- Security audit trails

✅ **Reporting**
- Multi-workflow Allure dashboards
- GitHub Pages automation
- Trend analysis & flaky detection
- Ownership-aware reporting

**Note:** Your custom Allure integration demonstrates many practices commonly found in mature CI/CD environments,
including reusable workflows, structured reporting, history preservation and metadata-driven execution.

The framework adopts many CI/CD practices, including reusable workflows, framework - driven entity registry,
metadata-driven execution, structured reporting and GitHub Pages publication for public reports.

---


4. **Monitor first runs:**
   - Check workflow execution times
   - Verify artifact generation
   - Validate GitHub Pages deployment
   - Review Allure dashboard

---

# 20. Troubleshooting Guide

### Workflows not triggering?
- ❌ Check YAML syntax (use GitHub Actions linter)
- ❌ Verify workflow is in `.github/workflows/` directory
- ❌ Confirm branch matches trigger (`push: [main]`)

### Allure report not generating?
- ❌ Verify `--alluredir=reports/allure-results` flag in pytest
- ❌ Check Java installation step completed
- ❌ Verify Allure CLI download succeeded

### GitHub Pages not updating?
- ❌ Enable Pages in repo settings (Settings → Pages)
- ❌ Verify `gh-pages` branch exists
- ❌ Check `keep_files: true` in deployment step
- ❌ Allow 1–2 min for Pages build

### History not showing in trends?
- ❌ Verify history restoration step runs (check logs)
- ❌ Confirm previous run successfully published to `gh-pages`
- ❌ Check that `gh-pages` branch has `history/` directory

### Tests running but not being detected?
- ❌ Verify test file names start with `test_`
- ❌ Verify pytest markers: `@pytest.mark.smoke`, etc.
- ❌ Run `pytest --collect-only -m "smoke"` locally to debug

---

## ⚠️ Note:
### Never use in CI:

```
latest
latest-stable
nightly
edge
```

Because:

* CI becomes nondeterministic
* builds randomly break
* historical runs become unreproducible

---

**Last updated:** 2026-08-15
**Guide version:** 1.4 (CI/CD & Allure best practices)
