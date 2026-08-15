import pytest

pytestmark = [
    pytest.mark.integration,
    pytest.mark.graphql,
]


def test_update_product(graphql_client, graphql_resources):
    """
    Verify that a product can be updated through the GraphQL API.

    The test creates its own product, captures its database ID, updates
    the product name, and verifies the mutation response. It then queries
    the same product again to confirm that the updated state was persisted.

    This ensures the test does not depend on pre-existing database data
    and validates both the mutation response and the resulting resource state.
    """

    create_query = """
    mutation {
        createProduct(
            input: {
                name: "GraphQL Update Test Product"
            }
        ) {
            product {
                databaseId
                name
            }
        }
    }
    """

    create_response = graphql_client.execute(create_query)

    assert create_response.ok
    assert not create_response.errors

    created_product = create_response.data["createProduct"]["product"]
    product_id = created_product["databaseId"]

    # Register the GraphQL-created product with the shared framework so the
    # existing product cleanup runs automatically during fixture teardown.
    graphql_resources(product_id)

    update_query = """
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
    """

    updated_name = "GraphQL Updated Product"

    update_response = graphql_client.execute(
        update_query,
        variables={
            "id": product_id,
            "name": updated_name,
        },
    )

    assert update_response.ok
    assert not update_response.errors

    updated_product = update_response.data["updateProduct"]["product"]

    assert updated_product["databaseId"] == product_id
    assert updated_product["name"] == updated_name

    get_query = """
    query GetProduct($id: ID!) {
        product(id: $id, idType: DATABASE_ID) {
            databaseId
            name
        }
    }
    """

    get_response = graphql_client.execute(
        get_query,
        variables={"id": product_id},
    )

    assert get_response.ok
    assert not get_response.errors

    product = get_response.data["product"]

    assert product is not None
    assert product["databaseId"] == product_id
    assert product["name"] == updated_name
