# GraphQL Testing Guide

> **Status:** Active development
> **Scope:** GraphQL testing with WPGraphQL + WPGraphQL for WooCommerce
> **Current entity:** Products
> **Last updated:** 2026-08-13

## 1. Purpose

This guide documents the GraphQL testing architecture and development approach used by the test suite.

GraphQL tests are kept separate from REST API tests while remaining organized by business entity.

```text
tests/
├── customers/
│   ├── api/
│   ├── graphql/
│   └── performance/
├── products/
│   ├── api/
│   ├── graphql/
│   │   ├── test_create_product.py
│   │   ├── test_get_product.py
│   │   └── test_product_negative.py
│   └── performance/
├── orders/
│   ├── api/
│   ├── graphql/
│   └── performance/
├── coupons/
│   ├── api/
│   ├── graphql/
│   └── performance/
└── shared/
    └── graphql/
        └── test_graphql_smoke.py
```

GraphQL therefore follows the same domain-oriented organization as REST, but uses a dedicated `graphql/` area inside each entity.

## 2. Current GraphQL Architecture

The current request flow is:

```text
pytest test
    ↓
graphql_client fixture
    ↓
GraphQLClient
    ↓
BasicAuth
    ↓
WordPress Application Password
    ↓
HttpClient
    ↓
/graphql
    ↓
WPGraphQL
    ↓
WPGraphQL for WooCommerce
```

The GraphQL client is responsible for GraphQL transport and response wrapping. Business-specific assertions remain in the tests.

## 3. GraphQL Endpoint Configuration

The environment-specific GraphQL endpoint is configured centrally in:

```text
EcommerceAPI/src/configs/config_graphql.py
```

The endpoint is selected according to the active framework environment (`API_ENV`).

This configuration remains in the framework because it describes where the GraphQL service is located, rather than product-specific test data or business behavior.

REST entity configuration remains under the individual test domains, for example:

```text
tests/products/configs/config_products.py
```

GraphQL and REST therefore intentionally have different configuration responsibilities.

## 4. Authentication

### 4.1 Why GraphQL does not use the REST OAuth1 pipeline

The REST framework uses WooCommerce API credentials:

```text
WC_KEY
WC_SECRET
```

and the global REST authentication configuration:

```text
AUTH_TYPE=oauth1
```

Those credentials are appropriate for the WooCommerce REST API but do not establish the WordPress user context required by WPGraphQL mutations.

GraphQL mutations such as `createProduct` therefore use WordPress authentication instead.

### 4.2 WordPress Application Password

The GraphQL client authenticates using:

```text
WP_ADMIN_USER
WP_ADMIN_APP_PASSWORD
```

through HTTP Basic Auth.

The `requests` transport receives:

```python
auth=(username, application_password)
```

which is handled by the existing `BasicAuth` authentication strategy.

The GraphQL authentication flow is intentionally separate from the REST `AUTH_TYPE/OAuth1` pipeline.

### 4.3 Docker requirement

The Docker WordPress service uses:

```yaml
WP_ENVIRONMENT_TYPE: local
```

The local environment setting is required because the Docker stack uses plain HTTP rather than HTTPS and WordPress otherwise disables Application Password authentication for the request.

The `wpcli` service uses the same environment type for consistency.

## 5. Credentials

The current local test environment provides:

```text
WP_ADMIN_USER=admin
WP_ADMIN_APP_PASSWORD=<application-password>
```

These values belong in the local `.env` file and must not be committed to the repository.

The application password is currently provisioned manually during development.

Automating Application Password generation as part of `setup.sh` is a possible future improvement, but is intentionally outside the current GraphQL implementation scope.

## 6. GraphQL Client

The GraphQL client is located at:

```text
EcommerceAPI/src/clients/graphql_client.py
```

Its responsibilities are intentionally narrow:

- accept the GraphQL endpoint;
- accept an optional authentication strategy;
- execute GraphQL queries and mutations;
- delegate HTTP transport to `HttpClient`;
- convert the HTTP response into `GraphQLResponse`.

It does not contain:

- business logic;
- product-specific logic;
- test assertions;
- schema validation;
- domain-specific data handling.

The client can therefore support both authenticated and anonymous GraphQL operations.

Conceptually:

```python
GraphQLClient(base_url)
```

can be used for anonymous operations, while:

```python
GraphQLClient(
    base_url=...,
    auth_strategy=BasicAuth(...),
)
```

is used by the authenticated test fixture.

## 7. GraphQL Fixture

The shared GraphQL fixture creates a session-scoped authenticated client.

Conceptually:

```python
graphql_base_url = get_graphql_host()
credentials = get_wp_admin_credentials()

auth_strategy = BasicAuth(
    username=credentials["wp_admin_user"],
    password=credentials["wp_admin_app_password"],
)

return GraphQLClient(
    base_url=graphql_base_url,
    auth_strategy=auth_strategy,
)
```

Tests therefore consume:

```python
def test_something(graphql_client):
    ...
```

rather than handling credentials themselves.

This keeps authentication out of individual tests.

## 8. GraphQL Response Semantics

GraphQL has an important behavior that differs from conventional REST testing:

```text
HTTP 200
```

does not necessarily mean the GraphQL operation succeeded.

A response can be:

