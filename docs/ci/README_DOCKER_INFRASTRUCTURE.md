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
           Seed deterministic UI/E2E data
                       │
                       ├── baseline products
                       └── repository-local image fixtures
                       │
                       ▼
                pip install -e "./EcommerceAPI[dev]"
                       │
                       ▼
                Playwright browsers
                       │
                       ▼
                    pytest
```

The same infrastructure is used locally and in GitHub Actions.

Both environments execute the same `scripts/setup.sh` bootstrap, so WooCommerce
checkout configuration and local test-only WordPress policies are applied
consistently in local development and CI.

Running tests against the same Dockerized services
helps ensure consistency between local development
and CI execution.

---

### 🗺️ The big picture

```text
                        TESTINGWOOCOMMERCEAPI
                                  │
              ┌───────────────────┴──────────────────┐
              │                                      │
          API TESTING                             UI TESTING
              │                                      │
       Entity / Shared                        Playwright
              │                                      │
       GitHub matrix                         Browser selection
              │                                      │
              │                         ┌────────────┴────────────┐
              │                         │                         │
              │                       PR                    main/manual
              │                         │                         │
              │                     Chromium              Chromium + Firefox
              │                                             + WebKit
              │
              └──────────────────┬───────────────────────────┘
                                 │
                           reusable-test-runner
                                 │
                         Docker WooCommerce
                                 │
                          Allure / JUnit / Logs

```

---

## 1. What this infra provides

The stack gives you a disposable, reproducible WooCommerce instance to run API + DB tests against:

| Service  | Role                                    |
|----------|------------------------------------------|
| `db`     | MySQL — backing database for WordPress   |
| `wordpress` | WordPress + WooCommerce application server, exposed on http://localhost:8080 |
| `wpcli`  | WP-CLI — runs one-off commands (install WP, install/activate WooCommerce, generate API keys) |

This is orchestrated by `docker-compose.wp.yml` at the repo root, and bootstrapped by `scripts/setup.sh`.

### Test-only WordPress policies

`setup.sh` provisions application settings required by UI tests rather than
making each test change the environment. Alongside checkout configuration, it
creates a must-use plugin in `wp-content/mu-plugins/` that disables WordPress's
15-second comment flood limit only when `WP_ENVIRONMENT_TYPE=local`.

This lets parallel review-submission tests run from the shared localhost source
IP without receiving HTTP 429. The plugin is recreated on each bootstrap and
does not relax comment protection in non-local environments.

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
                            suite itself (used for containerized test
                            execution), NOT for building WordPress/MySQL —
                            those are pulled as prebuilt images
scripts/setup.sh         → waits for containers, fixes permissions,
                            installs WordPress + WooCommerce, generates
                            API keys, generates WooCommerce credentials.
write_env_credentials.sh → merges generated REST and GraphQL credentials into `.env`

Makefile                 → orchestrates the whole flow behind `make run`
.env.example             → template for required environment variables
.dockerignore            → excludes files from the build context when
                            the Dockerfile image is built
```

**Important distinction:** this project *does* ship a `Dockerfile` and a `.dockerignore`. They aren't used to build WordPress or MySQL (those come from official prebuilt images). The Dockerfile is used when you choose containerized test execution (`API_ENV=docker`). The current GitHub Actions workflow runs pytest directly on the GitHub-hosted runner; it does not build the test-runner image. CI could be changed to use that image in the future, but CI execution does not automatically mean containerized test execution.

---

## 3. </> One-command bootstrap

```bash
git clone https://github.com/Kwakic/TestingWoocommerceAPI.git
cd TestingWoocommerceAPI
make run
```

`make run` chains together:


```text
Makefile
   ↓
docker compose up -d
   ↓
scripts/setup.sh
   │
   ├── WordPress + WooCommerce
   ├── Cash on Delivery
   ├── customer registration
   ├── checkout shipping destination
   ├── REST / GraphQL
   └── API credentials
   ↓
write_env_credentials.sh
   ↓
seed_test_products.sh
   ↓
seed_test_users.sh
   ↓
pip install -e "./EcommerceAPI[dev]"
   ↓
Playwright browser installation
   ↓
pre-commit Git hook installation
   ↓
pytest
```

Nothing needs to be run manually — no separate `docker compose up`, no manual WordPress install screen, no manually generated API keys.

`make run` orchestrates the complete local setup, including infrastructure startup,
environment bootstrap, framework installation, Playwright browser installation,
and the repository Git pre-commit hook.

