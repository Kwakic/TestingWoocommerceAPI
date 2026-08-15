from EcommerceAPI.src.utils.generic_utilities import safe_product_name

import pytest


pytestmark = [
    pytest.mark.integration,
    pytest.mark.graphql,
]


def test_filter_product_by_sku(graphql_client, graphql_resources):
    """
    Verify that products can be filtered by SKU through GraphQL.

    The test creates its own product with a unique SKU, filters the product
    collection by that SKU, and verifies that the created product is returned.
    """

    product_name = safe_product_name("GraphQL-SKU-Filter-Test-Product")
    product_sku = safe_product_name("graphql-filter-sku")

    create_query = """
    mutation CreateSkuFilterProduct($name: String!, $sku: String!) {
        createProduct(
            input: {
                name: $name
                sku: $sku
            }
        ) {
            product {
                databaseId
                name
                sku
            }
        }
    }
    """

    create_response = graphql_client.execute(
        create_query,
        variables={"name": product_name, "sku": product_sku},
    )

    assert create_response.ok
    assert not create_response.errors

    created_product = create_response.data["createProduct"]["product"]
    product_id = created_product["databaseId"]

    # Register the GraphQL-created product with the shared framework so the
    # existing product cleanup runs automatically during fixture teardown.
    graphql_resources(product_id)

    assert created_product["name"] == product_name
    assert created_product["sku"] == product_sku

    filter_query = """
    query FilterProductsBySku($sku: String!) {
        products(where: { sku: $sku }) {
            nodes {
                databaseId
                name
                sku
            }
        }
    }
    """

    filter_response = graphql_client.execute(
        filter_query,
        variables={"sku": product_sku},
    )

    assert filter_response.ok
    assert not filter_response.errors

    products = filter_response.data["products"]["nodes"]

    assert any(
        product["databaseId"] == product_id
        and product["name"] == product_name
        and product["sku"] == product_sku
        for product in products
    )


def test_filter_product_by_category(graphql_client, graphql_resources):
    """
    Verify that products can be filtered by product category through GraphQL.

    The test creates its own product category, creates a product assigned to
    that category, filters the product collection by the category ID, and
    verifies that the created product is returned.
    """

    category_name = safe_product_name("GraphQL-Category-Filter-Test-Category")
    product_name = safe_product_name("GraphQL-Category-Filter-Test-Product")

    create_category_query = """
    mutation CreateCategoryFilterCategory($name: String!) {
        createProductCategory(
            input: {
                name: $name
            }
        ) {
            productCategory {
                databaseId
                name
            }
        }
    }
    """

    category_response = graphql_client.execute(
        create_category_query,
        variables={"name": category_name},
    )

    assert category_response.ok
    assert not category_response.errors

    created_category = category_response.data["createProductCategory"][
        "productCategory"
    ]
    category_id = created_category["databaseId"]

    assert created_category["name"] == category_name

    create_product_query = """
    mutation CreateCategoryFilterProduct(
        $category_id: Int!
        $name: String!
    ) {
        createProduct(
            input: {
                name: $name
                categories: [$category_id]
            }
        ) {
            product {
                databaseId
                name
            }
        }
    }
    """

    product_response = graphql_client.execute(
        create_product_query,
        variables={"category_id": category_id, "name": product_name},
    )

    assert product_response.ok
    assert not product_response.errors

    created_product = product_response.data["createProduct"]["product"]
    product_id = created_product["databaseId"]

    # Register the GraphQL-created product with the shared framework so the
    # existing product cleanup runs automatically during fixture teardown.
    graphql_resources(product_id)

    assert created_product["name"] == product_name

    filter_query = """
    query FilterProductsByCategory($category_id: Int!) {
        products(where: { categoryId: $category_id }) {
            nodes {
                databaseId
                name
            }
        }
    }
    """

    filter_response = graphql_client.execute(
        filter_query,
        variables={"category_id": category_id},
    )

    assert filter_response.ok
    assert not filter_response.errors

    products = filter_response.data["products"]["nodes"]

    assert any(
        product["databaseId"] == product_id and product["name"] == product_name
        for product in products
    )
