"""
GraphQL contract tests for WooCommerce Product mutations.

These tests validate the GraphQL schema itself rather than executing
business operations.

The purpose is to detect schema changes that could break the
entity-level GraphQL tests under tests/products/graphql/.

What we're testing with the schema contract is essentially:
“Does the GraphQL API expose the fields/attributes that our request is supposed to accept?”

"""

import pytest


@pytest.mark.contract
@pytest.mark.graphql
def test_delete_product_schema(graphql_client):
    """
    Verify the DeleteProduct mutation contract exposed by GraphQL.

    The Product delete tests depend on:
    - DeleteProductPayload.product
    - DeleteProductInput.id
    - DeleteProductInput.force

    This test intentionally uses GraphQL introspection instead of
    executing a real deletion. It therefore validates the schema
    contract without modifying database state.
    """

    payload_query = """
    query DeleteProductPayloadSchema {
        __type(name: "DeleteProductPayload") {
            fields {
                name
            }
        }
    }
    """

    input_query = """
    query DeleteProductInputSchema {
        __type(name: "DeleteProductInput") {
            inputFields {
                name
            }
        }
    }
    """

    payload_response = graphql_client.execute(payload_query)
    input_response = graphql_client.execute(input_query)

    assert payload_response.ok
    assert not payload_response.errors

    assert input_response.ok
    assert not input_response.errors

    payload_fields = {
        field["name"] for field in payload_response.data["__type"]["fields"]
    }

    input_fields = {
        field["name"] for field in input_response.data["__type"]["inputFields"]
    }

    assert "product" in payload_fields
    assert "id" in input_fields
    assert "force" in input_fields


@pytest.mark.contract
@pytest.mark.graphql
def test_create_product_schema(graphql_client):
    """
    Verify the CreateProduct mutation contract exposed by GraphQL.

    The Product create test depends on:
    - CreateProductPayload.product
    - CreateProductInput.name
    - CreateProductInput.sku
    - CreateProductInput.description
    - CreateProductInput.regularPrice

    This test intentionally uses GraphQL introspection instead of creating a
    real Product. It therefore validates the schema contract without
    modifying database state.
    """

    payload_query = """
    query CreateProductPayloadSchema {
        __type(name: "CreateProductPayload") {
            fields {
                name
            }
        }
    }
    """

    input_query = """
    query CreateProductInputSchema {
        __type(name: "CreateProductInput") {
            inputFields {
                name
            }
        }
    }
    """

    payload_response = graphql_client.execute(payload_query)
    input_response = graphql_client.execute(input_query)

    assert payload_response.ok
    assert not payload_response.errors

    assert input_response.ok
    assert not input_response.errors

    payload_fields = {
        field["name"] for field in payload_response.data["__type"]["fields"]
    }

    input_fields = {
        field["name"] for field in input_response.data["__type"]["inputFields"]
    }

    assert "product" in payload_fields

    # Validate the Product attributes accepted by the create mutation.
    assert "name" in input_fields
    assert "sku" in input_fields
    assert "description" in input_fields
    assert "regularPrice" in input_fields


@pytest.mark.contract
@pytest.mark.graphql
def test_update_product_schema(graphql_client):
    """
    Verify the UpdateProduct mutation contract exposed by GraphQL.

    The Product update test depends on:
    - UpdateProductPayload.product
    - UpdateProductInput.id
    - UpdateProductInput.name
    - UpdateProductInput.sku
    - UpdateProductInput.description
    - UpdateProductInput.regularPrice

    This test intentionally uses GraphQL introspection instead of updating a
    real Product. It therefore validates the schema contract without
    modifying database state.
    """

    payload_query = """
    query UpdateProductPayloadSchema {
        __type(name: "UpdateProductPayload") {
            fields {
                name
            }
        }
    }
    """

    input_query = """
    query UpdateProductInputSchema {
        __type(name: "UpdateProductInput") {
            inputFields {
                name
            }
        }
    }
    """

    payload_response = graphql_client.execute(payload_query)
    input_response = graphql_client.execute(input_query)

    assert payload_response.ok
    assert not payload_response.errors

    assert input_response.ok
    assert not input_response.errors

    payload_fields = {
        field["name"] for field in payload_response.data["__type"]["fields"]
    }

    input_fields = {
        field["name"] for field in input_response.data["__type"]["inputFields"]
    }

    assert "product" in payload_fields

    # Validate the Product attributes accepted by the update mutation.
    assert "id" in input_fields
    assert "name" in input_fields
    assert "sku" in input_fields
    assert "description" in input_fields
    assert "regularPrice" in input_fields


@pytest.mark.contract
@pytest.mark.graphql
def test_products_query_schema(graphql_client):
    """
    Verify the Product connection contract used by Product queries.

    The Product query and pagination tests depend on:
    - ProductConnection.nodes
    - ProductConnection.pageInfo
    - PageInfo.hasNextPage
    - PageInfo.endCursor

    This test intentionally uses GraphQL introspection instead of querying
    real Products. It therefore validates the schema contract without
    modifying database state.
    """

    connection_query = """
    query ProductConnectionSchema {
        __type(name: "ProductConnection") {
            fields {
                name
            }
        }
    }
    """

    page_info_query = """
    query PageInfoSchema {
        __type(name: "PageInfo") {
            fields {
                name
            }
        }
    }
    """

    connection_response = graphql_client.execute(connection_query)
    page_info_response = graphql_client.execute(page_info_query)

    assert connection_response.ok
    assert not connection_response.errors

    assert page_info_response.ok
    assert not page_info_response.errors

    connection_fields = {
        field["name"] for field in connection_response.data["__type"]["fields"]
    }

    page_info_fields = {
        field["name"] for field in page_info_response.data["__type"]["fields"]
    }

    assert "nodes" in connection_fields
    assert "pageInfo" in connection_fields
    assert "hasNextPage" in page_info_fields
    assert "endCursor" in page_info_fields
