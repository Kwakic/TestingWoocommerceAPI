# GraphQL Testing Guide

* > **Status:** Active development
* > **Scope:** GraphQL testing with WPGraphQL + WPGraphQL for WooCommerce
* > **Current entity:** Products
* > **Last updated:** 2026-08-14

---

## 1. 🎯 Purpose

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
    ├── contracts/
    │    ├── rest/
    │    │    ├── error_schema.py
    │    │    ├── test_response_format.py
    │    │    ├── test_api_connectivity.py
    │    │    └── __init__.py
    │    └── graphql/
    │         ├── test_graphql_connectivity.py
    │         ├── test_product_mutation_schema.py
    │         └── __init__.py
    ├── security/
    └── preflight/

```
GraphQL follows the same domain-oriented organization as REST for
entity-specific behavior.

Entity-specific GraphQL operations live under:

```text
tests/<entity>/graphql/
```

Framework-level GraphQL contract tests live under the shared Contract suite:

```text
tests/shared/contracts/graphql/
```

---

## 2. 🏛️ Current GraphQL Architecture

The current request flow is:

```text
pytest test
    ↓
graphql_client fixture
    ↓
credentials
    ↓
BasicAuth
    ↓
HttpClient
    ↓
GraphQLClient
    ↓
WordPress Application Password
    ↓
/graphql
    ↓
WPGraphQL
    ↓
WPGraphQL for WooCommerce
    ↓
createProduct
    ↓
real database record
```

>This chain was verified during the initial GraphQL implementation using the Product createProduct mutation.

>The test does not rely on pre-existing database data. The mutation creates a real WooCommerce product, returns its
databaseId, and the test validates the resulting resource. This establishes that the complete path from pytest through
the framework's authentication and HTTP layers to WPGraphQL/WPGraphQL for WooCommerce is functioning end-to-end.
The GraphQL client is responsible for GraphQL transport and response wrapping. Business-specific assertions
remain in the tests.

---

## 3. 🛠️ GraphQL Endpoint Configuration

The environment-specific GraphQL endpoint is configured centrally in:

```text
EcommerceAPI/src/configs/config_graphql.py
```

👉 The endpoint is selected according to the active framework environment (`API_ENV`).

This configuration remains in the framework because it describes where the GraphQL service is located, rather than product-specific test data or business behavior.

REST entity configuration remains under the individual test domains, for example:

```text
tests/products/configs/config_products.py
```

GraphQL and REST therefore intentionally have **different configuration** responsibilities.

---


## 4. 🔐 Authentication

### 4.1 🤔 Why GraphQL does not use the REST OAuth1 pipeline

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

### 4.2 🔑 WordPress Application Password

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

### 4.3 🐋 Docker requirement

The Docker WordPress service uses:

```yaml
WP_ENVIRONMENT_TYPE: local
```

The local environment setting is required because the Docker stack uses plain HTTP rather than HTTPS and WordPress otherwise disables Application Password authentication for the request.

The `wpcli` service uses the same environment type for consistency.

---

## 5. 🔐 Credentials

The current local test environment provides:

```text
WP_ADMIN_USER=admin
WP_ADMIN_APP_PASSWORD=<application-password>
```

These values belong in the local `.env` file and must not be committed to the repository.

The application password is currently provisioned manually during development.

Automating Application Password generation as part of `setup.sh` is a possible future improvement, but is intentionally outside the current GraphQL implementation scope.

---

## 6. ⚙️ GraphQL Client

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

## 9. 🧪 Current Product GraphQL Tests

The initial Product GraphQL coverage contains 5 tests.

---

### 9.1 🛠️ Create Product

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

---

### 9.2 🫴 Get Product

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

---

### 9.3 🗑️ Delete Product

File:

```text
tests/products/graphql/test_delete_product.py
```

The test follows this lifecycle:

```
create product
    ↓
capture databaseId
    ↓
delete product using databaseId
    ↓
verify deletion
    ↓
query the same databaseId
    ↓
verify product no longer exists
```

The deletion mutation uses:

```
deleteProduct(
    input: {
        id: $id
        force: true
    }
)
```

The `force: true` option is important because the default deletion behavior moves the product to the WordPress trash
rather than permanently deleting it.

The test therefore verifies the final state by querying the product after deletion and expecting GraphQL to
report that no product exists with the given database `ID`.

The test creates its own product and never depends on an existing database record.



---

### 9.4 ❌ Negative GraphQL Test

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

### 9.5 ✏️ Update product

```text
tests/products/graphql/test_update_product.py
```

The test verifies that an existing product can be updated through the GraphQL API and that the change is
actually persisted.

The test follows this lifecycle:

```
create product
    ↓
