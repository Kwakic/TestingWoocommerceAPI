import pytest

pytestmark = [
    pytest.mark.integration,
    pytest.mark.graphql,
]


def test_create_product(graphql_client):
    """
    Verify that an authenticated GraphQL mutation creates a real product.

    The test creates the product through GraphQL and verifies that the
    response contains a valid database ID and the expected product name.
    """

    query = """
    mutation {
        createProduct(
            input: {
                name: "GraphQL Test Product"
            }
        ) {
            product {
                databaseId
                name
            }
        }
    }
    """

    response = graphql_client.execute(query)

    assert response.ok
    assert not response.errors

    product = response.data["createProduct"]["product"]

    assert product["databaseId"] > 0
    assert product["name"] == "GraphQL Test Product"
