# 🚀 TestEcommerceAPI - Team & Entity Discovery Architecture Guide

> Documentation explaining how Entities (Microservices), Teams, Logging, Allure, Fixtures, Runtime Resources, and CI Matrix execution work together.

---

# 📖 Table of Contents

1. Overview
2. Core Philosophy
3. Entity = Team = Microservice
4. Discovery Architecture
5. Entity Discovery (Test Ownership)
6. Framework Entity Discovery
7. Runtime Registry Discovery
8. EntityBundle Architecture
9. Entities Registry
10. Shared API Resources
11. Allure Ownership
12. Structured Logging
13. CI/CD Matrix Strategy
14. Adding a New Entity
15. Future Architecture Vision
16. Single Source of Truth

---

# 🎯 Overview

The framework is designed around a **Domain-Driven** Testing Architecture.

Each business domain represents:

- A Microservice
- An Entity
- An Owning Team
- A CI Ownership Boundary
- A Reporting Boundary

Examples:

| Entity | Team | Microservice |
|----------|----------|----------|
| customers | customers | Customers Service |
| orders | orders | Orders Service |
| products | products | Products Service |
| coupons | coupons | Coupons Service |
| shared | shared | Shared Platform Tests |

---

# 🏗️ Core Philosophy

For this framework:

```text
Business Entity
↓

Microservice
↓

Owning Team
↓

Logging

↓

Reporting

↓

CI Boundary
```

---

## 🧩 Current framework convention

Entity == Owning Team

Today each business entity is owned by a dedicated team.

This one-to-one relationship simplifies reporting, logging and CI ownership.

Future versions may allow a single team to own multiple entities without changing the framework architecture.

---

# 🏛️ Framework Discovery Architecture

The framework contains **three independent discovery mechanisms**.

Each one answers a different architectural question.

| Discovery | Question | Consumers |
|------------|----------|-----------|
| Entity Discovery | **Who owns this test?** | Logging, Allure, Reporting |
| Framework Entity Discovery | **What business domains belong to this framework?** | CI Matrix, Contract, Security, Documentation |
| Runtime Registry Discovery | **Build executable runtime resources.** | Fixtures, EntityBundle, Cross-domain access |

Although these mechanisms are independent, they all ultimately resolve to the same business entity.

Example:

```text
customers
```

represents:

- Business Entity
- Microservice
- Team
- CI Boundary
- Reporting Boundary

---

                         Test File
                             │
                             ▼
              extract_entity_from_nodeid()
                             │
                             ▼
                        customers
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
     Logging             Allure            Reporting


                 FRAMEWORK_ENTITIES
                             │
                             ▼
           discover_framework_entities()
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
        CI               Contract            Security


                  discover_entities()
                             │
                             ▼
                     Runtime Registry
                             │
                             ▼
                        EntityBundle
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
     entity_helper()      entity_dao()      all_resources


---
# 1. 🔍 Entity Discovery (Test Ownership)

**Source**

```text
src/utils/team_discovery.py
```

Entity Discovery determines **which business entity owns a test**.

The framework derives the entity directly from the pytest nodeid.

Example

```text
tests/customers/api/test_create_customer.py
                    │
                    ▼
extract_entity_from_nodeid()
                    │
                    ▼
               customers
```

The convention is intentionally simple:

```text
tests/<entity>/...
```

The first directory immediately below `tests/` determines the entity.

Examples

| Test Path | Entity |
|-----------|---------|
| tests/customers/api/test_x.py | customers |
| tests/orders/api/test_x.py | orders |
| tests/products/api/test_x.py | products |
| tests/shared/preflight/test_x.py | shared |

### Purpose

This discovery mechanism identifies **ownership**.

It is used by:

- Structured logging
- Allure reporting
- Reporting
- Future notifications

It does **not** inspect the framework implementation and performs no runtime initialization.

---

# 2. 🗂️ Framework Entity Discovery

**Source**

```text
src/metadata/entity_metadata.py
```

Framework Entity Discovery defines **which business domains officially belong to the framework**.