capture databaseId
    ↓
update product name
    ↓
verify mutation response
    ↓
query the same databaseId
    ↓
verify updated product state
```

The product is created by the test itself, so the test does not depend on any pre-existing database data.

The update mutation receives the product databaseId and the new product name as GraphQL variables:

```
mutation UpdateProduct($id: ID!, $name: String!) {
    updateProduct(
        input: {
            id: $id
            name: $name
        }
    ) {
        product {
            databaseId
            name
        }
    }
}
```

### ✅ The test verifies that:
* the mutation succeeds;
* the response contains no GraphQL errors;
* the returned databaseId is unchanged;
* the returned product name matches the new value;
* a subsequent query returns the updated product.

The final query is important because it verifies the resulting state rather than relying only on the mutation response.

This follows the general GraphQL testing pattern:

```
CREATE → UPDATE → READ
```
and keeps the test deterministic by using the identifier of the product created during the test.

---

## 10. 📊 Data Independence Principle

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

---

## 11.🏗️ Current Test Structure

The current Product GraphQL area is:

```text
tests/products/graphql/
├── test_create_product.py
├── test_get_product.py
├── test_delete_product.py
├── test_update_product.py
└── test_product_negative.py
```

Temporary diagnostic tests used during GraphQL authentication investigation have been removed.

---

## 12. ⚡ Running GraphQL Tests

Run an individual Product GraphQL test:

```bash
pytest tests/products/graphql/test_create_product.py -v
```

Run the complete Product GraphQL suite:

```bash
pytest tests/products/graphql/ -v
```

Run all GraphQL tests:

```bash
pytest -m graphql -v
```

Run GraphQL contract tests:

```bash
pytest -m "graphql and contract" -v
```

Run Product GraphQL integration tests:

```bash
pytest -m "products and graphql and integration" -v
```

Run GraphQL negative tests:

```bash
pytest -m "graphql and negative" -v
```

---

## 13. 🔗 GraphQL Contract Tests

Framework-level GraphQL contract tests live under:

```text
tests/shared/contracts/graph/
                        ├── test_graphql_connectivity.py
                        └── test_product_mutation_schema.py
```
These tests validate the GraphQL API contract rather than Product business
behavior.

### 🌐 GraphQL connectivity

```text
test_graphql_connectivity.py
```
Verifies that the GraphQL endpoint is reachable and can successfully execute
a basic GraphQL operation.

### 🧬 Product mutation schema
```text
test_product_mutation_schema.py
```
Uses GraphQL introspection to verify that the schema exposes the fields and
inputs required by the Product GraphQL tests.

The schema test does not execute a real Product mutation and therefore does
not modify database state.

Both tests are marked:

```text
@pytest.mark.contract
@pytest.mark.graphql
```
GraphQL business behavior remains under the corresponding entity:
```text
tests/products/graphql/
tests/customers/graphql/
tests/orders/graphql/
tests/coupons/graphql/
```
This keeps framework-level API contracts separate from entity-level GraphQL
behavior.


---

## 14. 👨‍💻 Development Roadmap

The GraphQL implementation is intentionally being developed incrementally.

### Completed

- [x] GraphQL plugins provisioned in Docker.
- [x] WPGraphQL version pinned.
- [x] WPGraphQL for WooCommerce version pinned.
- [x] GraphQL endpoint readiness check added to provisioning.
- [x] Environment-specific GraphQL endpoint configuration established.
- [x] Shared GraphQL connectivity test
- [x] GraphQL client implemented.
- [x] WordPress Application Password authentication established.
- [x] GraphQL authentication integrated into the client fixture.
- [x] Product create test.
- [x] Product get test.
- [x] Product delete test.
- [x] Product update test.
- [x] GraphQL negative/error test.
- [x] Temporary OAuth diagnostic test removed.
- [x] Product GraphQL test suite verified together.

### Next development area

The next logical areas for Product GraphQL coverage are:

* product search;
* product filters;
* categories;
* additional variables and query patterns;
* additional mutations;
* authorization scenarios;
* error handling;
* broader GraphQL schema contract coverage.


The exact order should evolve with the Product entity implementation rather than being over-designed in advance.

---

## 15. 🎨 Design Principles

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

---

## 16. </> Known Development State

This document is intentionally a living guide.

GraphQL support is currently under development and the Product entity is the first active implementation.

As GraphQL coverage expands to Customers, Orders, Coupons, and additional Product operations, this document should be updated to reflect the architecture that has actually been implemented rather than speculative future design.
