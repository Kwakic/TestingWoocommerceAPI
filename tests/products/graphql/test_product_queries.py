def test_get_products(graphql_client):
    response = graphql_client.execute(
        """
        {
            products(first: 1) {
                nodes {
                    databaseId
                    name
                }
            }
        }
        """
    )

    assert response.ok