Unlike runtime discovery, it does **not** inspect helpers, APIs or DAOs.

Instead, the framework maintains an explicit architectural registry.

```python
FRAMEWORK_ENTITIES = (
    "customers",
    "orders",
    "products",
    "coupons",
)
```

The registry is intentionally explicit.

Adding a new business entity is considered an architectural change and therefore becomes visible during code review.


### Purpose

Framework Entity Discovery is consumed by:

- GitHub Actions matrix generation
- Contract test suites
- Security test suites
- Documentation

This registry represents **framework architecture**, not runtime implementation.

> **Naming convention**
>
> Framework entity identifiers are lowercase, singular architectural
> identifiers without hyphens (for example `customers`, `orders`,
> `products`, `coupons`).
>
> This convention is relied upon by the CI/CD workflows when constructing
> artifact names and GitHub Pages report paths.
>
> Introducing hyphens into entity identifiers would require updating the
> artifact naming and parsing strategy.

---

# 3. ⚙️ Runtime Registry Discovery

**Source**

```text
plugins/entities.py
```

Runtime Registry Discovery builds the executable resources required during test execution.

Unlike Framework Entity Discovery, it performs runtime initialization.

For every implemented entity it creates:

```text
API Client
      │
      ▼
API
      │
      ▼
Helper
      │
      ▼
DAO
      │
      ▼
EntityBundle
```

Every successfully initialized entity is wrapped into an **EntityBundle** and registered in the runtime registry.

Tests can then access entities through a single unified interface.

Example:

```python
all_resources.customers.helper

entity_helper("customers")

entity_dao("customers")
```

### Runtime validation

During initialization the framework validates that every runtime component exists.

Entities that cannot be initialized are skipped and reported.

Example:

```text
🔍 ENTITY DISCOVERY SUMMARY

customers   READY
orders      SKIPPED (missing API)
products    SKIPPED (missing DAO)
coupons     SKIPPED (missing API)
```

This diagnostic information is produced during runtime registry construction and greatly simplifies troubleshooting.

---

# 📦 EntityBundle Architecture

Each discovered entity becomes:

```python
EntityBundle(
    helper,
    dao,
    delete_method
)
```

Example:

```python
customers
```

becomes:

```python
EntityBundle(
    helper=CustomersHelper,
    dao=CustomersDAO,
    delete_method=CustomersApi.delete
)
```

---

# ✅ Runtime Implementation Requirements

Required modules:

```text
<entity>_helper.py
<entity>_api.py
<entity>_dao.py
```

Example:

```text
customers_helper.py
customers_api.py
customers_dao.py
```

If any component is missing:

❌ Entity skipped

The framework logs the reason.

---

# 🗂️ Entities Registry

Source:

```text
entities_registry.py
```

Purpose:

Wrap discovered entities.

Supports:

Dictionary access:

```python
entities["customers"]
```

Attribute access:

```python
entities.customers
```

Benefits:

- Cleaner syntax
- Better readability
- Type-safe access
- Centralized registry

---

# 🔗 Shared API Resources

Fixture:

```python
shared_api_resources
```

Provides:

- Helpers
- DAOs
- API Clients
- Cleanup Registration

Examples:

```python
shared_api_resources["customers_helper"]
```

or

```python
all_resources.customers.helper
```

---

# 🤝 Cross-Team Access

One team can access another entity safely.

Example:

```python
entity_helper("customers")
```

allows:

```text
orders tests
    ↓
customer helper
```

without importing customer fixtures directly.

Benefits:

- No fixture leakage
- Better encapsulation
- Cleaner dependency management

---

# 📊 Allure Ownership Tracking

Source:

```text
allure_autogen.py
```

Team ownership is derived automatically.

Example:

```text
tests/customers/...
            ↓
        customers
```

Executed teams are collected during runtime.

Example:

```text
customers
orders
products
```

Allure Environment Tab receives:

```text
teams=customers,orders,products
```

automatically.

---

# 📝 Structured Logging

Source:

```text
log_context.py
```

Context Variables:

```python
correlation_id
test_nodeid
```

Ownership Flow:

