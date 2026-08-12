def test_graphql_endpoint(graphql_client):
    response = graphql_client.execute(
        """
        {
            __typename
        }
        """
    )

    assert response.ok