The hook installation is a **local developer setup step**. It does not configure
Git hooks inside GitHub Actions; CI runs its validation directly through the
workflow commands.

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
| Makefile | Orchestrates the complete local workflow and installs the repository Git pre-commit hook. |
| docker-compose.wp.yml | Starts the Docker infrastructure. |
| setup.sh | Installs/configures WordPress and WooCommerce, including the COD payment prerequisite and checkout shipping-destination configuration required by UI tests. |
| write_env_credentials.sh | Updates the generated REST and GraphQL authentication credentials inside `.env`. |
| seed_test_products.sh | Creates/repairs deterministic baseline UI/E2E products. |
| seed_test_users.sh | Creates/reuses the persistent UI test customer profiles and provisions Customer A's baseline billing/shipping address required by checkout UI tests. |
| EcommerceAPI | Executes the test suite. |

Following the Single Responsibility Principle (SRP), each component owns one specific task. This keeps the bootstrap
process reusable, easier to maintain, and allows the same `setup.sh` script to be used unchanged by both local development and GitHub Actions.

---

### How the components work together

The Docker infrastructure and application bootstrap are separate responsibilities.

**1. `docker-compose.wp.yml` — Defines the environment**

Defines the three services required by the framework:

| Service | Purpose |
|---|---|
| `db` (MySQL) | Database for WordPress and WooCommerce |
| `wordpress` | Runs the WordPress application |
| `wpcli` | Provides command-line tools to install and configure WordPress |

**2. Docker Engine — Creates and runs the containers**

When Docker Compose executes:

```bash
docker compose -f docker-compose.wp.yml up -d
```

It instructs Docker Engine to create and start the containers using their respective images.

At this point, the infrastructure is running, but WordPress and WooCommerce still need to be provisioned.

**3. `scripts/setup.sh` — Installs and configures the application**

The bootstrap script uses WP-CLI to:

1. Install WordPress.
2. Install and activate WooCommerce.
3. Configure WooCommerce and checkout settings.
4. Install and activate additional plugins, including WPGraphQL.
5. Generate WooCommerce REST API credentials.
6. Provision the WordPress Application Password for authenticated GraphQL operations.

**4. WooCommerce environment ready**

The framework now has a configured WooCommerce instance with REST and GraphQL APIs available for testing.

#### End-to-end flow

```text
docker-compose.wp.yml
Defines the services and their configuration
        |
        v
Docker Compose
Orchestrates the services
        |
        v
Docker Engine
Creates and runs the containers
        |
        v
MySQL + WordPress + WP-CLI
Infrastructure is running
        |
        v
scripts/setup.sh
Installs and configures WordPress + WooCommerce
        |
        v
WooCommerce environment ready
        |
        v
EcommerceAPI / pytest
Executes API, GraphQL and database tests
```

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
3. Ensures WooCommerce is installed and active.
4. Ensures WPGraphQL and WPGraphQL for WooCommerce are installed and active.
5. Configures the checkout shipping destination to use the customer's shipping address.
6. Configures the `Test Shipping` zone for Spain with a deterministic Flat Rate shipping method (`0.00`, no tax).
7. Configures permalinks.
7. Waits for the REST API to become available.
8. Waits for the GraphQL API to become available.
9. Generates fresh WooCommerce REST API credentials.
10. Provisions the WordPress Application Password used by authenticated GraphQL operations.
11. Emits the generated credentials to stdout in a machine-readable format.
12. Delegates `.env` updates to `write_env_credentials.sh`.

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

## 6. 🔄 Clean reset

To fully tear down and start fresh:

```bash
make clean
```

The project uses `./wp-data` as a **bind mount** for the WordPress application files. Therefore, `docker compose down -v` removes containers and Docker-managed volumes, but it does **not** remove the repository's `wp-data` directory.

`make clean` performs the complete reset by:

1. stopping and removing the Docker services;
2. removing Docker-managed volumes and orphan containers;
3. deleting the repository's `wp-data` directory.

The next `make run` therefore performs a completely clean WordPress/WooCommerce setup.

> ⚠️ `make down` only stops/removes the running Docker services. It does not delete `wp-data`, so application data and uploaded files remain available for the next `make run`.

---

### UI/E2E data after a clean reset

A clean reset removes the WooCommerce application data used by the UI/E2E
suite.

