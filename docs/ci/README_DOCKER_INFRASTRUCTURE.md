# 🐳 Docker Infrastructure — TestingWoocommerceAPI

This document describes the Docker layer of the [TestingWoocommerceAPI](https://github.com/Kwakic/TestingWoocommerceAPI) framework: what it spins up, how it's orchestrated, and the commands you'll actually use day to day.

> Framework docs live in `docs/` (CI/Allure guide, environment config guide). This file covers **infra only** — Docker, Compose, and the bootstrap process.

---

## 🏛️ Architecture Diagram
```
Developer
      │
      ▼
make run
      │
      ▼
ensure-env
      │
      ▼
Docker Compose
      │
      ▼
setup.sh
      │
      ▼
write_env_credentials.sh
      │
      ▼
pytest
```

The same infrastructure is used locally and in GitHub Actions.

Running tests against the same Dockerized services
helps ensure consistency between local development
and CI execution.

---

## 1. What this infra provides

The stack gives you a disposable, reproducible WooCommerce instance to run API + DB tests against:

| Service  | Role                                    |
|----------|------------------------------------------|
| `db`     | MySQL — backing database for WordPress   |
| `wordpress` | WordPress + WooCommerce application server, exposed on `http://localhost:8888` |
| `wpcli`  | WP-CLI — runs one-off commands (install WP, install/activate WooCommerce, generate API keys) |

This is orchestrated by `docker-compose.wp.yml` at the repo root, and bootstrapped by `scripts/setup.sh`.

---
## Why Docker?

The framework intentionally runs against a real
WooCommerce installation rather than mocked services.

Benefits:

*  reproducible environments
*  isolated test execution
*  realistic API behaviour
*  database validation
*  identical CI execution

---

## 2. Files involved

```
docker-compose.wp.yml    → defines db / wordpress / wpcli services
Dockerfile               → builds a container image for running the test
                            suite itself (used for API_ENV=docker and in CI),
                            NOT for building WordPress/MySQL — those are
                            pulled as prebuilt images
scripts/setup.sh         → waits for containers, fixes permissions,
                            installs WordPress + WooCommerce, generates
                            API keys, generates WooCommerce credentials.
write_env_credentials.sh → merges credentials into .env

Makefile                 → orchestrates the whole flow behind `make run`
.env.example             → template for required environment variables
.dockerignore            → excludes files from the build context when
                            the Dockerfile image is built
```

**Correction vs. earlier notes:** this project *does* ship a `Dockerfile` and a `.dockerignore`. They aren't used to build WordPress or MySQL (those come from official prebuilt images), but they matter when you run tests in containerized mode (`API_ENV=docker`) or in CI, where the test runner itself is built as an image.

---

## 3. One-command bootstrap

```bash
git clone https://github.com/Kwakic/TestingWoocommerceAPI.git
cd TestingWoocommerceAPI
make run
```

`make run` chains together:

```
Makefile → docker compose up -d → scripts/setup.sh → pip install -e ./EcommerceAPI[dev] → pytest
```

Nothing needs to be run manually — no separate `docker compose up`, no manual WordPress install screen, no manually generated API keys.

`make run` orchestrates the complete local setup, including infrastructure startup, environment bootstrap, framework installation and test execution.

---

## 4. What happens step by step

### Step 1 — Docker boots the empty environment
```bash
docker compose -f docker-compose.wp.yml up -d
```
Creates the `db`, `wordpress`, and `wpcli` containers. At this point:
- ❌ WordPress is not installed yet
- ❌ WooCommerce is not installed
- ❌ No API keys exist

### Step 2 — `scripts/setup.sh` configures the system
Run automatically by `make run` (or manually, see below). It:
1. Waits for `db` and `wordpress` to be reachable
2. Fixes file permissions where needed
3. Runs `wp core install` (WordPress)
4. Runs `wp plugin install woocommerce --activate`
5. Generates a `consumer_key` / `consumer_secret` pair via WP-CLI
6. Writes/updates `.env` with the values the test framework needs

This step is **idempotent** — rerunning `make run` skips anything already installed instead of failing or duplicating data.

### Step 3 — Framework installs and tests run
```bash
python -m pip install -e "./EcommerceAPI[dev]"
pytest
```
The framework talks to:
- **API** → `http://localhost:8888/wp-json/wc/v3/`
- **DB** → the `db` MySQL container, for direct state validation

---

## 5. Common Docker commands

| Purpose | Command |
|---|---|
| Start the stack | `docker compose -f docker-compose.wp.yml up -d` |
| Stop and remove containers + volumes | `docker compose -f docker-compose.wp.yml down -v` |
| List running containers | `docker ps` |
| List all containers (incl. stopped) | `docker ps -a` |
| Show only container IDs (scripting) | `docker ps -q` |
| Show container disk usage | `docker ps -s` |
| Show most recently created container | `docker ps -l` |
| Full, untruncated output | `docker ps --no-trunc` |
| Custom column output | `docker ps --format "{{.Names}}"` |
| Filter by status | `docker ps -f "status=exited"` |

**Output columns** (`docker ps`): `CONTAINER ID`, `IMAGE`, `COMMAND`, `STATUS` (Up / Exited / Paused), `NAMES`.

---

## 6. Clean reset

To fully tear down and start fresh:

```bash
docker compose -f docker-compose.wp.yml down -v
```

This removes the containers **and** the named volumes (DB data, WordPress files), so the next `make run` performs a completely clean install.

> ⚠️ Only delete local working files (e.g. a stray `wp-data/` directory or the `woocommerce/` plugin folder) if you've created them yourself outside of Docker's managed volumes. Docker Compose volumes are already handled by `down -v` — don't `rm -rf` paths you're not sure about.

---

## 7. Do you need to build anything yourself?

| Question | Answer |
|---|---|
| Does `docker compose up` build an image? | No — `db` and `wordpress` use official prebuilt images (`mysql`, `wordpress`) |
| Is the `Dockerfile` required for local test runs? | No — by default, pytest runs on the host against the Dockerized WordPress instance (`API_ENV=test`) |
| When *is* the `Dockerfile` used? | When running tests inside a container (`API_ENV=docker`) or in CI pipelines that containerize the test runner |
| Do I need `.dockerignore` for local test runs? | No — only relevant when the `Dockerfile` image is actually built |

---

## 8. Core Docker concepts (quick reference)

- **Image** — a blueprint (e.g. `mysql:8`, `wordpress:latest`)
- **Container** — a running instance of an image
- **Dockerfile** — instructions for building a custom image (used here for the test-runner image, not for WordPress/MySQL)
- **docker-compose** — orchestrates multiple containers as one stack

---

## 9. Framework vs Infrastructure (Mental model)

```
Framework (EcommerceAPI)  → HOW tests run
Docker + WordPress         → WHERE tests run
setup.sh                   → turns an empty Docker environment into a
                              usable WooCommerce instance
Makefile                   → single entrypoint tying it all together
```

---

## 10. Requirements

- Docker
- Docker Compose
- Python 3.13+
- Make (or Git Bash on Windows)

---

## 11. Troubleshooting

| Symptom | Likely cause |
|---|---|
| Tests fail with `401` / `403` | `setup.sh` didn't complete — WooCommerce API keys weren't generated. Re-run `make run`. |
| `docker compose up` hangs | A previous stack is still holding the ports/volumes. Run `down -v` first. |
| WordPress reachable but empty (no WooCommerce) | `setup.sh` was skipped or failed partway — check its logs, rerun it manually: `make setup` |
| Stale data after schema changes | Run `docker compose -f docker-compose.wp.yml down -v` for a full reset before `make run` |


## Related Documentation

- README_QA_DEVELOPER_ONBOARDING.md
- README_ARCHITECTURE.md
- README_ENVIRONMENT_CONFIG_GUIDE.md
- README_CI_ARCHITECTURE.md
- README_ALLURE.md
