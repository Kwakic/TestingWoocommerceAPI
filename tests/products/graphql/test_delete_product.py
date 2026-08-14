import pytest

pytestmark = [
    pytest.mark.integration,
    pytest.mark.graphql,
]


def test_delete_product(graphql_client):
    """
    Verify that a product can be permanently deleted through GraphQL.

    The test creates its own product to avoid relying on pre-existing
    database state, permanently deletes it using ``force: true``, and
    verifies that the product can no longer be retrieved by its database ID.

    The final lookup intentionally expects a GraphQL error indicating that
    the product does not exist. WPGraphQL returns HTTP 200 with
    ``data.product = null`` and an error entry for this expected condition,
    so the final assertion validates the response data rather than using
    ``GraphQLResponse.ok``.

    Args:
        graphql_client: Authenticated GraphQL client fixture.
    """
    create_query = """
    mutation {
        createProduct(
            input: {
                name: "GraphQL Delete Test Product"
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

    delete_query = """
    mutation DeleteProduct($id: ID!) {
        deleteProduct(
            input: {
                id: $id
                force: true
            }
        ) {
            product {
                databaseId
                name
            }
        }
    }
    """

    delete_response = graphql_client.execute(
        delete_query,
        variables={"id": product_id},
    )

    assert delete_response.ok
    assert not delete_response.errors

    deleted_product = delete_response.data["deleteProduct"]["product"]

    assert deleted_product["databaseId"] == product_id

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

    assert get_response.status_code == 200
    assert get_response.data["product"] is None