The next `make run` therefore recreates the deterministic baseline UI/E2E
state required by Playwright before pytest starts:

- baseline products are provisioned by `seed_test_products.sh`;
- Customer A, Customer B, and Customer C are provisioned by
  `seed_test_users.sh`;
- Customer A's baseline billing and shipping address is provisioned by
  `seed_test_users.sh` because checkout tests depend on that saved customer
  state;
- Customer B remains the dedicated address-management customer whose shipping
  address is established by its own UI tests;
- Customer C remains the dedicated mutable profile customer.

This keeps checkout prerequisites in the environment bootstrap instead of
depending on another UI test having created the state first.

The seed operations are idempotent: repeated `make run` executions reuse
existing users/products and converge Customer A's baseline checkout address
to the expected values.

### 🖼️ Repository-local UI image fixtures

Baseline UI/E2E products use image fixtures committed to the repository:

```text
tests/ui/data/images/
├── ui-seed-album.jpg
├── ui-seed-beanie.jpg
└── ui-seed-hoodie.jpg
```

The product seed script imports these files into WordPress through WP-CLI.

The fixtures are mounted read-only into the WP-CLI container during the import
operation.

This deliberately avoids external image URLs so that:

* clean local environments are reproducible
* CI does not depend on a third-party image host
* baseline product images remain deterministic
* UI/E2E seeding works consistently after make clean

The seed also validates the physical featured-image file, not only the
WordPress thumbnail metadata. If an attachment record exists but its physical
file is missing, `seed_test_products.sh` re-imports the repository fixture.
This allows an existing environment with incomplete upload files to repair its
baseline product images without creating duplicate baseline products.

---

## 7. Do you need to build anything yourself?

| Question | Answer |
|---|---|
| Does `docker compose up` build an image? | No — `db` and `wordpress` use official prebuilt images (`mysql`, `wordpress`) |
| Is the `Dockerfile` required for local test runs? | No — by default, pytest runs on the host against the Dockerized WordPress instance (`API_ENV=test`) |
| When *is* the `Dockerfile` used? | When running tests inside a container (`API_ENV=docker`). The current GitHub Actions workflow runs pytest on the hosted runner and does not build this image. |
| Do I need `.dockerignore` for local test runs? | No — only relevant when the `Dockerfile` image is actually built |

---

## 8. 🚦 Test execution models

The framework supports three execution models. **For a QA engineer joining the project, the recommended starting point is Host-Based Execution.** You do not need to build or run the test-runner Docker image to develop tests.

All three models use the same repository, framework code and test suite. The difference is **where pytest runs** and how it connects to the WooCommerce application.

### Quick decision guide

| What are you trying to do? | Use this model | Why? |
|---|---|---|
| Set up the project for the first time | **Host-Based Execution** | `make run` prepares the local development environment and runs the tests. |
| Write or change a test | **Host-Based Execution** | Your IDE, local Python environment and pytest work directly with your current source files. |
| Change framework code or dependencies | **Host-Based Execution** | You can edit, install and test changes without rebuilding a Docker image after every change. |
| Debug a failing test | **Host-Based Execution** | The local debugger and IDE can attach directly to pytest. |
| Check that the project runs in its packaged Docker environment | **Containerized Test Execution** | Confirms that the test-runner image contains the expected code, Python runtime and dependencies. |
| Validate a pull request or run scheduled suites | **CI Execution — GitHub Actions** | Runs automated checks and publishes the configured reports. |

> **The recommended team workflow:** develop and debug locally, validate changes through CI, and use containerized execution when you specifically need to verify the Docker test-runner environment. These are complementary options, not competing versions of the framework.

> 💡 **CI and containerized execution are different concepts.** CI describes how execution is triggered and orchestrated (for example, by GitHub Actions). Containerized execution describes where pytest runs (inside a Docker container). A CI pipeline can run pytest directly on its hosted runner or run a Dockerized test-runner image.

---

### 8.1 🧑‍💻 Default Local Execution — Host-Based

**Use this for normal day-to-day development.** Pytest runs on your computer using the project's local Python environment (`.venv`). Docker is still used for the application under test: WordPress, WooCommerce and MySQL.

You are not running a separate local Apache or WordPress server. The WordPress web server is inside the Dockerized application environment. Your local pytest process sends requests to it through the published `localhost:8080` port.

#### Architecture

