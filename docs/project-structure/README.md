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
│   │   ├── shared.py                 ← API client infrastructure
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
│   │   ├── config_loader.py          ← Load environment configs
│   │   ├── runtime_config.py         ← Runtime configuration
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
│   ├── core/                         ← HTTP transport layer
│   │   ├── http_client.py            ← Low-level requests wrapper
│   │   ├── http_response.py          ← Response object model
│   │   ├── request_context.py        ← Request context tracking
│   │   └── __init__.py
│   │
│   ├── clients/                      ← High-level API orchestration
│   │   ├── api_client.py             ← Main API client (uses http_client)
│   │   └── __init__.py
│   │
│   ├── customers/                    ← Domain: Customers
│   │   ├── dao/                      ← Data access & business logic
│   │   │   ├── customers_dao.py
│   │   │   └── __init__.py
│   │   ├── api/                      ← Domain API wrapper
│   │   │   ├── customers_api.py
│   │   │   └── __init__.py
│   │   ├── validators/               ← Custom validators
│   │   │   ├── customer_db_validators.py
│   │   │   ├── customer_validators.py
│   │   │   └── __init__.py
│   │   ├── models/                   ← Pydantic models (runtime validation)
│   │   │   ├── customer_model.py
│   │   │   └── __init__.py
│   │   └── helpers/                  ← Business & API logic
│   │       ├── customers_helper.py
│   │       └── __init__.py
│   │
│   ├── products/                     ← Domain: Products (same structure)
│   ├── orders/                       ← Domain: Orders (same structure)
│   ├── coupons/                      ← Domain: Coupons (same structure)
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

- **Add new domain?** → Create `src/{domain}/` with DAOs, APIs, validators, models
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
│   ├── api/
│   │   ├── test_create_customer.py
│   │   ├── test_customer_deletion.py
│   │   ├── test_customer_filters.py
│   │   ├── test_e2e_customer_lifecycle.py
│   │   ├── test_get_all_customers.py
│   │   ├── test_get_customer.py
│   │   ├── test_soft_deleted_customer_handling.py
│   │   ├── test_update_customer.py
│   │   └── __init__.py
│   └── performance/
│       ├── test_customer_performance.py
│       └── __init__.py
│
├── products/                         ← Domain: Products (same structure)
├── orders/                           ← Domain: Orders (same structure)
├── coupons/                          ← Domain: Coupons (same structure)
│
├── shared/                           ← Framework-level tests (run once)
│   ├── __init__.py
│   ├── contracts/                    ← Contract testing (response schemas)
│   │   ├── error_schema.py           ← Error response contracts
│   │   ├── test_response_format.py   ← Validate response format
│   │   ├── test_api_connectivity.py  ← Basic connectivity checks
│   │   └── __init__.py
│   ├── security/                     ← Security & auth validation
│   │   ├── test_authentication_matrix.py ← Auth scheme matrix
│   │   ├── test_authentication_success.py ← Successful auth scenarios
│   │   └── __init__.py
│   └── preflight/                    ← Pre-test checks
│       ├── test_logging_globals.py   ← Logging validation
│       ├── __init__.py
│       └── README_PREFLIGHT.md
│
├── __init__.py
├── conftest.py                       ← Shared root fixtures
└── README.md                          ← Test suite documentation
```

### 📋 Test Types per Domain

Each domain (`customers/`, `products/`, `orders/`, `coupons/`) contains:

| Test Type | Location | Examples |
|-----------|----------|----------|
| **Smoke** | `api/` | Create, read, delete basic operations |
| **Integration** | `api/` | Multi-step workflows, cross-entity tests |
| **Regression** | `api/` | Bug fixes, edge cases, known issues |
| **Performance** | `performance/` | Load tests, response times, bulk ops |

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
│   ├── generate_matrix.py            ← Generate test matrix
│   └── portal/
│       ├── style.css                 ← Portal styling
│       └── generate_portal.py        ← Generate Allure portal
└── portal/                           ← Allure portal configuration
    ├── style.css
    └── generate_portal.py
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
└── write_env_credentials.sh          ← Environment credential setup
```

### 📝 When to Edit

- Add new setup or utility scripts here

---

## 📦 **Root Configuration Files**

Project-level configuration and orchestration.

| File | Purpose |
|------|---------|
| **Makefile** | Orchestrates common tasks (`make run`, `make test`, etc.) |
| **pytest.ini** | pytest configuration & marker definitions |
| **conftest.py** | Shared root-level fixtures & hooks |
| **.env** | Local environment variables & credentials |
| **.env.example** | Template for `.env` file |
| **docker-compose.matrix.yml** | Multi-container setup (WordPress, WooCommerce, MySQL) |
| **Dockerfile** | Container image for CI/CD execution |
| **README.md** | Project landing page & documentation index |
| **.gitignore** | Git ignore rules |
| **CHANGELOG.md** | Project changelog |
| **pyproject.toml** | Python project metadata (in EcommerceAPI/) |

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