```text
test_nodeid
     ↓
team discovery
     ↓
entity ownership
     ↓
log routing
```

Example:

```text
reports/logs/customers/
reports/logs/orders/
reports/logs/products/
reports/logs/coupons/
```

---

# 🧪 Test Ownership vs Entity Registration

Important:

Creating:

```text
tests/customers/
```

does NOT register an entity.

Entity registration requires:

```text
customers_helper.py
customers_api.py
customers_dao.py
```

Therefore:

Test ownership and runtime entity registration are related but technically independent.

---

# ⚙️ CI/CD Matrix Strategy

The CI pipeline does **not** maintain its own list of entities.

Instead it consumes the framework architecture.

```text
FRAMEWORK_ENTITIES
        │
        ▼
discover_framework_entities()
        │
        ▼
generate_matrix.py
        │
        ▼
GitHub Actions Matrix
```

Every supported business entity automatically participates in:

- Smoke
- Integration
- Regression
- Performance

Shared framework suites (Preflight, Contract and Security) execute independently from the entity matrix.

This keeps CI aligned with the framework architecture while avoiding duplicated configuration across workflows.

---

# 🚦 CI Ownership Model

Each matrix entry represents:

```text
customers
    ↓
Entity
    ↓
Owning Team
    ↓
Deployment Boundary
    ↓
Reporting Boundary
```

This is why:

```yaml
entity: customers
```

is much more than simply selecting tests.

---

# ➕ Adding a New Entity

Introducing a new business entity is an architectural change.

### Step 1

Register the entity in the framework architecture.

```python
FRAMEWORK_ENTITIES = (
    ...
    "inventory",
)
```

### Step 2

(Optional)

Override metadata when required.

```python
ENTITY_METADATA = {
    "inventory": {
        "tier": "critical",
    },
}
```

### Step 3

Implement the runtime components.

```text
inventory_helper.py
inventory_api.py
inventory_dao.py
```

### Step 4

Create the test suite.

```text
tests/inventory/
```

No GitHub Actions workflow needs to be modified.

The framework automatically generates the CI matrix from the architectural registry.

---

# 🔮 Future Enterprise Evolution

Potential future metadata:

```yaml
matrix:
  include:
    - entity: customers
      owner: customers-team
      criticality: high

    - entity: coupons
      owner: promotions-team
      criticality: low
```

Benefits:

- 📣 Slack notifications
- 🔁 Selective retries
- 🚧 Deployment gates
- 🧪 Flaky-test quarantine
- 📊 Team dashboards


---
# 🚀 Dynamic CI Matrix

The framework owns entity discovery.

GitHub Actions consumes that information rather than maintaining its own list of entities.

Architecture:

```
FRAMEWORK_ENTITIES
        │
        ▼
discover_framework_entities()
        │
        ▼
generate_matrix.py
        │
        ▼
GitHub Actions Matrix

```

This approach eliminates duplicated configuration, keeps CI aligned with the framework, and allows new entities to participate in the pipeline without modifying workflow YAML files.

---

# 🎯 Single Source of Truth Vision

Today ownership and execution are intentionally separated.

```
Ownership

↓

extract_entity_from_nodeid()

Framework

↓

FRAMEWORK_ENTITIES

Runtime

↓

discover_entities()
```

---

# 🏁 Summary

The framework intentionally separates three different discovery mechanisms.

## 1. Entity Discovery

Determines **who owns a test**.

Used by:

- Logging
- Allure
- Reporting

---

## 2. Framework Entity Discovery

Determines **which business domains belong to the framework**.

Used by:

- CI Matrix
- Contract
- Security
- Documentation

---

## 3. Runtime Registry Discovery

Builds executable runtime resources.

Used by:

- EntityBundle
- Shared fixtures
- Cross-domain helpers
- Automatic cleanup

---

Together these mechanisms provide a clear separation between:

- **Test ownership**
- **Framework architecture**
- **Runtime execution**

This separation keeps the framework maintainable, scalable and suitable for multi-team development while avoiding
duplicated configuration and hidden runtime behaviour.
