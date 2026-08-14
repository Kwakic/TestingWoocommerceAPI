import pytest

pytestmark = [
    pytest.mark.negative,
    pytest.mark.graphql,
]


def test_graphql_returns_errors_for_invalid_field(graphql_client):
    """
    Verify that GraphQL errors are detected independently of HTTP status.

    The test requests a deliberately invalid product field and verifies that
    GraphQL returns HTTP 200 while populating the errors collection.

    This validates the framework's GraphQL response semantics: HTTP success
    does not necessarily mean that the GraphQL operation succeeded.
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
