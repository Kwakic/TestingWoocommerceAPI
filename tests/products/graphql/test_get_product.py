def test_get_product(graphql_client):
    """
    We can retrieve a product we created ourselves
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
