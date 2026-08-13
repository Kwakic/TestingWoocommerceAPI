def test_graphql_returns_errors_for_invalid_field(graphql_client):
    """
    GraphQL can return HTTP 200 while containing GraphQL errors
    """

    query = """
    {
        products(first: 1) {
            nodes {
                definitelyNotARealProductField
            }
        }
    }
    """

    response = graphql_client.execute(query)

    assert response.status_code == 200
    assert response.errors
