# Environment & Configuration Guide 🧭

A concise, practical guide to environment variables and configuration for TestEcommerceAPI.  
Covers local dev, CI, Docker, common env keys, examples, and troubleshooting tips. Good for developers, QA and cross-team readers.

---

## Quick principles (short)
- Keep secrets out of the repo — store them in CI secret stores.  
- Use a tracked `.env.example` that contains keys but no real secrets.  
- Use typed helpers (the framework uses `env_bool()` etc.) — set values as strings: `"1"`, `"true"`, `"yes"` (case-insensitive) for true.  
- Prefer editable install for local dev: `pip install -e './EcommerceAPI[dev]'`. This ensures the framework reads config in the same way as CI.

---

## Where config is resolved
- The canonical config loader is `EcommerceAPI.plugins._config`:
  - Use `get_config()` to read resolved typed settings.
  - Tests and plugins should use the `framework_config` fixture rather than calling `os.getenv()` directly.

- The `env_bool()` utility normalizes boolean strings into Python bools.

- Runtime session id: `SESSION_ID` is generated (or read from env) and used in logging/metadata.

---

## Important environment variables (common)

- CORE
  - `ENV` — environment name (e.g., `test`, `dev`, `staging`, `prod`). Default: `test`.
  - `SESSION_ID` — optional fixed session id for reproducible runs. If unset, a short random id is generated.

- TEST RUNNING / BEHAVIOR
  - `FAIL_ON_EMPTY_LIST` — when `true`, preflight schema tests fail if list endpoints return empty lists. Default: `false`.
  - `PERF_ITERATIONS` — integer, number of iterations for perf tests (default `5`).
  - `REQUIRE_ENV` — when `true`, fail early if required configuration is missing. Recommended: `false` locally, `true` in CI.

- REPORTING & ALLURE
  - `AUTO_ALLURE_REPORT` — `true` to auto-generate Allure HTML when `allure` CLI is present. Default: `true`.
  - `ALLURE_VER` — version used when you script Allure install (example `2.27.0`).

- LOGGING & STRUCTURED LOGS
  - `ENABLE_STRUCTURED_LOGS` — enable structured JSONL logs (per-team). Default: `true` in framework config but can be controlled at runtime.
  - `ENABLE_JSON_PRETTY` — pretty-print JSON logs (`true`/`false`).
  - `LOG_PAYLOADS` — include request/response payloads in structured logs (careful with secrets). Default: `false`.
  - `REDACT_SENSITIVE_FIELDS` — redact sensitive keys in logs. Default: `true`.
  - `DISABLE_LOG_EMOJIS` — disable emojis in console logs (useful in some CI outputs).
  - `LOG_DIR` — base dir for structured logs. Default: `reports/logs` or repo-root-level `reports` subfolders.
  - `KEEP_STRUCTURED_LOGS` — retention integer (how many JSONL files to keep per team/env).

- DEBUG / WARNINGS
  - `PYTHONWARNINGS` — controls Python warning handling (e.g., `error`, `default`, `ignore`). Useful to convert warnings into errors during debugging: `PYTHONWARNINGS=error`.
  - `ENABLE_JSON_PRETTY` — pretty JSON for local debugging.

---

## .env example (recommended)
Keep a tracked `.env.example` with no secrets:

```text
# .env.example (do NOT commit real secrets)
ENV=test
SESSION_ID=
FAIL_ON_EMPTY_LIST=false
PERF_ITERATIONS=5
REQUIRE_ENV=false

AUTO_ALLURE_REPORT=true
ENABLE_STRUCTURED_LOGS=true
ENABLE_JSON_PRETTY=true
LOG_PAYLOADS=false
REDACT_SENSITIVE_FIELDS=true
DISABLE_LOG_EMOJIS=false
LOG_DIR=reports/logs
KEEP_STRUCTURED_LOGS=3

# Example API credentials (leave blank in example)
WC_KEY=
WC_SECRET=
CUSTOMERS_BASE_URL=https://api.staging/customers
ORDERS_BASE_URL=https://api.staging/orders
```

Copy example to create local `.env`:
- macOS / Linux / Git Bash:
  ```bash
  cp .env.example .env
  ```
- Windows PowerShell:
  ```powershell
  Copy-Item .env.example .env
  ```

Fill `.env` with appropriate values. Never commit `.env`.

---

## How to set env vars (CLI / PowerShell examples)

- Inline for one command (Linux/macOS):
  ```bash
  ENV=test FAIL_ON_EMPTY_LIST=true pytest -m preflight -q
  ```

- PowerShell:
  ```powershell
  $env:FAIL_ON_EMPTY_LIST = "true"
  pytest -m preflight -q
  # then unset:
  Remove-Item Env:\FAIL_ON_EMPTY_LIST
  ```

- Temporarily treat warnings as errors (useful to find warnings source):
  ```powershell
  $env:PYTHONWARNINGS = 'error'
  pytest -q
  Remove-Item Env:\PYTHONWARNINGS
  ```

---

## CI examples

