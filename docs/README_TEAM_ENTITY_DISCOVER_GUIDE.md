# 🚀 TestEcommerceAPI - Team & Entity Discovery Architecture Guide

> Documentation explaining how Entities (Microservices), Teams, Logging, Allure, Fixtures, Runtime Resources, and CI Matrix execution work together.

---

# 📖 Table of Contents

1. Overview
2. Core Philosophy
3. Entity = Team = Microservice
4. Team Discovery
5. Entity Discovery
6. EntityBundle Architecture
7. Entities Registry
8. Shared API Resources
9. Allure Ownership
10. Structured Logging
11. CI/CD Matrix Strategy
12. Adding a New Entity
13. Future Architecture Vision
14. Single Source of Truth

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

Entity discovery powers runtime resources.

Unlike Team Discovery, it does not inspect tests.

Instead it scans framework modules.

Example:

```text
customers_helper.py
customers_api.py
customers_dao.py
```

If all required pieces exist:

```text
customers
```

is registered as an entity.

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

Current Enterprise Recommendation:

```yaml
matrix:
  entity:
    - customers
    - orders
    - products
    - coupons
```

Why explicit?

✅ Visible ownership

✅ Easier debugging

✅ Predictable CI behavior

✅ Stable reporting

✅ Stable permissions model

✅ Future deployment gates

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

Add CI matrix entry:

```yaml
- inventory
```

No framework modifications should be required.

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

# 🎯 Single Source of Truth Vision

Today several components determine ownership:

```text
team_discovery.py
entities.py
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
