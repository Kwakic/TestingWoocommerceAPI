import pytest

pytestmark = [
    pytest.mark.integration,
    pytest.mark.graphql,
]


def test_get_product(graphql_client, graphql_resources):
    """
    Verify that a product created by the test can be retrieved by database ID.

    The test creates its own product, captures its database ID, queries that
    exact product, and verifies the returned product data.
    """

    create_query = """
    mutation {
        createProduct(
            input: {
                name: "GraphQL Query Test Product"
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

    query = """
    query GetProduct($id: ID!) {
        product(id: $id, idType: DATABASE_ID) {
            databaseId
            name
        }
    }
    """

    response = graphql_client.execute(
        query,
        variables={"id": product_id},
    )

    assert response.ok
    assert not response.errors

    product = response.data["product"]

    assert product is not None
    assert product["databaseId"] == product_id
    assert product["name"] == "GraphQL Query Test Product"
