# Authentication System - TestEcommerceAPI

## Overview

The framework uses a **pluggable authentication architecture** so that
API authentication can be changed without modifying the API client or
tests.

The framework implements **OAuth1 (WooCommerce)** for the REST API.
GraphQL uses **WordPress Application Password + HTTP Basic Auth**.
The two authentication flows are intentionally independent.

Authentication is resolved dynamically during runtime using
configuration.

------------------------------------------------------------------------

# Authentication Architecture

    pytest
       ↓
    config_pytest plugin
       ↓
    runtime_config.get_config()
       ↓
    FrameworkConfig.AUTH_TYPE
       ↓
    auth_resolver.resolve_auth()
       ↓
    auth_factory.build_auth()
       ↓
    AuthStrategy implementation
       ↓
    APIClient
       ↓
    HttpClient
       ↓
    requests.Session

Key idea:

-   **Configuration chooses authentication**
-   **Factory builds strategy**
-   **APIClient applies strategy**

------------------------------------------------------------------------

# Core Components

## 1. runtime_config

File:

    src/configs/runtime_config.py

Responsibilities:

-   Reads environment variables
-   Builds immutable `FrameworkConfig`
-   Caches configuration for performance

Important field:

    AUTH_TYPE

Example:

    AUTH_TYPE=oauth1

This value determines which authentication strategy is used.

------------------------------------------------------------------------

## 2. auth_resolver

File:

    src/auth/auth_resolver.py

Purpose:

Connects runtime configuration with authentication factory.

Example:

``` python
cfg = get_config()
return build_auth(cfg.AUTH_TYPE)
```

This isolates configuration logic from the API client.

------------------------------------------------------------------------

## 3. auth_factory

File:

    src/auth/auth_factory.py

Purpose:

Selects the correct authentication strategy.

Example:

``` python
if auth_type == "oauth1":
    return OAuth1Auth()
```

The factory never performs authentication itself.\
It only **chooses the correct strategy class**.

------------------------------------------------------------------------

## 4. AuthStrategy (base class)

File:

    src/auth/base_auth.py

Defines the authentication interface.

Example:

``` python
class AuthStrategy(ABC):

    @abstractmethod
    def apply(self, request_kwargs):
        pass
```

Each strategy modifies request arguments before the request is sent.

------------------------------------------------------------------------

## 5. OAuth1Auth Strategy

File:

    src/auth/oauth1_auth.py

Purpose:

Authenticate WooCommerce REST API requests.

Credentials are loaded from:

    credentials_utility.get_wc_api_keys()

Example behavior:

    request_kwargs["auth"] = OAuth1(consumer_key, consumer_secret)

------------------------------------------------------------------------

# GraphQL Authentication

GraphQL uses a different authentication mechanism from the WooCommerce
REST API.

## REST authentication

```text
WC_KEY + WC_SECRET
        ↓
      OAuth1
        ↓
   WooCommerce REST API
```

## GraphQL authentication

```text
WP_ADMIN_USER + WP_ADMIN_APP_PASSWORD
                ↓
             BasicAuth
                ↓
             WPGraphQL
```

GraphQL mutations require a WordPress user context, so the REST OAuth1
credentials are **not** used for authenticated GraphQL operations.

The GraphQL client receives its authentication strategy through the
`graphql_client` fixture rather than resolving the REST
`AUTH_TYPE=oauth1` pipeline.

GraphQL authentication is therefore intentionally independent from the
REST OAuth1 pipeline.

The GraphQL credentials are:

```text
WP_ADMIN_USER
WP_ADMIN_APP_PASSWORD
```

They are loaded from the environment and must not be hardcoded in GraphQL
tests.

For the complete GraphQL authentication and testing flow, see:

```text
docs/development/README_GRAPHQL_TESTING_GUIDE.md
```

------------------------------------------------------------------------

# APIClient Authentication Resolution

Inside `APIClient.__init__`:

``` python
if auth_strategy:
    self.auth_strategy = auth_strategy
else:
    self.auth_strategy = resolve_auth()
```

Priority:

1.  **Injected authentication strategy** (used by security tests)
2.  **Framework configuration (AUTH_TYPE)**

This allows tests to override authentication.

Example:

``` python
APIClient(base_url, auth_strategy=InvalidOAuthStrategy())
```

------------------------------------------------------------------------

# Switching REST Authentication Methods

REST authentication is controlled by **environment configuration**, not code.

Edit your `.env` file:

    AUTH_TYPE=oauth1

Currently supported REST authentication:

  Method   Description
  -------- --------------------------------------------------
  oauth1   WooCommerce consumer key / secret authentication

GraphQL authentication is configured separately:

  Component                  Description
  ------------------------   --------------------------------------------
  BasicAuth                  HTTP Basic authentication
  WP_ADMIN_USER              WordPress administrator/user account
  WP_ADMIN_APP_PASSWORD      WordPress Application Password

Example `.env`:

    API_ENV=test
    AUTH_TYPE=oauth1

    WC_KEY=ck_xxxxxxxxx
    WC_SECRET=cs_xxxxxxxxx

After changing `.env`, restart pytest to reload configuration.

------------------------------------------------------------------------

# Adding New Authentication Methods (Future)

The architecture already supports adding more strategies.

Steps:

### 1. Create strategy

Example:

    src/auth/jwt_auth.py

Example implementation:

``` python
class JWTAuth(AuthStrategy):

    def __init__(self, token):
        self.token = token

    def apply(self, request_kwargs):
        headers = request_kwargs.setdefault("headers", {})
        headers["Authorization"] = f"Bearer {self.token}"
        return request_kwargs
```

### 2. Register strategy in factory

    src/auth/auth_factory.py

``` python
if auth_type == "jwt":
    return JWTAuth()
```

### 3. Configure environment

    AUTH_TYPE=jwt

No changes required in `APIClient` or tests.

> **Note:** `AUTH_TYPE` and `auth_factory` describe the REST authentication
> pipeline. GraphQL authentication is intentionally wired separately through
> the GraphQL client fixture and is not selected by `AUTH_TYPE`.

------------------------------------------------------------------------

# Security Testing

Authentication strategies can be injected directly during tests.

Example:

``` python
client = APIClient(
    base_url,
    auth_strategy=InvalidOAuthStrategy("bad_key", "bad_secret")
)
```

Used by:

    tests/shared/security/test_authentication_matrix.py

Allows testing:

-   invalid credentials
-   missing authentication
-   tampered signatures
-   expired tokens

------------------------------------------------------------------------

# Design Principles

The authentication system follows several architectural rules:

  Principle                Explanation
  ------------------------ --------------------------------------------
  Configuration Driven     authentication type controlled by config
  Strategy Pattern         authentication logic isolated per strategy
  Factory Pattern          strategy creation centralized
  Dependency Injection     tests can override authentication
  Separation of Concerns   APIClient never knows auth details

------------------------------------------------------------------------

# Final Notes

The current framework has two authentication paths:

```text
REST
    WC_KEY + WC_SECRET
            ↓
          OAuth1
            ↓
       APIClient

GraphQL
    WP_ADMIN_USER + WP_ADMIN_APP_PASSWORD
                    ↓
                 BasicAuth
                    ↓
              GraphQLClient
```

These paths are intentionally independent because WooCommerce REST and
WPGraphQL use different authentication mechanisms.

The REST authentication architecture remains pluggable and supports adding
additional REST authentication strategies without changing:

-   APIClient
-   HttpClient
-   existing REST tests

GraphQL authentication is handled independently by the GraphQL client
infrastructure.

This ensures the framework remains maintainable and extensible.
