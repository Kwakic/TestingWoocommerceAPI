# 🚀 TestEcommerceAPI - Team & Entity Discovery Architecture Guide

> Documentation explaining how Entities (Microservices), Teams, Logging, Allure, Fixtures, Runtime Resources, and CI Matrix execution work together.

---

# 📖 Table of Contents

1. Overview
2. Core Philosophy
3. Entity = Team = Microservice
4. Team Discovery
5. Entity Discovery
6. Discovery Architecture Overview
7. EntityBundle Architecture
8. Entities Registry
9. Shared API Resources
10. Allure Ownership
11. Structured Logging
12. CI/CD Matrix Strategy
13. Adding a New Entity
14. Future Architecture Vision
15. Single Source of Truth

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
customers
    ↓
Entity
    ↓
Microservice
    ↓
Owning Team
    ↓
Logging Ownership
    ↓
Allure Ownership
    ↓
CI Matrix Ownership
```

Important:

✅ Entity = Team

The team is derived from the microservice/entity.

This keeps ownership consistent across the framework.

---

# 🔍 Team Discovery

Source:

```text
team_discovery.py
```

Team discovery is used primarily by:

- Allure Reporting
- Structured Logging
- Ownership Tracking
- Future Notifications

The framework extracts the team from the pytest nodeid.

Example:

```text
tests/customers/api/test_create_customer.py
                    ↓
                customers
```

Rule:

```text
tests/<entity>/...
```

The first folder below tests determines ownership.

Examples:

| Test Path | Team |
|------------|------------|
| tests/customers/api/test_x.py | customers |
| tests/orders/api/test_x.py | orders |
| tests/products/api/test_x.py | products |
| tests/shared/utils/test_x.py | shared |

---

# 🧩 Entity Discovery

Source:

```text
entities.py
```

Entity discovery is the framework's **Single Source of Truth** for supported
business entities.

Unlike Team Discovery, it does not inspect the test suite.

Instead it discovers entities by scanning the framework implementation itself.

A valid entity requires a complete framework implementation:

```text
<entity>_helper.py
<entity>_api.py
<entity>_dao.py
```

Only fully implemented entities are exposed to the rest of the framework.

Current consumers include:

- Runtime resource discovery
- GitHub Actions dynamic matrix generation
- Contract test suites
- Security test suites
- Future framework tooling

---
## 🏛️ Discovery Architecture Overview

Although the framework contains multiple discovery mechanisms, they all ultimately resolve to the same ownership model.

### Ownership Model

```text
customers
    ↓
Entity
    ↓
Microservice
    ↓
Owning Team
```

The framework intentionally treats:

```text
Entity = Team = Microservice
```

Examples:

| Entity    | Team      | Microservice          |
| --------- | --------- | --------------------- |
| customers | customers | Customers Service     |
| orders    | orders    | Orders Service        |
| products  | products  | Products Service      |
| coupons   | coupons   | Coupons Service       |
| shared    | shared    | Shared Platform Tests |

---

## 🔍 Discovery Flows

The framework currently contains two discovery systems.

#### 1️⃣ Team Discovery

Used by:

* Allure Reporting
* Structured Logging
* Ownership Tracking
* Reporting

Flow:

```text
tests/customers/api/test_create_customer.py
                    ↓
             pytest nodeid
                    ↓
         extract_team_from_nodeid()
                    ↓
                customers
```

Result:

```text
customers
```

becomes the owner for:

* Allure metadata
* Structured logs
* Future notifications
* Reporting

---

#### 2️⃣ Entity Discovery

Used by:

- Runtime resources
- Generic fixtures
- Contract test suites
- Security test suites
- GitHub Actions dynamic matrix

Flow:

```text
customers_helper.py
customers_api.py
customers_dao.py
          │
          ▼
discover_entity_names()
          │
          ├── GitHub Actions Matrix
          ├── Contract Tests
          ├── Security Tests
          └── discover_entities()
                     │
                     ▼
                EntityBundle
```

This lightweight discovery mechanism allows multiple framework components
to enumerate supported entities without instantiating helpers, DAOs or API
clients.


---

### Why Two Discovery Systems?

At first glance they appear duplicated.

However, they solve different problems.

Team Discovery answers:


```text
Who owns this test?
```

Entity Discovery answers:

```text
What runtime resources are available?
```

Both ultimately resolve to:

```text
customers
orders
products
coupons
shared
```

which keeps ownership consistent across the framework.

---

### Complete Ownership Flow

```text
customers
     │
     ├── tests/customers/
     │         ↓
     │   Team Discovery
     │         ↓
     │  Allure + Logging
     │
     ├── customers_helper.py
     ├── customers_api.py
     ├── customers_dao.py
     │         ↓
     │   Entity Discovery
     │         ↓
     │   EntityBundle
     │
     └── CI Matrix
               ↓
      entity: customers
```

Every layer of the framework therefore points to the same ownership domain:

```text
customers
```

which enables consistent:

* Reporting
* Logging
* Resource discovery
* CI execution
* Future deployment gates
* Future team notifications



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

# ✅ Entity Registration Requirements

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

```text
Framework
     │
     ▼
discover_entity_names()
     │
     ▼
.github/scripts/generate_matrix.py
     │
     ▼
{
  "include": [
    {
      "entity": "customers",
      "team": "customers",
      "tier": "critical"
    }
  ]
}
     │
     ▼
GitHub Actions Matrix
     │
     ├── Test • customers
     └── Publish Report • customers
```
The CI pipeline never maintains a hardcoded list of entities.

The framework is the single source of truth. Every workflow dynamically builds its execution matrix by calling
`discover_entity_names()` through `.github/scripts/generate_matrix.py`.

---

## 🔗 Shared Framework Discovery

Entity discovery is not limited to GitHub Actions.

The same discovery mechanism is reused throughout the framework wherever
all supported entities must be enumerated.

Examples:

```python
discover_entity_names()
```

Current consumers include:

- GitHub Actions matrix generation
- Contract test suites
- Security test suites

This avoids maintaining duplicated entity lists and ensures that adding a
new entity automatically expands both CI execution and shared framework
validation.


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

Example:

```text
inventory
```

Step 1:

Create framework modules:

```text
inventory_helper.py
inventory_api.py
inventory_dao.py
```

Step 2:

Create tests:

```text
tests/inventory/
```

Step 3:

```text
Push the changes.

No CI workflow modifications are required.

The framework automatically discovers the new entity and the GitHub Actions matrix is generated dynamically.
```
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
Framework
        │
        ▼
discover_entity_names()
        │
        ▼
generate_matrix.py
        │
        ▼
Dynamic GitHub Actions Matrix
        │
        ├── Test
        └── Publish Report

```

This approach eliminates duplicated configuration, keeps CI aligned with the framework, and allows new entities to participate in the pipeline without modifying workflow YAML files.

---

# 🎯 Single Source of Truth Vision

Today several components determine ownership:

```text
team_discovery.py
discover_entity_names()
discover_entities()
config_loader.detect_service()
CI matrix entity
```

All ultimately answer:

```text
What entity am I executing?
```

Long-term vision:

```python
get_current_entity()
```

used consistently by:

- Logging
- Allure
- Reporting
- Runtime Resources
- CI Metadata

---

# 🏁 Summary

The framework follows a single ownership model:

```text
Entity
   =
Microservice
   =
Owning Team
```

Everything else is derived from that:

- Tests
- Logging
- Allure
- Runtime Resources
- CI/CD
- Reporting

This alignment is what enables the framework to scale cleanly across multiple microservices and teams.
