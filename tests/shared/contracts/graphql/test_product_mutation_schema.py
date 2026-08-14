"""
GraphQL contract tests for WooCommerce Product mutations.

These tests validate the GraphQL schema itself rather than executing
business operations.

The purpose is to detect schema changes that could break the
entity-level GraphQL tests under tests/products/graphql/.
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
    {
        __type(name: "DeleteProductPayload") {
            fields {
                name
            }
        }
    }
    """

    input_query = """
    {
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
