"""
This proves the entire chain:

pytest
 ↓
graphql_client fixture
 ↓
credentials
 ↓
BasicAuth
 ↓
GraphQLClient
 ↓
HttpClient
 ↓
WordPress Application Password
 ↓
WPGraphQL
 ↓
WooGraphQL
 ↓
createProduct
 ↓
real database record

"""


def test_create_product(graphql_client):
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
