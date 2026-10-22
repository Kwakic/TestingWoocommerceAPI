````
# 📁 Project Structure Guide

Quick navigation to understand what each directory does and where to find related documentation.

---

## 🗺️ Visual Project Map

```
TestEcommerceAPI (Root)
│
├── 📚 docs/                          ← Documentation Hub (START HERE)
├── 🔧 EcommerceAPI/                  ← Shared Framework Package
├── 🧪 tests/                         ← Domain-Driven Test Suites
├── 📊 reports/                       ← Test Results & Artifacts
├── ⚙️  .github/                      ← CI/CD & GitHub Actions
├── 🛠️  scripts/                      ← Utility Scripts
├── 📦 Root Config Files              ← Project Configuration
│
└── [Full tree below ↓]
```

---

## 📚 **Docs/** — Documentation Hub

Your **single source of truth** for learning the framework.

| Directory | Purpose | Best For |
|-----------|---------|----------|
| **getting-started/** | Onboarding & framework overview | New team members |
| **development/** | How to write tests & extend framework | Test writers, QA devs |
| **framework/** | Technical deep-dives (plugins, auth, config) | Framework maintainers |
| **ci/** | CI/CD pipeline design & workflows | DevOps, pipeline setup |
| **contributing/** | Contributing, changelog, packaging | Contributors |
| **project-structure/** | This directory structure | Navigation & orientation |

### 📖 Key Documents

| Document | Read When |
|----------|-----------|
| [Framework Overview](../getting-started/README_FRAMEWORK_OVERVIEW.md) | You're new to the project |
| [Test Development Guide](../development/README_TEST_DEVELOPMENT_GUIDE.md) ⭐ | Writing tests (canonical reference) |
| [API Client Guide](../development/README_API_CLIENT.md) | Using the HTTP client |
| [Plugins Reference](../framework/README_PLUGINS_REFERENCE.md) | Understanding fixtures & plugin system |
| [CI Architecture](../ci/README_CI_ARCHITECTURE.md) | Understanding workflows & pipelines |

---

## 🔧 **EcommerceAPI/** — Shared Framework Package

**Installable Python package** that all tests depend on.

### What It Does
- Provides reusable **pytest fixtures** (one per domain: customers, products, orders, coupons)
- Implements **HTTP transport layer** (requests wrapper with auth)
- Defines **API clients** for each business domain
- Supplies **data validators** & Pydantic models
- Offers **shared utilities** (logging, DB ops, credentials, etc.)
- Manages **configuration & environment resolution**

### Structure

```
EcommerceAPI/
│
├── plugins/                          ← pytest plugin system
│   ├── api/
│   │   ├── shared_api.py             ← Shared REST API fixtures
│   │   ├── shared_graphql.py         ← Shared GraphQL fixtures
│   │   ├── customers.py              ← @pytest.fixture for customers
│   │   ├── products.py               ← @pytest.fixture for products
│   │   ├── coupons.py                ← @pytest.fixture for coupons
│   │   └── orders.py                 ← @pytest.fixture for orders
│   ├── api_fixtures.py               ← Fixture setup & configuration
│   ├── db_fixtures.py                ← Database-related fixtures
│   ├── config_pytest.py              ← pytest hook implementations
│   ├── allure_autogen.py             ← Allure report auto-generation
│   ├── logging_plugin.py             ← Structured logging integration
│   ├── entities.py                   ← Dependency container
│   ├── entity_metadata.py            ← Entity discovery metadata
│   ├── reporting.py                  ← Report generation
│   └── README_plugins.md             ← Plugins documentation
│
├── src/                              ← ⚠️ ONLY reusable/shared/global
│   ├── metadata/
│   │   ├── entity_metadata.py        ← Entity discovery data
│   │   ├── runtime_metadata.py       ← Runtime metadata (future)
│   │   ├── deployment_metadata.py    ← Deployment metadata (future)
│   │   └── __init__.py
│   │
│   ├── configs/
│   │   ├── config_graphql.py         ← GraphQL endpoint configuration by environment
│   │   ├── config_loader.py          ← Load environment and service configuration
│   │   ├── runtime_config.py         ← Framework runtime configuration
│   │   ├── runtime_metadata.py       ← Runtime session metadata (shared, plugin-agnostic)
│   │   ├── README.md                 ← Configuration guide
│   │   └── __init__.py
│   │
│   ├── auth/                         ← Authentication implementations
│   │   ├── base_auth.py              ← Abstract auth base class
│   │   ├── oauth1_auth.py            ← OAuth1 handler
│   │   ├── oauth2_auth.py            ← OAuth2 handler
│   │   ├── jwt_auth.py               ← JWT handler
│   │   ├── basic_auth.py             ← Basic auth handler
│   │   ├── auth_factory.py           ← Auth strategy factory
│   │   ├── auth_resolver.py          ← Auth resolution logic
│   │   └── __init__.py
│   │
│   ├── core/                         ← Core HTTP transport and response models
│   │   ├── http_client.py            ← Low-level HTTP transport wrapper
│   │   ├── graphql_response.py       ← GraphQL response and error model
│   │   ├── http_response.py          ← Generic HTTP response object model
│   │   ├── request_context.py        ← Request context tracking
│   │   └── __init__.py
│   │
│   ├── clients/                      ← High-level API orchestration
│   │   ├── api_client.py             ← Main REST API client (uses http_client)
│   │   ├── graphql_client.py         ← Main GraphQL API client (uses http_client)
│   │   └── __init__.py
│   │
│   ├── entities/                     ← Domain-specific entity implementations
│   │   ├── customers/                ← Domain: Customers
│   │   │   ├── dao/                  ← Data access & business logic
│   │   │   │   ├── customers_dao.py
│   │   │   │   └── __init__.py
│   │   │   ├── api/                  ← Domain API wrapper
│   │   │   │   ├── customers_api.py
│   │   │   │   └── __init__.py
│   │   │   ├── validators/           ← Custom validators
│   │   │   │   ├── customer_db_validators.py
│   │   │   │   ├── customer_validators.py
│   │   │   │   └── __init__.py
│   │   │   ├── models/               ← Pydantic models (runtime validation)
│   │   │   │   ├── customer_model.py ← canonical Customer model
│   │   │   │   └── __init__.py
│   │   │   └── helpers/              ← Business & API logic
│   │   │       ├── customers_helper.py
│   │   │       └── __init__.py
│   │   ├── products/                 ← Domain: Products (same structure)
│   │   ├── orders/                   ← Domain: Orders (same structure)
│   │   ├── coupons/                  ← Domain: Coupons (same structure)
│   │   └── __init__.py
│   │
│   ├── shared/                       ← ⚠️ Reusable across all domains
│   │   ├── assertions/               ← Common assertion helpers
│   │   │   ├── common_assertions.py
│   │   │   └── __init__.py
│   │   ├── api/                      ← Shared API utilities
│   │   │   ├── common_api.py
│   │   │   └── __init__.py
│   │   └── helpers/                  ← Shared helpers
│   │       ├── cleanup_helpers.py
│   │       └── __init__.py
│   │
│   ├── utils/                        ← ⚠️ Universal reusable utilities
│   │   ├── bulk_ops.py               ← Bulk operations
│   │   ├── credentials_utility.py    ← Credential management
│   │   ├── custom_logger.py          ← Logging utilities
│   │   ├── data_utils.py             ← Data transformation
│   │   ├── date_timestamp_utils.py   ← Date/time helpers
│   │   ├── db_utility.py             ← Database operations
│   │   ├── entities_registry.py      ← Entity registry
│   │   ├── env_utils.py              ← Environment utilities
│   │   ├── exceptions.py             ← Custom exceptions
│   │   ├── filtering_utils.py        ← Filtering helpers
│   │   ├── generic_utilities.py      ← Generic utilities
│   │   ├── log_context.py            ← Log context management
│   │   ├── pagination_utils.py       ← Pagination helpers
│   │   ├── performance_utils.py      ← Performance measurement
│   │   ├── entity_discovery.py       ← Dynamic entity discovery
│   │   ├── truncate_logging_utils.py ← Log truncation
│   │   └── __init__.py
│   │
│   ├── manual_cleanup_scripts/       ← Manual cleanup utilities
│   └── __init__.py
│
├── __init__.py
└── pyproject.toml                    ← Package metadata & dependencies
```

### 📝 When to Edit

- **Add new domain?** → Create `src/entities/{domain}/` with DAOs, APIs, validators, models
- **Add shared utility?** → Add to `src/utils/`
- **Add new auth scheme?** → Add to `src/auth/`
- **Add new fixture?** → Add to `plugins/api/{domain}.py` or `plugins/*_fixtures.py`

### 📖 Read Also

- [Plugins Reference](../framework/README_PLUGINS_REFERENCE.md)
- [API Client Guide](../development/README_API_CLIENT.md)
- [Authentication Guide](../framework/README_AUTHENTICATION.md)

---

## 🧪 **Tests/** — Domain-Driven Test Suites

Each **business entity owns its own test suite**. Independent, scalable, and clear ownership.

### Structure

```
tests/
│
├── customers/                        ← Domain: Customers
│   ├── configs/
│   │   ├── config_customers.py       ← API hosts & domain config
│   │   ├── __init__.py
│   │   └── Entity_Configuration_Guide.md
│   ├── data/
│   │   ├── __init__.py
│   │   └── create_customer_payload.json ← Test payloads
│   ├── __init__.py
│   ├── conftest.py                  ← Domain-specific fixtures
│   ├── api/                         ← REST API tests for this business entity
│   │   ├── test_create_customer.py
│   │   ├── test_customer_deletion.py
│   │   ├── test_customer_filters.py
│   │   ├── test_e2e_customer_lifecycle.py
│   │   ├── test_get_all_customers.py
│   │   ├── test_get_customer.py
│   │   ├── test_soft_deleted_customer_handling.py
│   │   ├── test_update_customer.py
│   │   └── __init__.py
│   ├── graphql/                       ← GraphQL queries/mutations
│   │   ├── test_create_customer.py
│   │   ├── test_delete_customer.py
│   │   ├── test_get_customer.py
│   │   ├── test_update_customer.py
│   │   ├── test_customer_negative.py
│   │   └── __init__.py
│   └── performance/
│       ├── test_customer_performance.py
│       └── __init__.py
│
├── products/                         ← Domain: Products (same structure)
├── orders/                           ← Domain: Orders (same structure)
├── coupons/                          ← Domain: Coupons (same structure)
├── shared/                           ← Framework-level tests (run once)
│   ├── __init__.py
│   ├── contracts/                             ← Contract testing (response schemas)
│   │    ├── rest/
│   │    │    ├── error_schema.py              ← Error response contracts
│   │    │    ├── test_response_format.py      ← Validate response format
│   │    │    ├── test_api_connectivity.py     ← Basic rest connectivity checks
│   │    │    └── __init__.py
│   │    └── graphql/
│   │         ├── test_graphql_conectivity.py  ← Basic graphql connectivity checks
│   │         ├── test_product_mutation_schema.py  ← Validation of GraphQL schema
│   │         └── __init__.py
│   ├── security/                     ← Security & auth validation
│   │   ├── test_authentication_matrix.py ← Auth scheme matrix
│   │   ├── test_authentication_success.py ← Successful auth scenarios
│   │   └── __init__.py
│   └── preflight/                    ← Pre-test checks
│       ├── test_logging_globals.py   ← Logging validation
│       ├── __init__.py
│       └── README_PREFLIGHT.md
│
├── ui/                               ← Playwright tests
│   ├── tests
│   ├──  __init__.py
│   │
│   ├───account
│   │   │   test_customer_account.py
│   │   │   test_customer_account_details.py
│   │   │   test_customer_address.py
│   │   └───  __init__.py
│   │
│   ├───admin
│   │   │   test_admin_authentication.py
│   │   └───  __init__.py
│   ├───auth
│   │   │   README Playwright Authentication & Page Object Arch
│   │   │   test_customer_login.py
│   │   │   test_customer_login_security.py
│   │   │   test_customer_password_recovery.py
│   │   │   test_customer_registration.py
│   │   │   test_customer_registration_security.py
│   │   │   test_customer_session_security.py
│   │   └─── __init__.py
│   ├───catalog
│   │   │   test_product_discovery.py
│   │   │   test_product_review.py
│   │   └───  __init__.py
│   ├───home
│   │   │   test_home_page.py
│   │   └───  __init__.py
│   └───shopping
│       │   __init__.py
│       │
│       ├───cart
│       │   │   test_add_product_to_cart.py
│       │   │   test_apply_coupon.py
│       │   │   test_cart_contents.py
│       │   │   test_remove_product_from_cart.py
│       │   │   test_update_cart_quantity.py
│       │   └───  __init__.py
│       └───checkout
│            │   test_customer_checkout.py
│            │   test_guest_can_checkout.py
│            │   test_order_confirmation.py
│            └───  __init__.py
│
├── pages/                        ← Page Objects
├── components/                   ← Reusable UI components
├── data/                         ← UI test data
├── fixtures.py                   ← UI-specific fixtures
└── README.md                     ← UI testing guide

```

### 📋 Test Types per Domain

Each domain (`customers/`, `products/`, `orders/`, `coupons/`) contains:

| Test Type | Location | Examples |
|-----------|----------|----------|
| **Smoke** | `api/` | Create, read, delete basic operations |
| **Integration** | `api/` | Multi-step workflows, cross-entity tests |
| **Regression** | `api/` | Bug fixes, edge cases, known issues |
| **Performance** | `performance/` | Load tests, response times, bulk ops |

### 📖 Team Guides

| Domain | Team Guide |
|--------|-----------|
| **customers/** | [Customers Guide](../development/TEAM_GUIDES/README_CUSTOMERS.md) |
| **products/** | [Products Guide](../development/TEAM_GUIDES/README_PRODUCTS.md) |
| **orders/** | [Orders Guide](../development/TEAM_GUIDES/README_ORDERS.md) |
| **coupons/** | [Coupons Guide](../development/TEAM_GUIDES/README_COUPONS.md) |
| **shared/** | Framework-level validation — no dedicated team guide |

### 📝 When to Edit

- **Add domain test?** → Create `tests/{domain}/api/test_*.py`
- **Add test data?** → Add to `tests/{domain}/data/`
- **Add domain fixture?** → Add to `tests/{domain}/conftest.py`
- **Add shared test?** → Add to `tests/shared/{contracts,security,preflight}/`

### 📖 Read Also

- [Test Development Guide](../development/README_TEST_DEVELOPMENT_GUIDE.md)
- [Team Guides](../development/TEAM_GUIDES/) — Domain-specific conventions
  - [Customers Guide](../development/TEAM_GUIDES/README_CUSTOMERS.md)
  - [Products Guide](../development/TEAM_GUIDES/README_PRODUCTS.md)
  - [Orders Guide](../development/TEAM_GUIDES/README_ORDERS.md)
  - [Coupons Guide](../development/TEAM_GUIDES/README_COUPONS.md)

---

## 📊 **Reports/** — Test Results & Artifacts

Generated test results, logs, and interactive reports.

```
reports/
│
├── allure-report/                    ← Interactive HTML report
│   ├── data/                         ← Allure data files
│   ├── export/                       ← Export data
│   ├── history/                      ← Historical trends
│   ├── plugins/                      ← Allure plugins
│   ├── widgets/                      ← Report widgets
│   ├── app.js                        ← Report application
│   ├── favicon.ico
│   ├── index.html                    ← Open this in browser
│   └── style.css
│
├── allure-results/                   ← Raw test results (JSON)
│   ├── *-result.json                 ← Test execution results
│   ├── *-container.json              ← Test containers
│   ├── *-attachment.txt              ← Logs & attachments
│   ├── categories.json               ← Result categories
│   ├── environment.properties        ← Test environment info
│   └── etc.
│
└── logs/                             ← Structured test logs
    ├── customers/
    │   ├── docker/                   ← Docker environment logs
    │   │   └── test_debug_structured_*.jsonl
    │   └── test/                     ← Test environment logs
    │       └── test_debug_structured_*.jsonl
    ├── products/
    │   └── test/
    │       └── test_debug_structured_*.jsonl
    └── shared/
        ├── dev/
        │   └── test_debug_structured_*.jsonl
        └── test/
            └── test_debug_structured_*.jsonl
```

### 📝 How to Use

- **View test report** → Open `reports/allure-report/index.html` in your browser
- **Debug failures** → Check `reports/logs/{domain}/test/` for structured logs
- **Analyze trends** → Allure report shows historical data in `reports/allure-report/history/`

### 📖 Read Also

- [Allure Reporting Guide](../ci/README_ALLURE.md)

---

## ⚙️ **.github/** — CI/CD & GitHub Actions

Automation, workflows, and GitHub-specific configuration.

```
.github/
│
├── workflows/                        ← GitHub Actions workflows
│   ├── smoke.yml                     ← Smoke test pipeline
│   ├── integration.yml               ← Integration test pipeline
│   ├── regression.yml                ← Regression test pipeline
│   ├── performance.yml               ← Performance test pipeline
│   ├── contract.yml                  ← Contract test pipeline
│   ├── preflight.yml                 ← Pre-flight checks
│   ├── security.yml                  ← Security test pipeline
│   ├── ui.yml                        ← Playwright UI tests pipeline
│   ├── e2e.yml                       ← Future API → UI → API
│   ├── dashboard-publisher.yml       ← Allure dashboard publishing
│   ├── reusable-test-runner.yml      ← Reusable test execution
│   └── reusable-allure-report.yml    ← Reusable report generation
│
├── actions/                          ← Custom GitHub Actions
│   ├── setup-python-project/
│   │   └── action.yml                ← Python project setup
│   ├── configure-ci-env/
│   │   └── action.yml                ← CI environment setup
│   ├── docker-cleanup/
│   │   └── action.yml                ← Docker cleanup action
│   └── setup-woocommerce/
│       └── action.yml                ← WooCommerce container setup
│
├── scripts/
│   └──  generate_matrix.py           ← Generate test matrix
│
└── portal/                           ← Allure portal configuration
    ├── style.css                     ← Portal styling
    └── generate_portal.py            ← Generate Allure portal
```

### 📝 When to Edit

- **Add new test pipeline?** → Create `workflows/new-test-type.yml`
- **Modify CI environment?** → Edit `actions/configure-ci-env/action.yml`
- **Update Docker setup?** → Edit `actions/setup-woocommerce/action.yml`

### 📖 Read Also

- [CI Architecture Guide](../ci/README_CI_ARCHITECTURE.md)
- [Allure Reporting Guide](../ci/README_ALLURE.md)

---

## 🛠️ **Scripts/** — Utility Scripts

Shared project utilities and helpers.

```
scripts/
├── setup.sh                          ← Project setup script
├── seed_test_users.sh                ← Seed UI users
├── seed_test_products.sh             ← Seed UI products
└── write_env_credentials.sh          ← Environment credential setup
```

### 📝 When to Edit

- Add new setup or utility scripts here

---

## 📦 **Root Configuration Files**

Project-level configuration and orchestration.

| File                          | Purpose                                                         |
|-------------------------------|-----------------------------------------------------------------|
| **Makefile**                  | Orchestrates common tasks (`make run`, `make test`, etc.)       |
| **pytest.ini**                | pytest configuration & marker definitions                       |
| **conftest.py**               | Shared root-level fixtures & hooks                              |
| **.env**                      | Local environment variables & credentials                       |
| **.env.example**              | Template for `.env` file                                        |
| **docker-compose.matrix.yml** | Multi-container setup (WordPress, WooCommerce, MySQL)           |
| **Dockerfile**                | Container image for CI/CD execution                             |
| **README.md**                 | Project landing page & documentation index                      |
| **.gitignore**                | Git ignore rules                                                |
| **CHANGELOG.md**              | Project changelog                                               |
| **pyproject.toml**            | Python project metadata (in EcommerceAPI/)                      |
| **scripts**                   | setup, write_env_credentials, seed_test_usersseed_test_products |

### 📝 When to Edit

- **Changing test execution?** → Edit `Makefile`, `pytest.ini`, `conftest.py`
- **Adding environment variable?** → Edit `.env.example` & `.env`
- **Changing Docker setup?** → Edit `docker-compose.matrix.yml`
- **Recording changes?** → Update `CHANGELOG.md`

---

## 🚀 Common Tasks & Where to Find Files

### 👤 QA Developer — Writing Tests

```
📍 Workspace:
   └── tests/{domain}/api/test_*.py              ← Write tests here
   └── tests/{domain}/data/                      ← Add test payloads
   └── tests/{domain}/conftest.py                ← Add domain fixtures

📖 Read:
   └── docs/development/TEAM_GUIDES/README_{DOMAIN}.md  ← Team conventions
   └── docs/development/README_TEST_DEVELOPMENT_GUIDE.md ← Framework guide

🚀 Execute:
   └── pytest tests/{domain}                     ← Run domain tests
   └── make run                                  ← Full setup & execution
```

### 🛠️ Framework Maintainer — Extending Framework

```
📍 Workspace:
   └── EcommerceAPI/src/                         ← Core framework
   └── EcommerceAPI/plugins/                     ← Fixtures & plugins
   └── docs/framework/                           ← Framework documentation

📖 Read:
   └── docs/framework/README_PLUGINS_REFERENCE.md
   └── docs/development/README_ARCHITECTURE.md

🚀 Execute:
   └── pytest tests/shared                       ← Test framework
   └── make install-dev                          ← Develop mode
```

### 🔄 DevOps Engineer — CI/CD Pipeline

```
📍 Workspace:
   └── .github/workflows/                        ← Edit pipelines
   └── .github/actions/                          ← Edit custom actions
   └── docker-compose.matrix.yml                 ← Docker config

📖 Read:
   └── docs/ci/README_CI_ARCHITECTURE.md
   └── docs/ci/README_DOCKER_INFRASTRUCTURE.md

🚀 Execute:
   └── Commit & push to trigger workflows
```

### 🔍 Test Analyzer — Debugging Failures

```
📍 Workspace:
   └── reports/allure-report/index.html          ← View results
   └── reports/logs/{domain}/test/               ← Read logs

📖 Read:
   └── docs/ci/README_ALLURE.md

🚀 Execute:
   └── make report                               ← Regenerate report
```

---

## 🗂️ Full Project Tree

The following tree is updated from the repository output provided on 22 October 2026:

```text
TestEcommerceAPI/
├── .github/
│   ├── actions/
│   │   ├── configure-ci-env/
│   │   │   └── action.yml
│   │   ├── docker-cleanup/
│   │   │   └── action.yml
│   │   ├── setup-python-project/
│   │   │   └── action.yml
│   │   └── setup-woocommerce/
│   │       └── action.yml
│   ├── portal/
│   │   ├── __init__.py
│   │   ├── generate_portal.py
│   │   └── style.css
│   ├── scripts/
│   │   ├── __init__.py
│   │   └── generate_matrix.py
│   ├── workflows/
│   │   ├── contract.yml
│   │   ├── dashboard-publisher.yml
│   │   ├── integration.yml
│   │   ├── performance.yml
│   │   ├── preflight.yml
│   │   ├── regression.yml
│   │   ├── reusable-allure-report.yml
│   │   ├── reusable-test-runner.yml
│   │   ├── security.yml
│   │   ├── smoke.yml
│   │   └── ui.yml
│   └── __init__.py
├── .idea/
│   ├── inspectionProfiles/
│   │   └── profiles_settings.xml
│   ├── .gitignore
│   ├── .name
│   ├── API_TESTING_MS.iml
│   ├── misc.xml
│   ├── modules.xml
│   ├── vcs.xml
│   └── workspace.xml
├── EcommerceAPI/
│   ├── plugins/
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── coupons.py
│   │   │   ├── customers.py
│   │   │   ├── orders.py
│   │   │   ├── products.py
│   │   │   ├── shared_api.py
│   │   │   └── shared_graphql.py
│   │   ├── README_plugins.md
│   │   ├── __init__.py
│   │   ├── allure_autogen.py
│   │   ├── config_pytest.py
│   │   ├── db_fixtures.py
│   │   ├── entities.py
│   │   ├── logging_plugin.py
│   │   └── reporting.py
│   ├── src/
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── auth_factory.py
│   │   │   ├── auth_resolver.py
│   │   │   ├── base_auth.py
│   │   │   ├── basic_auth.py
│   │   │   ├── jwt_auth.py
│   │   │   ├── oauth1_auth.py
│   │   │   └── oauth2_auth.py
│   │   ├── clients/
│   │   │   ├── __init__.py
│   │   │   ├── api_client.py
│   │   │   └── graphql_client.py
│   │   ├── configs/
│   │   │   ├── __init__.py
│   │   │   ├── config_graphql.py
│   │   │   ├── config_loader.py
│   │   │   ├── runtime_config.py
│   │   │   └── runtime_metadata.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── graphql_response.py
│   │   │   ├── http_client.py
│   │   │   ├── http_response.py
│   │   │   └── request_context.py
│   │   ├── entities/
│   │   │   ├── coupons/
│   │   │   ├── customers/
│   │   │   ├── orders/
│   │   │   ├── products/
│   │   │   └── __init__.py
│   │   ├── manual_cleanup_scripts/
│   │   │   ├── __init__.py
│   │   │   ├── coupons_cleaner.py
│   │   │   ├── delete_coupon_individually.py
│   │   │   └── delete_entities_from_code_and_CLI.py
│   │   ├── metadata/
│   │   │   ├── __init__.py
│   │   │   └── entity_metadata.py
│   │   ├── shared/
│   │   │   ├── api/
│   │   │   ├── assertions/
│   │   │   ├── helpers/
│   │   │   └── __init__.py
│   │   ├── test_data/
│   │   │   ├── builders/
│   │   │   ├── factories/
│   │   │   ├── ownership/
│   │   │   ├── provisioning/
│   │   │   ├── seeds/
│   │   │   └── __init__.py
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   ├── bulk_ops.py
│   │   │   ├── credentials_utility.py
│   │   │   ├── custom_logger.py
│   │   │   ├── data_utils.py
│   │   │   ├── date_timestamp_utils.py
│   │   │   ├── db_utility.py
│   │   │   ├── entities_registry.py
│   │   │   ├── entity_discovery.py
│   │   │   ├── env_utils.py
│   │   │   ├── exceptions.py
│   │   │   ├── filtering_utils.py
│   │   │   ├── generic_utilities.py
│   │   │   ├── log_context.py
│   │   │   ├── pagination_utils.py
│   │   │   ├── performance_utils.py
│   │   │   └── truncate_logging_utils.py
│   │   └── __init__.py
│   ├── __init__.py
│   └── pyproject.toml
├── docs/
│   ├── ci/
│   │   ├── README_ALLURE.md
│   │   ├── README_CI_ARCHITECTURE.md
│   │   ├── README_DOCKER_INFRASTRUCTURE.md
│   │   ├── README_ENV_AND_CI.md
│   │   ├── README_GITHUB_PRODUCTION_SETTINGS.md
│   │   └── README_GIT_WORKFLOW_HANDBOOK.md
│   ├── contributing/
│   │   ├── README_CHANGELOG_GUIDELINES.md
│   │   ├── README_CONTRIBUTING.md
│   │   └── README_PYPROJECT.md
│   ├── development/
│   │   ├── team-guides/
│   │   │   ├── README_COUPONS.md
│   │   │   ├── README_CUSTOMERS.md
│   │   │   └── README_PRODUCTS.md
│   │   ├── README_API_CLIENT.md
│   │   ├── README_ARCHITECTURE.md
│   │   ├── README_GRAPHQL_TESTING_GUIDE.md
│   │   ├── README_TEST_DATA_ARCHITECTURE.md
│   │   ├── README_TEST_DEVELOPMENT_GUIDE.md
│   │   ├── README_UI_TESTING_GUIDE.md
│   │   └── README_VALIDATORS.md
│   ├── framework/
│   │   ├── README_AUTHENTICATION.md
│   │   ├── README_CONFIG_CONTRACT.md
│   │   ├── README_ENTITY_DISCOVER_ARCHITECTURE_GUIDE.md
│   │   ├── README_ENVIRONMENT_CONFIG_GUIDE.md
│   │   ├── README_LOGGING_ARCHITECTURE.md
│   │   └── README_PLUGINS_REFERENCE.md
│   ├── getting-started/
│   │   ├── README_ARCHITECTURE_QUICK_START.md
│   │   ├── README_FRAMEWORK_OVERVIEW.md
│   │   └── README_QA_DEVELOPER_ONBOARDING.md
│   └── project-structure/
│       └── README_project_navigation.md
├── scripts/
│   ├── seed_test_products.sh
│   ├── seed_test_users.sh
│   ├── setup.sh
│   └── write_env_credentials.sh
├── tests/
│   ├── coupons/
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── test_create_coupons.py
│   │   │   └── test_get_coupon.py
│   │   ├── configs/
│   │   │   ├── Entity_Configuration_Guide.md
│   │   │   ├── __init__.py
│   │   │   └── config_coupons.py
│   │   ├── data/
│   │   │   └── __init__.py
│   │   ├── performance/
│   │   │   └── __init__.py
│   │   ├── __init__.py
│   │   └── conftest.py
│   ├── customers/
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── test_create_customer.py
│   │   │   ├── test_customer_deletion.py
│   │   │   ├── test_customer_filters.py
│   │   │   ├── test_e2e_customer_lifecycle.py
│   │   │   ├── test_get_all_customers.py
│   │   │   ├── test_get_customer.py
│   │   │   ├── test_soft_deleted_customer_handling.py
│   │   │   └── test_update_customer.py
│   │   ├── configs/
│   │   │   ├── Entity_Configuration_Guide.md
│   │   │   ├── __init__.py
│   │   │   └── config_customers.py
│   │   ├── data/
│   │   │   └── __init__.py
│   │   ├── performance/
│   │   │   ├── __init__.py
│   │   │   └── test_customer_performance.py
│   │   ├── __init__.py
│   │   └── conftest.py
│   ├── orders/
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── test_apply_valid_coupon_to_order.py
│   │   │   ├── test_create_order.py
│   │   │   ├── test_create_order_negative.py
│   │   │   ├── test_get_order.py
│   │   │   ├── test_orders_param_inside_module.py
│   │   │   ├── test_orders_params_using_json_file.py
│   │   │   └── test_update_order.py
│   │   ├── configs/
│   │   │   ├── README.md
│   │   │   ├── __init__.py
│   │   │   └── config_orders.py
│   │   ├── data/
│   │   │   ├── __init__.py
│   │   │   ├── coupon_scenarios.json
│   │   │   └── scenario_loader.py
│   │   ├── __init__.py
│   │   └── conftest.py
│   ├── products/
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── test_create_products.py
│   │   │   ├── test_create_products_negative.py
│   │   │   ├── test_get_products.py
│   │   │   ├── test_get_products_with_filter.py
│   │   │   └── test_update_product_price.py
│   │   ├── configs/
│   │   │   ├── Entity_Configuration_Guide.md
│   │   │   ├── __init__.py
│   │   │   └── config_products.py
│   │   ├── data/
│   │   │   └── __init__.py
│   │   ├── graphql/
│   │   │   ├── __init__.py
│   │   │   ├── test_create_product.py
│   │   │   ├── test_delete_product.py
│   │   │   ├── test_filter_products.py
│   │   │   ├── test_get_all_products.py
│   │   │   ├── test_get_product.py
│   │   │   ├── test_product_error_handling.py
│   │   │   ├── test_search_product.py
│   │   │   └── test_update_product.py
│   │   ├── performance/
│   │   │   ├── __init__.py
│   │   │   └── test_product_performance.py
│   │   ├── __init__.py
│   │   └── conftest.py
│   ├── shared/
│   │   ├── contracts/
│   │   │   ├── graphql/
│   │   │   ├── rest/
│   │   │   └── __init__.py
│   │   ├── preflight/
│   │   │   ├── README_PREFLIGHT.md
│   │   │   ├── __init__.py
│   │   │   └── test_logging_globals.py
│   │   ├── security/
│   │   │   ├── __init__.py
│   │   │   ├── test_authentication_matrix.py
│   │   │   └── test_authentication_success.py
│   │   ├── unit_tests/
│   │   │   ├── test_data_infrastructure/
│   │   │   └── __init__.py
│   │   └── __init__.py
│   ├── ui/
│   │   ├── components/
│   │   │   ├── __init__.py
│   │   │   └── site_header.py
│   │   ├── config/
│   │   │   ├── __init__.py
│   │   │   └── config_ui.py
│   │   ├── data/
│   │   │   ├── images/
│   │   │   ├── models/
│   │   │   └── __init__.py
│   │   ├── fixtures/
│   │   │   ├── __init__.py
│   │   │   ├── admin.py
│   │   │   ├── authentication.py
│   │   │   ├── browser.py
│   │   │   ├── customer_auth.py
│   │   │   └── resources.py
│   │   ├── pages/
│   │   │   ├── account/
│   │   │   ├── admin/
│   │   │   ├── authentication/
│   │   │   ├── catalog/
│   │   │   ├── common/
│   │   │   ├── shopping/
│   │   │   └── __init__.py
│   │   ├── tests/
│   │   │   ├── account/
│   │   │   ├── admin/
│   │   │   ├── auth/
│   │   │   ├── catalog/
│   │   │   ├── home/
│   │   │   ├── shopping/
│   │   │   └── __init__.py
│   │   ├── README.md
│   │   └── __init__.py
│   ├── README.md
│   ├── __init__.py
│   └── conftest.py
├── .dockerignore
├── .env
├── .env.example
├── .gitattributes
├── .gitignore
├── .gitlab-ci.yml
├── .pre-commit-config.yaml
├── CHANGELOG.md
├── Dockerfile
├── Makefile
├── README.md
├── conftest.py
├── docker-compose.wp.yml
└── pytest.ini
```

## 💡 Key Design Principles

| Principle | Benefit |
|-----------|---------|
| **Domain Ownership** | Each team owns their domain tests |
| **Shared Framework** | All tests use the same base infrastructure |
| **Clear Boundaries** | Framework code lives in `EcommerceAPI/`, tests in `tests/` |
| **Reusable Utilities** | `src/utils/` & `src/shared/` prevent duplication |
| **Scalability** | Easy to add new domains without affecting existing ones |
| **CI Separation** | Each test type has its own workflow |

---

## 🎯 Next Steps

- **Getting Started?** → Read [Framework Overview](../getting-started/README_FRAMEWORK_OVERVIEW.md)
- **Writing Tests?** → Read [Test Development Guide](../development/README_TEST_DEVELOPMENT_GUIDE.md) ⭐
- **Extending Framework?** → Read [Plugins Reference](../framework/README_PLUGINS_REFERENCE.md)
- **Setting Up CI?** → Read [CI Architecture](../ci/README_CI_ARCHITECTURE.md)
- **Need Full Tree?** → See [Full Project Tree](#-full-project-tree) above

---

**Happy testing! 🚀**

````
