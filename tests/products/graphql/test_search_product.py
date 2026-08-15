import pytest


pytestmark = [
    pytest.mark.integration,
    pytest.mark.graphql,
]


def test_search_product(graphql_client, graphql_resources):
    """
    Verify that a product can be found through the GraphQL product search.

    The test creates its own product, searches for a unique part of its name,
    and verifies that the created product is returned by the search.
    """

    product_name = "GraphQL Search Test Product"

    create_query = """
    mutation {
        createProduct(
            input: {
                name: "GraphQL Search Test Product"
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

    search_query = """
    query SearchProducts($search: String!) {
        products(where: { search: $search }) {
            nodes {
                databaseId
                name
            }
        }
    }
    """

    search_response = graphql_client.execute(
        search_query,
        variables={"search": product_name},
    )

    assert search_response.ok
    assert not search_response.errors

    products = search_response.data["products"]["nodes"]

    assert any(
        product["databaseId"] == product_id and product["name"] == product_name
        for product in products
    )