```text
┌──────────────────────────────────────────────┐
│              Developer's computer            │
│                                              │
│       Python + .venv + pytest + EcommerceAPI  │
│                  TEST RUNNER                  │
└──────────────────────┬───────────────────────┘
                       │
                       │ HTTP / REST / GraphQL
                       │ localhost:8080
                       ▼
┌──────────────────────────────────────────────┐
│                    Docker                    │
│                                              │
│       WordPress + WooCommerce + MySQL         │
│             APPLICATION UNDER TEST           │
└──────────────────────────────────────────────┘
```

#### First-time setup

Clone the repository, enter the project directory and run:

```bash
make run
```

This prepares the local environment, starts and provisions WooCommerce, installs the framework's development dependencies, prepares Playwright browsers and runs the test suite.

#### Everyday development workflow

Once the environment is set up, the normal development loop is:

1. Create a feature branch.
2. Edit tests or framework code in your IDE.
3. Run the relevant test or suite with your local pytest environment.
4. Debug and iterate as needed.
5. Commit and push your changes, then open a pull request.

For example, run pytest from the project root:

```bash
pytest
```

You can also target a specific test file, directory or marker using the usual pytest options. You do not need to rebuild the test-runner Docker image when you change a test or framework file in this host-based workflow.

If you have stopped the WooCommerce services, start them and provision the application again before running tests:

```bash
make up
make setup
```

#### Connection configuration

The host-based test runner uses host-accessible endpoints:

- `API_ENV=test`
- REST API: `http://localhost:8080/wp-json/wc/v3/`
- GraphQL API: `http://localhost:8080/graphql`
- Database host: the host-accessible MySQL address and published port (for example, `127.0.0.1:3306`).

#### When to use it

- Developing new API, GraphQL, database or UI tests.
- Updating shared framework code, fixtures, builders or helpers.
- Installing or changing Python dependencies during development.
- Running individual tests, test files or complete suites.
- Debugging failures using an IDE or Python debugger.
- Getting fast feedback without rebuilding a test-runner image.

**Recommended for everyday local development and the default approach for QA engineers contributing to this repository.**

---

### 8.2 🐳 Containerized Test Execution

In this model, **pytest itself runs inside Docker**. The custom test-runner image packages the Python runtime, framework dependencies and the project files copied into the image. The test-runner container connects to the WooCommerce services over the Docker network.

This is an additional execution option. It is not necessary for every test change or every local development run.

#### Architecture

```text
┌────────────────────────────────────────────────────┐
│                       Docker                       │
│                                                    │
│  ┌──────────────────────┐                          │
│  │   Test-runner        │                          │
│  │   container          │                          │
│  │                      │                          │
│  │   Python + pytest    │                          │
│  │   EcommerceAPI       │                          │
│  │   Tests              │                          │
│  └──────────┬───────────┘                          │
│             │                                      │
│             │ Docker network                       │
│             │                                      │
│  ┌──────────▼───────────┐    ┌──────────────────┐   │
│  │ WordPress +          │    │      MySQL       │   │
│  │ WooCommerce          │    │                  │   │
│  └──────────────────────┘    └──────────────────┘   │
│                                                    │
└────────────────────────────────────────────────────┘
```

#### How it works

1. Start the WooCommerce infrastructure with Docker Compose.
2. Provision WordPress, WooCommerce, plugins, credentials and test data.
3. Build the custom test-runner image from the project's `Dockerfile`.
4. Start a test-runner container on the same Docker network as the application services.
5. Pytest executes inside that container.
6. The test runner reaches WordPress and MySQL using Docker service names.

Inside a Docker network, containers should use service names such as `wordpress` and `db`, rather than `localhost`. Within the test-runner container, `localhost` refers to the test-runner container itself.

#### Important: what happens when you change code?

The current Dockerfile copies the framework and tests into the image during the image build. The image therefore contains a **snapshot of the source code at build time**.

- If you change a test or framework file on your computer, the already-built image does not automatically receive that change.
- To test the updated source using the current image approach, rebuild the image.
- If you only want to develop and iterate quickly, use Host-Based Execution instead.

A Docker development setup with bind mounts or an IDE Dev Container can make live source changes available inside a container, but that is a different configuration and is not what the current `docker run` example below sets up.

#### Example

Start and provision the application:

```bash
make up
make setup
```

Build the test-runner image:

```bash
docker build -t ecommerceapi-test-runner .
```

Run the test runner:

