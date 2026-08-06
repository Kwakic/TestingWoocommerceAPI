# ⚙️ Entity Configuration

This directory contains the **entity-specific configuration** used by this
test suite.

Each entity owns its own `config_<entity>.py` module, which defines the
public `API_HOSTS` mapping for every supported execution environment.

These configuration files:

- 🌐 Define public API endpoint URLs
- 🔒 Contain **no secrets**
- ✅ Are safe to commit to Git
- 👥 Are owned by the entity team

Sensitive runtime values (such as WooCommerce API credentials) are
generated during `make setup` and stored in `.env`.

Framework runtime configuration (environment parsing, feature flags,
logging, reporting, CI behaviour and runtime configuration) is managed
by the shared EcommerceAPI framework.

---

## 📦 What belongs here?

This directory contains only the **entity-specific endpoint configuration**.

Typical contents:

```text
configs/
├── config_customers.py
└── README.md
```

`config_<entity>.py` defines the public `API_HOSTS` mapping used by the
entity helpers to resolve the correct API endpoint for the active
execution environment.

The configuration is intentionally public because endpoint URLs are not
sensitive.

---

## 🚫 What does **not** belong here?

This directory must **not** contain:

- ❌ Secrets or credentials
- ❌ Environment variable parsing
- ❌ Runtime configuration
- ❌ Logging configuration
- ❌ Reporting configuration
- ❌ Framework feature flags
- ❌ CI-specific logic

Those responsibilities belong to the shared EcommerceAPI framework.

---

## 📚 Related Documentation

### 🧭 Learn how the configuration system works

`docs/framework/README_ENVIRONMENT_CONFIG_GUIDE.md`

This is the **canonical guide** explaining:

- API_ENV
- Environment selection
- Endpoint resolution
- Docker
- CI
- Execution modes
- Runtime configuration
- Troubleshooting

### 📘 Framework rules and architecture

`docs/framework/README_CONFIG_CONTRACT.md`

This document defines the configuration contract, ownership model, and
architectural rules that all entities must follow.

---

## 🏗️ Entity Ownership

Each entity owns only its own endpoint definitions.

For example:

- 👤 Customers → `config_customers.py`
- 📦 Orders → `config_orders.py`
- 🛍️ Products → `config_products.py`
- 🎟️ Coupons → `config_coupons.py`

Shared framework components never import these modules directly.
Instead, entity helpers resolve the correct endpoint and inject it into
the shared API client, keeping the framework completely service-agnostic.

---

> 💡 **Why is this README so short?**
>
> This document is intentionally lightweight.
> It explains only the purpose of this entity's configuration directory.
>
> The complete framework configuration architecture is documented centrally in:
>
> - `docs/framework/README_ENVIRONMENT_CONFIG_GUIDE.md`
> - `docs/framework/README_CONFIG_CONTRACT.md`
