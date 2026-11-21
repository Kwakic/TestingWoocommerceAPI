# ⚙️ Coupons Entity Configuration

This directory contains the public REST endpoint mapping for Coupons. The
active `API_ENV` selects the endpoint; credentials and database connection
settings come from the selected environment profile.

## Coupons REST endpoints

`config_coupons.py` defines one endpoint for each supported execution profile:

| Profile | `API_ENV` | Where pytest runs | Coupons REST endpoint | How to run |
|---|---|---|---|---|
| Existing WAMP site | `local` | Developer's computer | `http://localhost:8888/kwakiweb/wp-json/wc/v3/` | Direct pytest; REST tests only |
| Docker host-based | `test` | Developer's computer | `http://localhost:8080/wp-json/wc/v3/` | `make run` |
| Docker containerized | `docker` | Test-runner container | `http://wordpress/wp-json/wc/v3/` | `make test-docker` |
| GitHub Actions | `ci` | GitHub-hosted runner | `http://localhost:8080/wp-json/wc/v3/` | Run a GitHub Actions workflow |

Choose the profile that matches where pytest runs. For example, when running
Coupons REST tests against the existing WAMP site, copy `.env.wamp.example` to
`.env.wamp`, fill in the existing WAMP credentials, then run from PowerShell:

```powershell
$env:API_ENV = "local"
.\.venv\Scripts\python.exe -m pytest tests\coupons\api
Remove-Item Env:API_ENV
```

This direct command does not start, provision, or clean up Docker. WAMP
currently supports REST tests only; GraphQL and UI tests require the
provisioned Docker/CI environments.

## What belongs in this directory?

`config_coupons.py` may contain public Coupons API endpoint URLs. It must not
contain API keys, passwords, database credentials, environment-variable
loading, or other runtime settings.

- `.env` contains the Docker host-based profile (`API_ENV=test`).
- `.env.wamp` contains the existing WAMP profile (`API_ENV=local`).
- Docker container and CI credentials are supplied by their runner or
  workflow environment.
- GraphQL endpoints are shared and defined in
  `EcommerceAPI/src/configs/config_graphql.py`.
- Docker Compose has three services: `wordpress` (WordPress with the
  WooCommerce plugin), `db` (MySQL), and `wpcli` (WP-CLI). WooCommerce is not
  a separate container.

See the [Environment & Configuration Guide](../../../docs/framework/README_ENVIRONMENT_CONFIG_GUIDE.md)
for the shared profile, credential, and database configuration details.
