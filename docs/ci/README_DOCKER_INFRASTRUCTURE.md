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
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
  ensure-env              docker compose up
(create .env if needed)        │
        │                      ▼
        │              WordPress + MySQL
        │                      │
        └──────────────┬───────┘
                       ▼
                scripts/setup.sh
                       │
        ┌──────────────┼─────────────────┐
        │              │                 │
        ▼              ▼                 ▼
 Install WP     Install WooCommerce   Generate API Keys
                       │
                       ▼
      write_env_credentials.sh
                       │
      updates only WC_KEY / WC_SECRET
                       │
                       ▼
          pip install -e "./EcommerceAPI[dev]"
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
| `wordpress` | WordPress + WooCommerce application server, exposed on http://localhost:8080 |
| `wpcli`  | WP-CLI — runs one-off commands (install WP, install/activate WooCommerce, generate API keys) |

This is orchestrated by `docker-compose.wp.yml` at the repo root, and bootstrapped by `scripts/setup.sh`.

### 🌐 GraphQL uses the same Docker environment

GraphQL does not introduce a separate container, database, or Docker network.

The GraphQL endpoint is served by the existing WordPress application:

```text
WordPress container
       │
       ├── WooCommerce REST API
       │
       └── WPGraphQL
             ↓
          /graphql
```

Authenticated GraphQL mutations use the WordPress Application Password
provisioned during bootstrap. The Docker infrastructure is therefore shared
by both REST and GraphQL tests.

---
## 🐳 Why Docker?

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
write_env_credentials.sh → merges generated REST and GraphQL credentials into `.env`

Makefile                 → orchestrates the whole flow behind `make run`
.env.example             → template for required environment variables
.dockerignore            → excludes files from the build context when
                            the Dockerfile image is built
```

**Correction vs. earlier notes:** this project *does* ship a `Dockerfile` and a `.dockerignore`. They aren't used to build WordPress or MySQL (those come from official prebuilt images), but they matter when you run tests in containerized mode (`API_ENV=docker`) or in CI, where the test runner itself is built as an image.

---

## 3. </> One-command bootstrap

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

### ⚠️ Running multiple local environments

`make run` is idempotent when used with the same project environment.
You do **not** need to run `make down` before every `make run`.

However, this project uses fixed host ports for its Docker services
(WordPress: `8080`, MySQL: `3306`). Therefore, two separate
TestEcommerceAPI environments cannot normally run simultaneously on the
same machine.

For example, if you have both a development checkout and a separate
public/clean checkout using the same Docker Compose configuration, make
sure only one environment is running at a time:

```bash
make down
```

Then, from the environment you want to use:

```bash
make run
```

This avoids port conflicts and prevents commands from one repository
from accidentally interacting with containers belonging to another
checkout.

> ⚠️ Important: `make down` is a precaution when switching between
separate local environments. It is not required before every
make run.


---

## 3.5 🔑 Bootstrap responsibilities

The local bootstrap process intentionally separates responsibilities across multiple components.

| Component | Responsibility |
|-----------|----------------|
| Makefile | Orchestrates the complete local workflow. |
| docker-compose.wp.yml | Starts the Docker infrastructure. |
| setup.sh | Installs and configures WordPress and WooCommerce. |
| write_env_credentials.sh | Updates the generated REST and GraphQL authentication credentials inside `.env`. |
| EcommerceAPI | Executes the test suite. |

Following the Single Responsibility Principle (SRP), each component owns one specific task. This keeps the bootstrap
process reusable, easier to maintain, and allows the same `setup.sh` script to be used unchanged by both local development and GitHub Actions.

---

## 4. 💫 What happens step by step

### Step 1 — Docker boots the empty environment
```bash
docker compose -f docker-compose.wp.yml up -d
```
Creates the `db`, `wordpress`, and `wpcli` containers. At this point:
- ❌ WordPress is not installed yet
- ❌ WooCommerce is not installed
- ❌ No API keys exist

### Step 2 — `scripts/setup.sh` provisions WooCommerce

The setup script is intentionally idempotent and can safely be executed multiple times.

During the bootstrap it:

1. Waits for the infrastructure to become healthy.
2. Installs WordPress (if needed).
3. Installs WooCommerce (if needed).
4. Configures permalinks.
5. Waits for the REST API to become available.
6. Generates fresh WooCommerce REST API credentials.
7. Provisions the WordPress Application Password used by authenticated GraphQL operations.
8. Emits the generated credentials to stdout in a machine-readable format.
9. Delegates `.env` updates to `write_env_credentials.sh`.

This step is **idempotent** — rerunning `make run` skips anything already installed instead of failing or duplicating data.

### Step 3 — Framework installs and tests run
```bash
python -m pip install -e "./EcommerceAPI[dev]"
pytest
```
The framework talks to:
- **REST API** → `http://localhost:8080/wp-json/wc/v3/`
- **GraphQL API** → `http://localhost:8080/graphql`
- **DB** → the `db` MySQL container, for direct state validation

REST and GraphQL use the same WordPress/WooCommerce container; GraphQL does
not require a separate Docker service or network.

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

## 11. 🛠️ Troubleshooting

| Symptom | Possible cause | Solution |
|---------|----------------|----------|
| 401 Unauthorized | Stale WooCommerce credentials | Re-run `make run` to regenerate credentials. |
| Tests target the wrong URL | `WC_API_URL` exists in `.env` | Remove `WC_API_URL`. The framework resolves URLs from `API_ENV`. |
| WordPress installation missing | Bootstrap interrupted | Run `make setup`. |
| WordPress files missing | `wp-data` bind mount missing | Create `wp-data/` and rerun `make run`. |
| Git Bash converts `/var/www/html` into `C:\Program Files\Git\...` | MSYS path conversion | Use `MSYS_NO_PATHCONV=1`. |

## 🔗 Related Documentation

- README_QA_DEVELOPER_ONBOARDING.md
- README_ARCHITECTURE.md
- README_ENVIRONMENT_CONFIG_GUIDE.md
- README_CI_ARCHITECTURE.md
- README_ALLURE.md
- docs/development/README_GRAPHQL_TESTING_GUIDE.md


---

## ⚠️ API Endpoint Resolution

The bootstrap process generates only authentication credentials.

It intentionally does **not** generate or overwrite `WC_API_URL`.

The framework resolves API endpoints from the selected execution
environment (`API_ENV`) using dedicated configuration.

REST entity APIs use the entity configuration files.

GraphQL uses dedicated GraphQL configuration:

```text
API_ENV
   ↓
config_graphql.py
   ↓
graphql_client fixture
   ↓
GraphQLClient
```

For example:

- API_ENV=test
- API_ENV=ci
- API_ENV=docker

all resolve their endpoints through the framework configuration.

GraphQL endpoint configuration is infrastructure configuration and must not
be hardcoded in individual GraphQL tests.

This prevents stale `.env` values from overriding the intended execution environment.

---

## 🎯 Design Principles

The Docker infrastructure follows several design principles.

- Infrastructure is disposable.
- Local development mirrors CI.
- Bootstrap is idempotent.
- Credentials are generated automatically.
- Environment selection belongs to the framework, not `.env`.
- REST and GraphQL share the same Docker infrastructure.
- Components follow the Single Responsibility Principle.
- Developers should only need one command (`make run`) to obtain a fully working test environment.