```
TestEcommerceAPI (Root)
│
├── .git/
├── .venv/                                       ← Virtual environment (optional)
│
├── 📚 docs/
│   ├── getting-started/
│   │   ├── README_FRAMEWORK_OVERVIEW.md
│   │   ├── README_QA_DEVELOPER_ONBOARDING.md
│   │   └── README_ARCHITECTURE_QUICK_START.md
│   ├── development/
│   │   ├── README_TEST_DEVELOPMENT_GUIDE.md    ⭐ Canonical guide
│   │   ├── README_API_CLIENT.md
│   │   ├── README_ARCHITECTURE.md
│   │   ├── README_VALIDATORS.md
│   │   └── team-guides/
│   │       ├── README_CUSTOMERS.md
│   │       ├── README_ORDERS.md
│   │       ├── README_COUPONS.md
│   │       └── README_PRODUCTS.md
│   ├── framework/
│   │   ├── README_PLUGINS_REFERENCE.md
│   │   ├── README_ENVIRONMENT_CONFIG_GUIDE.md
│   │   ├── README_CONFIG_CONTRACT.md
│   │   ├── README_AUTHENTICATION.md
│   │   ├── README_LOGGING_ARCHITECTURE.md
│   │   └── README_ENTITY_DISCOVER_ARCHITECTURE_GUIDE.md
│   ├── ci/
│   │   ├── README_CI_ARCHITECTURE.md
│   │   ├── README_ALLURE.md
│   │   ├── README_ENV_AND_CI.md
│   │   ├── README_DOCKER_INFRASTRUCTURE.md
│   │   └── README_GIT_WORKFLOW_HANDBOOK.md
│   ├── contributing/
│   │   ├── README_CONTRIBUTING.md
│   │   ├── README_CHANGELOG_GUIDELINES.md
│   │   └── README_PYPROJECT.md
│   └── project-structure/
│       └── README.md                           ← You are here
│
├── 🔧 EcommerceAPI/                            ← Shared Framework
│   ├── plugins/
│   │   ├── api/
│   │   │   ├── shared.py
│   │   │   ├── customers.py
│   │   │   ├── products.py
│   │   │   ├── coupons.py
│   │   │   └── orders.py
│   │   ├── config_pytest.py
│   │   ├── allure_autogen.py
│   │   ├── api_fixtures.py
│   │   ├── db_fixtures.py
│   │   ├── entities.py
│   │   ├── entity_metadata.py
│   │   ├── reporting.py
│   │   ├── logging_plugin.py
│   │   └── README_plugins.md
│   ├── src/
│   │   ├── metadata/
│   │   │   ├── entity_metadata.py
│   │   │   ├── runtime_metadata.py
│   │   │   ├── deployment_metadata.py
│   │   │   └── __init__.py
│   │   ├── configs/
│   │   │   ├── config_loader.py
│   │   │   ├── runtime_config.py
│   │   │   ├── README.md
│   │   │   └── __init__.py
│   │   ├── auth/
│   │   │   ├── base_auth.py
│   │   │   ├── oauth1_auth.py
│   │   │   ├── oauth2_auth.py
│   │   │   ├── jwt_auth.py
│   │   │   ├── basic_auth.py
│   │   │   ├── auth_factory.py
│   │   │   ├── auth_resolver.py
│   │   │   └── __init__.py
│   │   ├── core/
│   │   │   ├── http_client.py
│   │   │   ├── http_response.py
│   │   │   ├── request_context.py
│   │   │   └── __init__.py
│   │   ├── clients/
│   │   │   ├── api_client.py
│   │   │   └── __init__.py
│   │   ├── customers/
│   │   │   ├── dao/
│   │   │   │   ├── customers_dao.py
│   │   │   │   └── __init__.py
│   │   │   ├── api/
│   │   │   │   ├── customers_api.py
│   │   │   │   └── __init__.py
│   │   │   ├── validators/
│   │   │   │   ├── customer_db_validators.py
│   │   │   │   ├── customer_validators.py
│   │   │   │   └── __init__.py
│   │   │   ├── models/
│   │   │   │   ├── customer_model.py
│   │   │   │   └── __init__.py
│   │   │   └── helpers/
│   │   │       ├── customers_helper.py
│   │   │       └── __init__.py
│   │   ├── products/
│   │   ├── orders/
│   │   ├── coupons/
│   │   ├── shared/
│   │   │   ├── assertions/
│   │   │   │   ├── common_assertions.py
│   │   │   │   └── __init__.py
│   │   │   ├── api/
│   │   │   │   ├── common_api.py
│   │   │   │   └── __init__.py
│   │   │   └── helpers/
│   │   │       ├── cleanup_helpers.py
│   │   │       └── __init__.py
│   │   ├── manual_cleanup_scripts/
│   │   ├── utils/
│   │   │   ├── bulk_ops.py
│   │   │   ├── credentials_utility.py
│   │   │   ├── custom_logger.py
│   │   │   ├── data_utils.py
│   │   │   ├── date_timestamp_utils.py
│   │   │   ├── db_utility.py
│   │   │   ├── entities_registry.py
│   │   │   ├── env_utils.py
│   │   │   ├── exceptions.py
│   │   │   ├── filtering_utils.py
│   │   │   ├── generic_utilities.py
│   │   │   ├── log_context.py
│   │   │   ├── pagination_utils.py
│   │   │   ├── performance_utils.py
│   │   │   ├── entity_discovery.py
│   │   │   ├── truncate_logging_utils.py
│   │   │   └── __init__.py
│   │   └── __init__.py
│   ├── __init__.py
│   └── pyproject.toml
│
├── 🧪 tests/
│   ├── customers/
│   │   ├── configs/
│   │   │   ├── config_customers.py
│   │   │   ├── __init__.py
│   │   │   └── Entity_Configuration_Guide.md
│   │   ├── data/
│   │   │   ├── __init__.py
│   │   │   └── create_customer_payload.json
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── api/
│   │   │   ├── test_create_customer.py
│   │   │   ├── test_customer_deletion.py
│   │   │   ├── test_customer_filters.py
│   │   │   ├── test_e2e_customer_lifecycle.py
│   │   │   ├── test_get_all_customers.py
│   │   │   ├── test_get_customer.py
│   │   │   ├── test_soft_deleted_customer_handling.py
│   │   │   ├── test_update_customer.py
│   │   │   └── __init__.py
│   │   └── performance/
│   │       ├── test_customer_performance.py
│   │       └── __init__.py
│   ├── products/
│   ├── orders/
│   │   ├── configs/
│   │   │   ├── config_orders.py
│   │   │   ├── __init__.py
│   │   │   └── Entity_Configuration_Guide.md
│   │   ├── data/
│   │   │   ├── __init__.py
│   │   │   └── create_order_payload.json
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── README.md
│   │   ├── api/
│   │   │   ├── test_apply_valid_coupon_to_order.py
│   │   │   ├── test_create_order_smoke.py
│   │   │   ├── test_orders_param_inside_module.py
│   │   │   ├── test_orders_params_using_json_file.py
│   │   │   ├── test_update_order.py
│   │   │   └── __init__.py
│   │   └── performance/
│   │       ├── test_order_performance.py
│   │       └── __init__.py
│   ├── coupons/
│   ├── shared/
│   │   ├── __init__.py
│   │   ├── contracts/
│   │   │   ├── error_schema.py
│   │   │   ├── test_response_format.py
│   │   │   ├── test_api_connectivity.py
│   │   │   └── __init__.py
│   │   ├── security/
│   │   │   ├── test_authentication_matrix.py
│   │   │   ├── test_authentication_success.py
│   │   │   └── __init__.py
│   │   └── preflight/
│   │       ├── test_logging_globals.py
│   │       ├── __init__.py
│   │       └── README_PREFLIGHT.md
│   ├── __init__.py
│   ├── conftest.py
│   └── README.md
│
├── 📊 reports/
│   ├── allure-report/
│   │   ├── data/
│   │   ├── export/
│   │   ├── history/
│   │   ├── plugins/
│   │   ├── widgets/
│   │   ├── app.js
│   │   ├── favicon.ico
│   │   ├── index.html
│   │   └── style.css
│   ├── allure-results/
│   │   ├── *.json
│   │   ├── categories.json
│   │   ├── environment.properties
│   │   └── etc.
│   └── logs/
│       ├── customers/
│       │   ├── docker/
│       │   │   └── test_debug_structured_*.jsonl
│       │   └── test/
│       │       └── test_debug_structured_*.jsonl
│       ├── products/
│       │   └── test/
│       │       └── test_debug_structured_*.jsonl
│       └── shared/
│           ├── dev/
│           │   └── test_debug_structured_*.jsonl
│           └── test/
│               └── test_debug_structured_*.jsonl
│
├── ⚙️ .github/
│   ├── workflows/
│   │   ├── smoke.yml
│   │   ├── integration.yml
│   │   ├── regression.yml
│   │   ├─�� performance.yml
│   │   ├── contract.yml
│   │   ├── preflight.yml
│   │   ├── security.yml
│   │   ├── dashboard-publisher.yml
│   │   ├── reusable-test-runner.yml
│   │   └── reusable-allure-report.yml
│   ├── actions/
│   │   ├── setup-python-project/
│   │   │   └── action.yml
│   │   ├── configure-ci-env/
│   │   │   └── action.yml
│   │   ├── docker-cleanup/
│   │   │   └── action.yml
│   │   └── setup-woocommerce/
│   │       └── action.yml
│   ├── scripts/
│   │   └── generate_matrix.py
│   └── portal/
│       ├── style.css
│       └── generate_portal.py
│
├── 🛠️ scripts/
│   ├── setup.sh
│   └── write_env_credentials.sh
│
├── wp-data/
│
├── 📦 Root Configuration
│   ├── Makefile
│   ├── pytest.ini
│   ├── conftest.py
│   ├── .env
│   ├── .env.example
│   ├── docker-compose.matrix.yml
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── .gitignore
│   ├── .gitattributes
│   ├── .gitlab-ci.yml
│   ├── .pre-commit-config.yaml
│   ├── README.md
│   └── CHANGELOG.md
│
└── .git/
```

---

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
