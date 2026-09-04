# GraphQL Testing Guide

* > **Status:** Active development
* > **Scope:** GraphQL testing with WPGraphQL + WPGraphQL for WooCommerce
* > **Current entity:** Products
* > **Last updated:** 2026-08-16

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
│   │   ├── test_delete_product.py
│   │   ├── test_get_product.py
│   │   ├── test_update_product.py
│   │   ├── test_search_product.py
│   │   ├── test_filter_products.py
│   │   ├── test_get_all_products.py
│   │   └── test_product_error_handling.py
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

---

## 7. GraphQL Fixtures

### 7.1 Authenticated GraphQL client

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

### 7.2 GraphQL resource cleanup

GraphQL-created Products use the existing shared REST resource cleanup mechanism.

The shared GraphQL fixture exposes:

```python
graphql_resources(product_id)
```

When a GraphQL test creates a Product, it registers the returned `databaseId` with the shared resource tracker. The existing entity teardown then removes the Product using the established Product delete method.

This keeps GraphQL from introducing a second cleanup framework.

Normal usage:

```python
product_id = created_product["databaseId"]

# Register the GraphQL-created product with the shared framework so the
# existing product cleanup runs automatically during fixture teardown.
graphql_resources(product_id)
```

When a test intentionally needs to keep the Product in the database:

```python
graphql_resources(product_id, skip_cleanup=True)
```

This mirrors the existing REST fixture cleanup pattern.

The cleanup lifecycle is therefore:

```text
GraphQL createProduct
        ↓
capture databaseId
        ↓
graphql_resources(product_id)
        ↓
shared_api_resources
        ↓
existing Product teardown
        ↓
DELETE /wp-json/wc/v3/products/{id}?force=True
```

Tests that explicitly delete the Product themselves, such as the GraphQL delete test, do not register that Product for shared cleanup.

Category resources are not currently part of the shared entity cleanup model.

---

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
assert not response.ok
```

The important distinction is:

```text
HTTP 200
    ↓
The GraphQL endpoint successfully received and processed the HTTP request.

GraphQL errors[]
    ↓
The requested GraphQL operation failed.
```

Therefore, `HTTP 200` should not be read as "the test operation passed".
`GraphQLResponse.ok` combines both levels:

```text
HTTP 200 + no GraphQL errors → GraphQL success
HTTP 200 + GraphQL errors    → GraphQL failure
HTTP != 200                  → GraphQL failure
```

This distinction is part of the GraphQL test contract and is intentionally
different from the usual REST API status-code model.


---

## 9. 🧪 Current Product GraphQL Tests

The current Product GraphQL coverage contains 10 tests.

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

### 9.4 ❌ GraphQL Error Handling

File:

```text
tests/products/graphql/test_product_error_handling.py
```

This file contains two meaningful GraphQL error scenarios.

#### Schema-level error

The first test requests a known valid Product field (`databaseId`) together
with an intentionally invalid field.

The operation is explicitly named:

```graphql
query InvalidProductField
```

so the request log remains meaningful.

The test verifies:

```python
assert response.status_code == 200
assert response.errors
assert not response.ok
```

It also verifies that the GraphQL error identifies the intentionally invalid
field.

This documents the distinction between HTTP-level success and GraphQL-level
success: HTTP 200 means the GraphQL endpoint processed the request, while the
`errors` collection tells us that GraphQL rejected the operation.

#### Resolver/business-level error

The second test does not rely on an arbitrary Product ID such as
`999999999`. It first creates a real Product, permanently deletes it, and then
attempts to update the captured ID.

The lifecycle is:

```text
create Product
    ↓
capture databaseId
    ↓
delete Product with force: true
    ↓
update the same databaseId
    ↓
verify GraphQL error
```

This makes the negative scenario deterministic because the test itself proves
that the Product existed and was then removed.

When GraphQL provides an error path, the test verifies that the failure belongs
to:

```text
updateProduct
```

The test does not register the Product with shared cleanup because it
explicitly deletes the Product itself before the negative update.

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

### 9.6 🔎 Product Search

File:

```text
tests/products/graphql/test_search_product.py
```

The test creates its own Product, searches for it using the GraphQL `search`
filter, and verifies that the created Product is returned.

The flow is:

```text
create product
    ↓
capture databaseId
    ↓
products(where: { search: $search })
    ↓
verify created product is returned
```

The test uses GraphQL variables for the search value and registers the created
Product with the shared cleanup mechanism.

### 9.7 🔍 Product Filters

File:

```text
tests/products/graphql/test_filter_products.py
```

This file contains the Product filter coverage currently implemented:

- filter by SKU;
- filter by category.

The SKU test creates a Product with unique test data, filters the Product
connection by SKU, and verifies that the created Product is returned.

The category test creates a Product Category, creates a Product assigned to that
category, filters the Product connection by category ID, and verifies that the
created Product is returned.

Both tests register their created Products with the shared cleanup mechanism.

The category itself is currently not registered for shared cleanup because
Product Categories are not part of the framework's existing entity cleanup
model.

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
├── test_search_product.py
├── test_filter_products.py
├── test_get_all_products.py
└── test_product_error_handling.py
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

The current Product schema contract coverage verifies:

```text
CreateProductPayload
└── product

CreateProductInput
├── name
├── sku
├── description
└── regularPrice

UpdateProductPayload
└── product

UpdateProductInput
├── id
├── name
├── sku
├── description
└── regularPrice

DeleteProductPayload
└── product

DeleteProductInput
├── id
└── force

ProductConnection
├── nodes
└── pageInfo

PageInfo
├── hasNextPage
└── endCursor
```

The introspection operations are explicitly named so that the shared GraphQL
request logger reports meaningful operation names rather than `unknown`.

The schema tests do not execute real Product mutations or queries and therefore
do not modify database state.

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
- [x] GraphQL error-handling coverage (schema-level and resolver-level errors).
- [x] Temporary OAuth diagnostic test removed.
- [x] Product GraphQL test suite verified together.
- [x] Product search test.
- [x] Product SKU filter test.
- [x] Product category filter test.
- [x] Product pagination test using GraphQL cursors.
- [x] Shared Product cleanup reused by GraphQL tests.
- [x] GraphQL request-level logging with operation name/type, HTTP status, duration, and GraphQL error path.
- [x] Product GraphQL schema contracts for create, update, delete, and Product pagination.

### Next development area

The next logical areas for Product GraphQL coverage are:

* additional useful query and variable patterns;
* additional mutations;
* authorization scenarios;
* further GraphQL error handling only where a real uncovered behavior is identified.

Further schema contract coverage should be added only where it protects a
real Product GraphQL operation rather than duplicating the functional tests.


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

### Clean up what GraphQL creates

GraphQL-created Products should be registered with the shared resource cleanup
mechanism so normal test execution does not leave Product data behind.

### Treat GraphQL errors explicitly

HTTP status alone is insufficient to determine GraphQL operation success.

---

## 16. </> Known Development State

This document is intentionally a living guide.

GraphQL support is currently under development and the Product entity is the first active implementation. Product coverage now includes CRUD, search, SKU/category filtering, cursor-based pagination, negative/error behavior, shared cleanup, request-level logging, and schema contracts.

As GraphQL coverage expands to Customers, Orders, Coupons, and additional Product operations, this document should be updated to reflect the architecture that has actually been implemented rather than speculative future design.
