import pytest


pytestmark = [
    pytest.mark.negative,
    pytest.mark.graphql,
]


def test_graphql_returns_errors_for_invalid_field(graphql_client):
    """
    Verify that GraphQL schema errors are reported independently of HTTP status.

    The test deliberately requests one valid Product field and one field that
    does not exist in the GraphQL schema. This makes the intent explicit:
    ``databaseId`` is a known valid Product field used by the Product GraphQL
    tests, while ``definitelyNotARealProductField`` is intentionally invalid.

    GraphQL should reject the operation while still returning HTTP 200 and
    exposing the failure through the ``errors`` collection.

    This protects an important GraphQL response rule: HTTP success does not
    necessarily mean that the GraphQL operation succeeded.
    """

    query = """
    query InvalidProductField {
        products(first: 1) {
            nodes {
                # Known valid Product field used throughout the GraphQL tests.
                databaseId

                # Deliberately invalid field used to exercise schema validation.
                definitelyNotARealProductField
            }
        }
    }
    """

    response = graphql_client.execute(query)

    assert response.status_code == 200
    assert response.errors
    assert not response.ok

    # Verify that the schema rejected the field we intentionally requested.
    assert "definitelyNotARealProductField" in response.errors[0]["message"]


def test_graphql_returns_errors_for_nonexistent_product_update(graphql_client):
    """
    Verify that updating a Product after it has been deleted returns a
    GraphQL-level error.

    The test deliberately creates and then permanently deletes a real Product
    before attempting the update. This is deterministic and avoids relying on
    an arbitrary ID such as ``999999999`` not existing in the database.

    The update request itself is valid according to the GraphQL schema, so this
    exercises resolver/business-level error handling rather than schema
    validation.

    GraphQL is expected to return HTTP 200 because the request was successfully
    processed at the HTTP level. The failed mutation is therefore detected by
    checking ``response.errors`` and ``response.ok``.

    The Product is explicitly deleted before the negative update, so no shared
    cleanup registration is required for this test.
    """

    create_query = """
    mutation CreateErrorHandlingProduct {
        createProduct(
            input: {
                name: "GraphQL Error Handling Test Product"
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

    product_id = create_response.data["createProduct"]["product"]["databaseId"]

    delete_query = """
    mutation DeleteErrorHandlingProduct($id: ID!) {
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
    assert delete_response.data["deleteProduct"]["product"]["databaseId"] == product_id

    # The Product now definitely existed and was permanently deleted.
    # Updating this captured ID therefore exercises the "resource no longer
    # exists" path without depending on database state outside this test.
    update_query = """
    mutation UpdateDeletedProduct($id: ID!, $name: String!) {
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

    response = graphql_client.execute(
        update_query,
        variables={
            "id": product_id,
            "name": "GraphQL Invalid Update Product",
        },
    )

    assert response.status_code == 200
    assert response.errors
    assert not response.ok

    # The resolver should identify the failing mutation field when GraphQL
    # provides a path in its error payload.
    error = response.errors[0]
    if isinstance(error, dict) and error.get("path"):
        assert error["path"] == ["updateProduct"]
