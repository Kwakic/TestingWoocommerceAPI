# 📚 CI/CD & Allure Reporting Guide for TestEcommerceAPI

Your framework has evolved beyond a "simple pytest project." You now have:

- ✅ Layered enterprise API testing
- ✅ Segmented CI/CD pipelines
- ✅ Dockerized test environments
- ✅ Structured logging
- ✅ Allure reporting with history tracking
- ✅ GitHub Pages publishing
- ✅ Performance & contract testing
- ✅ Smoke validation & security testing
- ✅ Trend/history preservation

Your custom Allure integration implements many advanced enterprise reporting concepts.

---

# 🎯 1. CI/CD Philosophy

Your pipelines should answer **one specific question each**:

| Workflow | Question | Purpose |
|----------|----------|---------|
| **preflight.yml** | Can the framework start safely? | Ultra-fast validation; fast feedback |
| **smoke.yml** | Are critical business flows healthy? | Deployment gate; powers badge |
| **contract.yml** | Did the API contract/schema change? | Schema validation; diagnostics |
| **integration.yml** | Does API state match DB state? | End-to-end integration validation |
| **regression.yml** | Did we break anything? | Full coverage; trends & history |
| **performance.yml** | Is the system getting slower? | Latency tracking; SLA validation |
| **security.yml** | Are auth/permission rules still safe? | Auth boundaries; internal audit |

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

---

## 2.1 preflight.yml ⚡

### Purpose
Ultra-fast validation before expensive infrastructure tests.

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
- **Badge:** Shows last smoke run status

### Why This Configuration?
- **PR-only trigger** ensures developers get instant feedback
- **No Docker** means no infrastructure spin-up delays
- **No Allure** keeps dashboard clean (preflight is developer-focused, not operational)
- **`--maxfail=1`** stops immediately on first failure (fail-fast)

---

## 2.2 smoke.yml 🔥

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
  push:
    branches: [ main ]    # Every merge to main
  workflow_dispatch:      # Manual
```

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
- **Dashboard location:** `https://username.github.io/repo/`
- **History:** Tracks run-to-run pass/fail trends
- **Badge:** Shows last smoke run status

### Why This Configuration?
- **Push to main only** ensures stable test population for trends
- **Allure + Pages** provides operational visibility & confidence signal
- **Maxfail=3** prevents cascading failures (stops after 3rd failure)
- **Structured logs** enable deep diagnostics on failures

---

## 2.3 integration.yml 🔗

### Purpose

Validate full API + database integration behavior across services.

This suite verifies that:

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
  push:
    branches: [ main ]
  workflow_dispatch:
```

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

* **Dashboard location:** `https://username.github.io/repo/integration`
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
Validate API contracts and response schemas before regression runs.

### What It Tests
- JSON schema validation
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
  push:
    branches: [ main ]    # Every push to main
  workflow_dispatch:      # Manual (on-demand debugging)
```

### Allure Report?
⚠️ **Optional** — Captured as artifact for diagnostics

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
- **Push trigger** catches schema changes early
- **No public Allure** keeps dashboard focused on operational metrics
- **Artifacts only** allow developers to debug contract failures
- **Structured logs** provide detailed request/response data

---

## 2.5 regression.yml 🔬

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
- **Dashboard location:** `https://username.github.io/repo/regression`
- **History:** Full trend analysis enabled
- **Separate from smoke** to maintain distinct trend graphs
- **Badge:** Shows last smoke run status


### Why This Configuration?
- **Nightly schedule** keeps costs low while maintaining coverage
- **Separate destination_dir** prevents smoke/regression trends from mixing
- **Long timeout acceptable** (no developer waiting)
- **Allure + history** enables performance trending & flaky test detection

---

## 2.6 performance.yml ⏱️

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
- **Dashboard location:** `https://username.github.io/repo/performance`
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
- **Dashboard location:** `https://username.github.io/repo/`
- **History:** Tracks run-to-run pass/fail trends
- **Badge:** Shows last smoke run status

### Why This Configuration?
- **No public dashboard** prevents exposure of security test details
- **Artifacts only** allows team to audit without external visibility
- **Structured logs** provide evidence trail for security reviews
- **Sunday schedule** aligns with regression (other nightly tests)

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

- `--maxfail=1` — Stop at first schema failure (diagnostic-focused)

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

# 14. Correct Enterprise Failure Flow

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
    publish_dir: reports/allure-report
    publish_branch: gh-pages
    keep_files: true
    destination_dir: smoke  # or "regression", "performance"
```

### How It Works

- 📍 Workflow runs on: `main` branch
- 📍 Report published to: `gh-pages` branch
- 📍 Accessible at: `https://username.github.io/repo/[destination_dir]`
- 📝 `keep_files: true` preserves history (allows trend analysis)

### Result

```
main branch:  Your code & workflows
gh-pages:     Generated reports (indexed by destination_dir)
              ├── /smoke           (latest smoke report)
              ├── /regression      (latest regression report)
              ├── /performance     (latest performance report)
              └── /history         (all historical data)
```

---

# 16. Suggested Repository Structure

```text
.github/workflows/
├── preflight.yml        # PR validation (1–3 min)
├── smoke.yml            # Business path (3–10 min)
├── contract.yml         # Schema validation (5–15 min)
├── regression.yml       # Full suite (nightly, long)
├── integration.yml      # API+DB validation
├── performance.yml      # Latency tracking (weekly)
└── security.yml         # Auth validation (weekly)

docs/
├── README_CI_ALLURE_GUIDE.md  # This guide
├── ENVIRONMENT_CONFIG_GUIDE.md
├── CONFIG_CONTRACT.md
└── CI_TROUBLESHOOTING.md

reports/
├── allure-results/      # Generated by pytest
├── allure-report/       # Generated by allure CLI
└── logs/                # Structured JSONL logs
```

---

# 17. Dashboard Recommendation

### Public Dashboards (README Badge)

Use for **external visibility** & **stakeholder confidence:**

```markdown
[![Smoke Tests](https://github.com/user/repo/actions/workflows/smoke.yml/badge.svg?branch=main)](https://user.github.io/repo/)
```

- **Smoke report** — Powers "passing" status
- **Regression report** — Powers historical trends

### Internal Dashboards (Team Tools)

Use for **engineering diagnostics:**

- **Contract tests** — Artifacts only (on-demand debugging)
- **Performance tests** — Separate dashboard (SLA tracking)
- **Security tests** — Artifacts only (audit trail)

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

# 19. Your Framework Maturity

Your framework is implementing enterprise-grade concepts:

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
- API contract validation (schema checking)
- Performance telemetry (latency tracking)
- Security audit trails

✅ **Reporting**
- Multi-workflow Allure dashboards
- GitHub Pages automation
- Trend analysis & flaky detection
- Ownership-aware reporting

**Note:** Your custom Allure integration is significantly more advanced than what many teams maintain internally. This is enterprise-grade infrastructure.

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

**Last updated:** 2026-05-08
**Guide version:** 1.2 (Enterprise-grade CI/CD & Allure best practices)
