# Authentication System --- TestEcommerceAPI

## Overview

The framework uses a **pluggable authentication architecture** so that
API authentication can be changed without modifying the API client or
tests.

Currently the framework **implements OAuth1 (WooCommerce)**
authentication, but the architecture is intentionally designed to
support additional strategies in the future (JWT, OAuth2, Basic, etc.).

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

# Switching Authentication Methods

Authentication is controlled by **environment configuration**, not code.

Edit your `.env` file:

    AUTH_TYPE=oauth1

Currently supported:

  Method   Description
  -------- --------------------------------------------------
  oauth1   WooCommerce consumer key / secret authentication

Example `.env`:

    ENV=test
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

Current implementation focuses on **WooCommerce OAuth1 authentication**,
which is the only method required by the system under test.

However the architecture already supports adding additional
authentication strategies without changing:

-   APIClient
-   HttpClient
-   existing tests

This ensures the framework remains maintainable and extensible.