```bash
docker run --rm \
  --network <compose-network-name> \
  --env-file .env \
  -e API_ENV=docker \
  -e DB_HOST=db \
  ecommerceapi-test-runner
```

The image must have a suitable `CMD` or `ENTRYPOINT` that runs pytest. Replace the network placeholder with the actual network created by this project's Compose configuration. The `--env-file` passes configured environment variables into the container; explicit `-e` values override matching values from that file.

When finished, stop the WooCommerce infrastructure:

```bash
make down
```

`docker run --rm` removes the test-runner container when it exits. It does **not** stop the WooCommerce services; `make down` handles those services.

#### Configuration differences

| Setting | Host-Based Execution | Containerized Execution |
|---|---|---|
| `API_ENV` | `test` | `docker` |
| WordPress hostname | `localhost` | `wordpress` |
| Database hostname | Host-accessible address, e.g. `127.0.0.1` | `db` |
| Database port | Published host port | Internal MySQL service port |
| Test runner location | Developer's computer | Test-runner container |

`API_ENV` selects the endpoint configuration; it does not start Docker or decide where pytest runs. Selecting `API_ENV=docker` is appropriate when the test runner is actually inside the Docker network.

#### When to use it

- Verifying that the framework and tests run in the packaged Docker environment.
- Checking that the expected Python version and dependencies are included in the image.
- Reproducing an issue that occurs only inside the container.
- Providing a portable, controlled test-runner environment for another team or machine.
- Preparing or validating a containerized runner that could later be used by CI.

**Use this when you need to validate or distribute the containerized test-runner environment. It is not the default workflow for editing tests.**

---

### 8.3 ⚙️ CI Execution — GitHub Actions

CI execution automates test runs in response to events such as pull requests, pushes or scheduled workflows.

In the project's **current GitHub Actions setup**, the GitHub-hosted runner is the test runner. Python and the project dependencies are installed on that runner, while Docker Compose starts the WooCommerce application services. Pytest runs directly on the GitHub-hosted runner — it does not run inside the custom test-runner image.

#### Architecture

```text
┌────────────────────────────────────────────────────┐
│                  GitHub Actions                     │
│                                                    │
│  ┌──────────────────────────────────────────────┐  │
│  │              GitHub-hosted runner             │  │
│  │                                              │  │
│  │       Python + pytest + EcommerceAPI          │  │
│  │                 TEST RUNNER                   │  │
│  └──────────────────────┬───────────────────────┘  │
│                         │                          │
│                         │ localhost:8080           │
│                         ▼                          │
│  ┌──────────────────────────────────────────────┐  │
│  │                    Docker                    │  │
│  │                                              │  │
│  │       WordPress + WooCommerce + MySQL         │  │
│  │              APPLICATION UNDER TEST          │  │
│  └──────────────────────────────────────────────┘  │
│                                                    │
└────────────────────────────────────────────────────┘
```

#### How it works

1. A GitHub event triggers the relevant workflow.
2. GitHub Actions provisions a hosted runner and checks out the repository.
3. The workflow sets up Python and installs the project dependencies.
4. Docker Compose starts the WooCommerce infrastructure.
5. The setup process provisions WordPress, WooCommerce, plugins and test data.
6. Pytest executes directly on the GitHub-hosted runner.
7. Allure results and other test artifacts are uploaded.
8. The workflow attempts Docker cleanup, including when earlier steps fail.

The project's reusable workflows and composite actions coordinate common setup, execution, reporting and cleanup tasks.

#### Example: pull request validation

```text
Pull Request
     │
     ▼
PR Validation Workflow
     │
     ├── Preflight Checks
     │
     ├── Unit Tests
     │
     └── Integration Tests
              │
              ▼
         Quality Gate
              │
              ▼
       PR Validation Result
```

Other workflows can run smoke, regression, performance, contract and security tests according to their configured triggers.

#### Configuration

The current CI execution uses the host-accessible service endpoints from the GitHub-hosted runner:

- `API_ENV=ci`
- REST API: `http://localhost:8080/wp-json/wc/v3/`
- GraphQL API: `http://localhost:8080/graphql`
- Database host: `127.0.0.1`
- Database port: the published MySQL port (`3306`).

The hosted runner reaches the Dockerized services through their published host ports. This is why the CI configuration differs from the `API_ENV=docker` configuration used by a test runner inside the Docker network.

#### When to use it

