# Configuration System Overview

This README explains how the project manages environments and configuration when each microservice owns its own API host configuration, while still using a single shared config loader and shared utilities (logging, reporting, api_client).

The design avoids hardcoding service names inside shared code and keeps sensitive data out of Git.

---

## High‑Level Principles

- Each microservice owns its own API_HOSTS
  - customers, orders, products, etc. define their own base URLs
- No shared utility imports config_customers, config_orders, etc. directly
  - Shared code is service‑agnostic
- Logging, reporting, api_client never care which service they run under
  - They only read environment selectors (ENV, MACHINE) and runtime context
- Secrets live only in `.env` or CI
  - No credentials or real DB details in service configs

---

## 1. .env File (Sensitive Runtime Data)

The `.env` file contains only secrets and selectors. It is never committed to Git.

Example `.env`:

```text
# --- Environment selection ---
ENV=test
MACHINE=machine1

# --- WooCommerce credentials ---
WC_KEY=ck_********
WC_SECRET=cs_********

# --- Database credentials (if used) ---
DB_USER=my_user
DB_PASSWORD=my_password

# --- Logging / reporting toggles ---
LOG_PAYLOADS=false
KEEP_STRUCTURED_LOGS=3
KEEP_HTML_REPORTS=3
```

Purpose
- Selects the active environment (test, dev, prod)
- Selects the active machine (machine1, docker, etc.)
- Stores only sensitive values (never committed)

---

## 2. Per‑Service Config Files (Non‑Sensitive)

Each microservice defines its own public API base URLs. These files are safe to commit because they contain no secrets.

Example directory layout:

```
tests/
├── customers/
│   └── configs/
│       └── config_customers.py
├── orders/
│   └── configs/
│       └── config_orders.py
├── products/
│   └── configs/
│       └── config_products.py
```

Example: `config_customers.py`

```python
# Public, non‑sensitive API endpoints for Customers service

API_HOSTS = {
    "test":    "http://localhost:8888/wp-json/wc/v3/customers",
    "staging": "https://staging.example.com/customers",
    "dev":     "https://dev.example.com/customers",
    "prod":    "https://api.example.com/customers",
}
```

Each service:
- Controls its own base URLs
- Can evolve independently
- Remains safe to commit

---

## 3. Shared `config_loader.py` (Service‑Agnostic)

The shared config loader:
- Loads `.env`
- Exposes only environment selectors
- Does not import any service config

Example `config_loader.py`:

```python
from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()

ENV = os.getenv("ENV", "test").lower()
MACHINE = os.getenv("MACHINE", "machine1").lower()

__all__ = ["ENV", "MACHINE"]
```

Why this is important
- Shared utilities stay clean
- No circular imports
- No service knowledge leaks into logging, reporting, or request layers

---

## 4. How the Correct Service Is Selected (Key Concept)

Shared utilities never decide the service. Instead, the service context is established higher up, typically via:
- `all_resources` fixture
- Service‑specific helpers / DAOs
- Test folder location (e.g. `tests/customers/...`)

Example usage in a service helper:

```python
from tests.customers.configs.config_customers import API_HOSTS
from EcommerceAPI.src.configs import ENV

BASE_URL = API_HOSTS.get(ENV, "")
```

That helper:
- Imports its own `config_<service>.API_HOSTS`
- Uses `ENV` from the shared loader
- Builds its own `BASE_URL`

This keeps ownership local and shared code generic.

---

## 5. APIClient Usage (No Hardcoding)

`APIClient` does not know about services. Helpers inject the correct base URL:

```python
req = APIClient(base_url=BASE_URL)
```

Benefits:
- Same `APIClient` works for every microservice
- No factory methods required
- No string service names hardcoded into shared code

---

## 6. Logging & Reporting Compatibility

Logging and reporting rely only on:
- `ENV`
- Runtime context (nodeid, correlation_id)

They automatically work across all services without modification. Reports are grouped by environment:

```
reports/
└── test/
    ├── html/
    └── logs/
```

---

## 7. Recommended Pattern Summary

Layer | Responsibility | Service‑Aware | Notes
--- | ---: | :---: | ---
`.env` | Secrets + selectors | ❌ | Never committed
`config_loader.py` | ENV + MACHINE | ❌ | Shared
`config_<service>.py` | API_HOSTS | ✅ | Owned by service
Helpers / DAOs | Build `base_url` | ✅ | Injected into utilities
`APIClient` | HTTP execution | ❌ | Reusable
Logging / Reporting | Observability | ❌ | Fully generic

---

## 8. Configuration Flow Diagram

```
 ┌──────────────┐
 │    .env      │  (ENV, MACHINE, secrets)
 └──────┬───────┘
        │
        ▼
 ┌──────────────────┐
 │ config_loader.py │  → ENV, MACHINE
 └──────┬───────────┘
        │
        ▼
 ┌───────────────────────────────┐
 │ Service Helper / DAO           │
 │ (customers / orders / etc.)   │
 │  - imports its own API_HOSTS  │
 │  - selects API_HOSTS[ENV]     │
 └──────┬────────────────────────┘
        │ base_url injected
        ▼
 ┌───────────────────────────────┐
 │ APIClient / Logger /     │
 │ Reporting (service‑agnostic)  │
 └───────────────────────────────┘
```

---

## 9. Key Benefits

- Zero hardcoded service names in shared code
- Clear ownership boundaries (service owns endpoints, shared code owns environment selectors)
- Easy onboarding for new microservices
- CI/CD friendly (secrets kept in CI or `.env`)
- Minimal coupling, maximal reuse

---

If you add a new microservice:
1. Create `tests/<service>/configs/config_<service>.py` with `API_HOSTS`.
2. Implement helpers/DAOs that import that `API_HOSTS`, read `ENV` from `config_loader`, and build `BASE_URL`.
3. Inject `BASE_URL` into `APIClient` and use shared logging/reporting as‑is.

This pattern keeps shared utilities generic, service ownership clear, and secrets out of the repository.
