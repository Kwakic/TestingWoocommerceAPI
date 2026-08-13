from EcommerceAPI.src.auth.auth_resolver import resolve_auth
from EcommerceAPI.src.clients.graphql_client import GraphQLClient
from EcommerceAPI.src.configs.config_graphql import get_graphql_host


def test_graphql_oauth1_create_product():
    auth = resolve_auth()

    client = GraphQLClient(
        base_url=get_graphql_host(),
    )

    response = client.http.request(
        method="POST",
        url=client.base_url,
        headers={"Content-Type": "application/json"},
        json={
            "query": """
                mutation {
                    createProduct(
                        input: {
                            name: "GraphQL OAuth Test Product"
                        }
                    ) {
                        product {
                            databaseId
                            name
                        }
                    }
                }
            """
        },
        auth=auth.oauth,
    )

    print(response.status_code)
    print(response.text)

    assert response.status_code == 200