- Automatically validating pull requests.
- Running tests after code is pushed to a branch.
- Executing scheduled regression suites.
- Enforcing quality gates before changes are merged.
- Generating and publishing Allure reports.
- Providing repeatable validation results to the development team.

**This is the project's current approach to automated CI validation.**

---

### 8.4 🔀 Comparing the three execution models

| Aspect | Local Host-Based | Containerized Test Runner | GitHub Actions CI |
|---|---|---|---|
| Where pytest runs | Developer's computer | Docker container | GitHub-hosted runner |
| Where WooCommerce runs | Docker | Docker | Docker |
| Python environment | Local `.venv` | Built into test-runner image | Set up on CI runner |
| API connection | Host-published port | Docker service name | Host-published port |
| Typical trigger | Developer | Developer or automation | GitHub event or schedule |
| Main purpose | Development and debugging | Reproducible packaged execution | Automated validation |

### 8.5 🎯 Recommended team workflow

For a team sharing and maintaining this framework, use the execution models together:

| Team activity | Recommended execution |
|---|---|
| New QA engineer onboarding | Host-Based — `make run` |
| Developing or updating tests | Host-Based |
| Changing framework code or dependencies | Host-Based |
| Debugging a failing test | Host-Based |
| Checking the packaged Docker runner | Containerized Test Runner |
| Validating a pull request | GitHub Actions CI |
| Running nightly regression | GitHub Actions CI |
| Investigating a container-specific failure | Containerized Test Runner |

The normal contribution lifecycle is:

```text
Clone / Pull latest changes
          │
          ▼
     make run
  (local setup)
          │
          ▼
 Develop tests and framework
     using local .venv
          │
          ▼
 Run relevant pytest tests
          │
          ▼
     Commit / Push
          │
          ▼
    Open Pull Request
          │
          ▼
    GitHub Actions CI
          │
          ▼
      Review / Merge
```

This keeps everyday development quick while ensuring that changes are validated automatically before they are merged.

### 8.6 🧩 CI and containerized execution can be combined

The three models are not mutually exclusive. A CI pipeline can also build and execute the test-runner Docker image instead of installing Python directly on the hosted runner.

For example, a future containerized CI flow could look like this:

```text
GitHub Actions
      │
      ▼
Build Test-runner Image
      │
      ▼
Start WooCommerce Infrastructure
      │
      ▼
Run Test-runner Container
      │
      ▼
Execute Pytest
      │
      ▼
Publish Allure Results
      │
      ▼
Cleanup Docker Environment
```

That approach combines automated CI orchestration with containerized test execution. It is an alternative architecture, not a description of the current workflow.

The key principle is to maintain **one shared framework and one test suite**, independent of the execution environment. Developers can work locally, validate the packaged runner in Docker, and rely on CI/CD for automated team-wide validation.

---

## 9. Core Docker concepts (quick reference)

- **Image** — a blueprint (e.g. `mysql:8`, `wordpress:latest`)
- **Container** — a running instance of an image
- **Dockerfile** — instructions for building a custom image (used here for the test-runner image, not for WordPress/MySQL)
- **docker-compose** — orchestrates multiple containers as one stack

---

## 10. Framework vs Infrastructure (Mental model)

```
Framework (EcommerceAPI)  → HOW tests run
Docker + WordPress         → WHERE tests run
setup.sh                   → turns an empty Docker environment into a
                              usable WooCommerce instance
Makefile                   → single entrypoint tying it all together
```

---

## 11. Requirements

- Docker
- Docker Compose
- Python 3.13+
- Make (or Git Bash on Windows)

---

## 12. 🛠️ Troubleshooting

| Symptom | Possible cause | Solution |
|---------|----------------|----------|
| 401 Unauthorized | Stale WooCommerce credentials | Re-run `make run` to regenerate credentials. |
| Tests target the wrong URL | `WC_API_URL` exists in `.env` | Remove `WC_API_URL`. The framework resolves URLs from `API_ENV`. |
| WordPress installation missing | Bootstrap interrupted | Run `make setup`. |
| WordPress files missing | `wp-data` bind mount missing | Create `wp-data/` and rerun `make run`. |
| `wp-graphql` reports “already installed” but cannot be activated | Stale WordPress plugin state / missing plugin files | Run `make run` again. `setup.sh` automatically reinstalls required plugins when they are not both installed and active. |
| `No generated credential lines received on stdin` | Bootstrap failed before credential generation | Check the setup error immediately above this message; the credential error is a downstream symptom. |
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