- GitHub Actions (env snippet):
```yaml
env:
  PYTHON_VERSION: "3.11"
  REQUIRE_ENV: "true"
  AUTO_ALLURE_REPORT: "true"
  ENABLE_STRUCTURED_LOGS: "true"
  ENABLE_JSON_PRETTY: "true"
  LOG_DIR: "${{ github.workspace }}/reports/logs"
  KEEP_STRUCTURED_LOGS: "3"
# Secrets (example)
# - name: WC_KEY, value: ${{ secrets.WC_KEY }}
```

- GitLab CI (variables block):
```yaml
variables:
  REQUIRE_ENV: "true"
  AUTO_ALLURE_REPORT: "true"
  ENABLE_STRUCTURED_LOGS: "true"
  LOG_DIR: "$CI_PROJECT_DIR/reports/logs"
  KEEP_STRUCTURED_LOGS: "3"
```

CI tips:
- Store API keys/secrets using the provider’s secret store (GitHub Secrets, GitLab CI variables).
- Install Allure CLI in the job at runtime if you plan to generate HTML (`AUTO_ALLURE_REPORT=true`).

---

## Docker notes

- The runtime test image intentionally does not include Allure CLI — CI will install it at job runtime when needed.
- When running containers locally mount `./reports` so host can access results:
  - Example (docker-compose.matrix.yml): `- ./reports:/app/reports`
- Ensure `LOG_DIR` is writable by the container user or create it on the host before running.

---

## Runtime overrides & pytest integration

- The root `pyproject.toml` sets default pytest `addopts`. If you set `--disable-warnings` there, you will not see warnings unless you override addopts at run time:
  ```bash
  # Override configured addopts for one run
  pytest -m tcid333 -o addopts="" -r w
  ```

- `framework_config` pytest fixture reflects CLI option precedence:
  - Passing `--fail-on-empty-list` will set the `FAIL_ON_EMPTY_LIST` behavior for that run.

- Programmatic access (quick inspect):
  ```bash
  python -c "from EcommerceAPI.plugins._config import get_config; print(get_config())"
  ```
  Or, inside a Python session:
  ```python
  from EcommerceAPI.plugins._config import get_config
  cfg = get_config(reload=True)   # reload reads current env
  print(cfg.FAIL_ON_EMPTY_LIST, cfg.LOG_DIR)
  ```

---

## How to change config for one run (examples)

- Make preflight fail on empty lists:
  ```bash
  FAIL_ON_EMPTY_LIST=true pytest -m preflight -q
  ```

- Generate Allure HTML locally (requires Allure CLI):
  ```bash
  AUTO_ALLURE_REPORT=true pytest tests/customers --alluredir=reports/customers/allure-results
  allure generate reports/customers/allure-results -o reports/customers/allure-report --clean
  ```

- Enable structured logs for a single run:
  ```bash
  ENABLE_STRUCTURED_LOGS=true ENABLE_JSON_PRETTY=true pytest -q
  ```

---

## Debugging & troubleshooting

- “Nothing happened / setting ignored”:
  - Confirm `.env` was loaded (plugins locate `.env` by walking up from pytest root).
  - Run with `-o addopts=""` to avoid hidden flags in `pyproject.toml`.

- “Why am I not seeing warnings?”  
  - Check `pyproject.toml` `addopts` for `--disable-warnings`. Override with `-o addopts=""`.

- View resolved config at test start:
  - The framework emits a startup banner (search `FRAMEWORK CONFIG` in pytest live logs) showing values used for that run.

- If structured logs not produced:
  - Check `ENABLE_STRUCTURED_LOGS`, `LOG_DIR` and file write permissions.
  - Look for `LAST_STRUCTURED_LOG` in `custom_logger` if set.

- If an env change in your shell is not reflected in pytest:
  - Use `get_config(reload=True)` in a small Python snippet or restart your shell virtual environment to ensure env vars are present.

---

## Security & best practices

- Never store secrets in `.env` in the repo. Use `.env.example` with placeholders.
- Keep `REDACT_SENSITIVE_FIELDS=true` by default to avoid leaking secrets into logs.
- Limit `LOG_PAYLOADS=true` to troubleshooting sessions only. Prefer structured logs with redaction.
- Review `KEEP_STRUCTURED_LOGS` to avoid disk fill on long CI runs.

---

## Quick checklist for CI readiness
- [ ] Secrets are in CI secret store (do not commit to repo)
- [ ] `REQUIRE_ENV=true` is set in CI so missing config fails early
- [ ] Jobs write `--alluredir=reports/<service>/allure-results`
- [ ] CI installs Allure CLI when `AUTO_ALLURE_REPORT=true`
- [ ] `LOG_DIR` points to a writable directory in the runner
- [ ] `KEEP_STRUCTURED_LOGS` is a small number (e.g., `3`) to limit retention

---

If you want, I can:
- Produce a ready-to-add `.env.example` file with placeholders tailored to your services, or
- Create `scripts/print_config.py` that prints resolved config for debugging, or
- Add a small CI snippet that installs Allure and uploads both results and generated HTML.

Which would you like next? 🎯