```json
{
  "errors": [
    {
      "message": "..."
    }
  ],
  "data": null
}
```

while still returning HTTP `200`.

Therefore, GraphQL tests must consider both:

```python
response.ok
```

and:

```python
response.errors
```

A successful operation should generally assert:

```python
assert response.ok
assert not response.errors
```

A negative GraphQL test can intentionally assert:

```python
assert response.status_code == 200
assert response.errors
```

This distinction is part of the GraphQL test contract.

## 9. Current Product GraphQL Tests

The initial Product GraphQL coverage contains three tests.

### 9.1 Create Product

File:

```text
tests/products/graphql/test_create_product.py
```

The test:

1. executes a `createProduct` mutation;
2. creates a real product in the test database;
3. captures the returned `databaseId`;
4. verifies the returned product data.

The important principle is that the test creates its own data rather than depending on products that happen to exist in the database.

### 9.2 Get Product

File:

```text
tests/products/graphql/test_get_product.py
```

The test follows this lifecycle:

```text
create product
    ↓
capture databaseId
    ↓
query that databaseId
    ↓
verify returned product
```

The product query uses:

```graphql
product(id: $id, idType: DATABASE_ID)
```

This makes the test deterministic with respect to the product being tested.

It does not rely on:

```graphql
products(first: 1)
```

or any pre-existing database record.

### 9.3 Negative GraphQL Test

File:

```text
tests/products/graphql/test_product_negative.py
```

The test requests an invalid product field and verifies that GraphQL reports an error.

The key assertions are:

```python
assert response.status_code == 200
assert response.errors
```

This test documents the distinction between HTTP-level success and GraphQL-level success.

## 10. Data Independence Principle

GraphQL tests must not depend on arbitrary records already present in the Docker database.

Avoid patterns such as:

```graphql
products(first: 1)
```

when the purpose of the test is to validate a particular product.

Prefer:

```text
create
  ↓
capture identifier
  ↓
query/update/delete using identifier
```

This makes tests deterministic and suitable for fresh Docker environments and CI.

## 11. Current Test Structure

The current Product GraphQL area is:

```text
tests/products/graphql/
├── test_create_product.py
├── test_get_product.py
└── test_product_negative.py
```

Temporary diagnostic tests used during GraphQL authentication investigation have been removed.

## 12. Running GraphQL Tests

Run an individual test:

```bash
pytest tests/products/graphql/test_create_product.py -v
```

Run the Product GraphQL suite:

```bash
pytest tests/products/graphql/ -v
```

Run the shared GraphQL smoke test:

```bash
pytest tests/shared/graphql/test_graphql_smoke.py -v
```

## 13. Shared GraphQL Smoke Test

Framework-level GraphQL checks live under:

```text
tests/shared/graphql/
```

The current smoke test verifies basic GraphQL endpoint availability.

Entity-specific GraphQL behavior belongs under the corresponding domain:

```text
tests/products/graphql/
tests/customers/graphql/
tests/orders/graphql/
tests/coupons/graphql/
```

This keeps framework-level connectivity checks separate from business-entity behavior.

## 14. Development Roadmap

The GraphQL implementation is intentionally being developed incrementally.

### Completed

- [x] GraphQL plugins provisioned in Docker.
- [x] WPGraphQL version pinned.
- [x] WPGraphQL for WooCommerce version pinned.
- [x] GraphQL endpoint readiness check added to provisioning.
- [x] Environment-specific GraphQL endpoint configuration established.
- [x] Shared GraphQL smoke test created.
- [x] GraphQL client implemented.
- [x] WordPress Application Password authentication established.
- [x] GraphQL authentication integrated into the client fixture.
- [x] Product create test.
- [x] Product get test.
- [x] GraphQL negative/error test.
- [x] Temporary OAuth diagnostic test removed.
- [x] Product GraphQL test suite verified together.

### Next development area

The next logical Product GraphQL coverage should extend the entity lifecycle, for example:

```text
CREATE
  ↓
READ
  ↓
UPDATE
  ↓
DELETE
```

Additional GraphQL capabilities can then be added incrementally, such as:

- product search;
- product filters;
- categories;
- variables;
- mutations;
- authorization scenarios;
- error handling;
- GraphQL-specific contract coverage.

The exact order should evolve with the Product entity implementation rather than being over-designed in advance.

## 15. Design Principles

### Keep GraphQL separate from REST

GraphQL tests live under:

```text
<entity>/graphql/
```

rather than being mixed into:

```text
<entity>/api/
```

This makes the transport style immediately visible while preserving the domain-oriented structure.

### Keep authentication out of tests

Tests consume the `graphql_client` fixture.

Credentials and authentication strategy are infrastructure concerns.

### Keep the GraphQL client thin

The client should transport GraphQL operations and wrap responses.

Domain behavior belongs in tests/helpers as the framework evolves.

### Create the data you test

Do not rely on arbitrary records already present in the database.

### Treat GraphQL errors explicitly

HTTP status alone is insufficient to determine GraphQL operation success.

## 16. Known Development State

This document is intentionally a living guide.

GraphQL support is currently under development and the Product entity is the first active implementation.

As GraphQL coverage expands to Customers, Orders, Coupons, and additional Product operations, this document should be updated to reflect the architecture that has actually been implemented rather than speculative future design.
