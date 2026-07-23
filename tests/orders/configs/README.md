# Configuration System Overview

This README explains how the project manages environments, configuration files, and dynamic selection of hosts, credentials, and databases using:

- `.env` file (sensitive variables)
- `hosts_config.py` (non-sensitive mappings)
- `config_loader.py` (dynamic configuration selector)

This structure ensures a clean separation between secrets and public configuration, supports multiple machines, and enables easy switching between `test`, `dev`, and `prod` environments.

---

## 1. `.env` File (Sensitive Data)

The `.env` file contains **private credentials and selectors** that must never be committed to Git. Example:

```bash
# --- Environment and machine ---
API_ENV=test
MACHINE=machine1

# --- WooCommerce API credentials ---
WC_KEY=ck_******
WC_SECRET=cs_******

# --- Database credentials ---
DB_USER=my_user
DB_PASSWORD=my_password

# --- System settings ---
PYTHONIOENCODING=utf-8
```

### Purpose

- Defines which environment is currently active (`test`, `dev`, `prod`).
- Stores credentials that must remain secret.

### Switching Environment

You can temporarily override the environment when running commands:

```bash
ENV=dev pytest
```

Or set it permanently by editing `.env`.

---

## 2. `hosts_config.py` (Non-Sensitive Public Configuration)

This file contains **public, non-sensitive settings** for multiple environments and machines, including:

- API base URLs
- WooCommerce endpoints
- Database hosts and ports (non-secret)

Example structure:

```python
API_HOSTS = {
    "test": "http://localhost:8888/kwakiweb/wp-json/wc/v3/",
    "dev": "https://dev.example.com/wp-json/wc/v3/",
    "prod": "https://example.com/wp-json/wc/v3/"
}

WOO_API_HOSTS = {
    "test": "http://localhost:8888/kwakiweb",
    "dev": "https://dev.example.com",
    "prod": "https://example.com"
}

```

### Purpose

- Contains **public endpoint mappings** per environment.
- Supports multiple machines (e.g., laptop vs Docker).
- Safe to commit to Git.

---

## 3. `config_loader.py` (Dynamic Config Selector)

This module loads `.env`, reads `hosts_config.py`, and provides a **clean API** for accessing environment-specific configuration.

### Example Implementation

```python
import os
from dotenv import load_dotenv
from hosts_config import API_HOSTS, WOO_API_HOSTS, DB_HOST

load_dotenv()

ENV = os.getenv("ENV", "test").lower()
MACHINE = os.getenv("MACHINE", "machine1").lower()

def get_api_host():
    return API_HOSTS.get(ENV, "")

def get_woo_host():
    return WOO_API_HOSTS.get(ENV, "")

def get_db_config():
    machine_cfg = DB_HOST.get(MACHINE, {})
    return machine_cfg.get(ENV, {})

def get_config():
    return {
        "env": ENV,
        "machine": MACHINE,
        "api_host": get_api_host(),
        "woo_host": get_woo_host(),
        "db": get_db_config(),
        "wc_key": os.getenv("WC_KEY"),
        "wc_secret": os.getenv("WC_SECRET")

    }
```

### Purpose

- Provides unified access to: API URLs, DB config, credentials, and environment parameters.
- Ensures consistent environment selection across the whole test suite.
- Eliminates hardcoding and reduces risk of mixing environments.

### Usage Example

```python
from config_loader import get_config

cfg = get_config()
print(cfg["api_host"])
print(cfg["db"]["host"])
```

---

## 4. How to Switch Environments

### Option A — Use `.env`

Edit:

```text
ENV=dev
MACHINE=docker
```

### Option B — Temporary override in shell

```bash
ENV=prod MACHINE=docker pytest
```

### Option C — CI/CD (e.g., GitHub Actions)

```yaml
env:
  ENV: prod
  MACHINE: docker
```

---

## 5. Recommended Pattern Summary

| File               | Contains                            | Sensitive | Committed | Purpose                        |
| ------------------ | ----------------------------------- | --------- | --------- | ------------------------------ |
| `.env`             | Secrets, environment selectors      | Yes       | No        | Secure runtime variables       |
| `hosts_config.py`  | Public endpoints, DB host structure | No        | Yes       | Static configuration mapping   |
| `config_loader.py` | Logic to combine `.env` + config    | No        | Yes       | Provides dynamic config access |

---

## 6. Benefits of This System

- Safe separation of sensitive vs non-sensitive data.
- Easy environment switching (local + CI/CD).
- Supports multiple machines (machine1, docker, machine2…).
- Centralized configuration avoids duplication.
- Cleaner code — no more hardcoded URLs or DB settings.

---

## 7. Configuration Flow Diagram

```
 ┌──────────────┐        ┌──────────────────┐        ┌────────────────────────┐
 │    .env      │        │ hosts_config.py  │        │   config_loader.py      │
 │ (Sensitive:  │        │ (Public: APIs,   │        │ - Loads .env           │
 │  ENV, MACHINE│        │  DB hosts, URLs) │        │ - Selects env + machine│
 │  Credentials)│        └──────────────────┘        │ - Combines config      │
 └──────┬───────┘                   ▲                │ - Provides get_config() │
        │                           │                └───────────┬────────────┘
        │  Environment + Secrets    │ Public Config               │ Unified Config
        ▼                           │                            ▼
 ┌──────────────────────────────────────────────────────────────────────────────┐
 │                              Test Suite / App                               │
 │                                                                              │
 │  Uses:                                                                       │
 │   - cfg["api_host"]                                                          │
 │   - cfg["woo_host"]                                                          │
 │   - cfg["db"]                                                                 │
 │   - cfg["wc_key"], cfg["wc_secret"]                                          │
 │   - cfg["env"], cfg["machine"]                                               │
 │                                                                              │
 └──────────────────────────────────────────────────────────────────────────────┘
```

This diagram shows:

- `.env` provides the **sensitive** data and environment selectors.
- `hosts_config.py` provides **non-sensitive** mappings.
- `config_loader.py` merges both sources into a unified configuration object.
- Your test suite or application consumes `get_config()` for all environment-specific data.

---

If you want, I can also create:

- A diagram explaining the configuration flow (SVG or ASCII in a separate file)
- A template folder structure for the entire project
- A section on environment-specific report directories

Let me know which of the above you'd like next and I will add it to the repo (or produce the files here).
