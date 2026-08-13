def test_delete_product(graphql_client):
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
            }
        ) {
            deletedProductId
        }
    }
    """

    delete_response = graphql_client.execute(
        delete_query,
        variables={"id": product_id},
    )

    assert delete_response.ok
    assert not delete_response.errors

    deleted_product_id = delete_response.data["deleteProduct"]["deletedProductId"]

    assert deleted_product_id == product_id

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

    assert get_response.ok
    assert not get_response.errors

    assert get_response.data["product"] is None
