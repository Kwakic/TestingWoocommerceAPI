# 📁 Project Structure Guide

Quick navigation to understand what each directory does and where to find related documentation.

---

## 🏗️ Core Areas

### 📚 **Docs/** — Documentation Hub
Your single source of truth for learning the framework.

| Directory | Purpose | Start Here |
|-----------|---------|-----------|
| **getting-started/** | Onboarding & overview | [Framework Overview](../getting-started/README_FRAMEWORK_OVERVIEW.md) |
| **development/** | How to write tests & extend the framework | [Test Development Guide](../development/README_TEST_DEVELOPMENT_GUIDE.md) ⭐ |
| **framework/** | Technical deep-dives on plugins, auth, config | [Plugins Reference](../framework/README_PLUGINS_REFERENCE.md) |
| **ci/** | CI/CD pipeline design & workflows | [CI Architecture](../ci/README_CI_ARCHITECTURE.md) |
| **contributing/** | Contributing, changelog, packaging | [Contributing Guide](../contributing/README_CONTRIBUTING.md) |
| **project-structure/** | This directory structure explained | ← You are here |

---

### 🔧 **EcommerceAPI/** — Shared Framework Package
Installable Python package that all tests depend on.

**Key Responsibility:** Provide reusable test infrastructure (fixtures, API client, auth, DB utilities)

| Subdirectory | What It Does |
|--------------|-------------|
| **plugins/** | pytest plugin system (fixtures for each domain) |
| **src/auth/** | OAuth1, OAuth2, JWT, basic auth implementations |
| **src/configs/** | Environment & runtime configuration loaders |
| **src/core/** | HTTP transport layer (requests wrapper) |
| **src/clients/** | High-level API client for orchestrating requests |
| **src/{domain}/** | Domain-specific DAOs, APIs, validators, models |
| **src/shared/** | Reusable assertions, helpers, utilities |
| **src/utils/** | Generic utilities (logging, date parsing, DB ops) |

👉 **When to edit:** Framework-wide changes, shared fixtures, new auth schemes
👉 **See also:** [API Client Guide](../development/README_API_CLIENT.md), [Plugins Reference](../framework/README_PLUGINS_REFERENCE.md)

---

### 🧪 **Tests/** — Domain-Driven Test Suites
Each business entity owns its own test suite.

| Domain | Test Types | Team Guide |
|--------|-----------|-----------|
| **customers/** | Smoke, integration, regression, performance | [Customers Guide](../development/TEAM_GUIDES/README_CUSTOMERS.md) |
| **products/** | Smoke, integration, regression, performance | [Products Guide](../development/TEAM_GUIDES/README_PRODUCTS.md) |
| **orders/** | Smoke, integration, regression, performance | [Orders Guide](../development/TEAM_GUIDES/README_ORDERS.md) |
| **coupons/** | Smoke, integration, regression, performance | [Coupons Guide](../development/TEAM_GUIDES/README_COUPONS.md) |
| **shared/** | Framework-level validation (contracts, security, preflight) | — |

**Structure of each domain:**
