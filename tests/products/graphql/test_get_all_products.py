import logging

import pytest

from EcommerceAPI.src.utils.generic_utilities import generate_random_string

from EcommerceAPI.src.utils.generic_utilities import safe_product_name


logger = logging.getLogger(__name__)

pytestmark = [
    pytest.mark.integration,
    pytest.mark.graphql,
]


@pytest.mark.tcid("TCID-XXX")
@pytest.mark.contract
@pytest.mark.regression
def test_get_all_products_pagination(
    graphql_client,
    graphql_resources,
):
    """
    Verify cursor-based pagination for the GraphQL Product collection.

    The test creates a controlled dataset so that pagination does not depend
    on products already present in the database. The GraphQL collection is
    scoped with a unique search token so only products created by this test
    are included in the paginated result set.

    Test flow:
        1. Create a controlled set of products.
        2. Register every created product with the shared cleanup framework.
        3. Request the first page using a small `first` value.
        4. Follow `pageInfo.endCursor` while `hasNextPage` is True.
        5. Aggregate all returned products.
        6. Verify the expected number of products was retrieved.
        7. Verify pagination actually required multiple pages.
        8. Verify there are no duplicate product IDs.
        9. Verify all products created by this test were returned.

    GraphQL pagination uses cursors rather than the REST API's page/per_page
    parameters, so this test intentionally exercises GraphQL's native
    connection pagination instead of the REST pagination utility.
    """

    # --------------------------------------------------
    # Test configuration
    # --------------------------------------------------

    # Small page size is intentional: 12 products with first=5 guarantees
    # that the test must traverse multiple GraphQL pages.
    first = 5  # per page
    qty = 12

    logger.info(
        "Creating %s products for GraphQL pagination test (first=%s)",
        qty,
        first,
    )

    # --------------------------------------------------
    # Step 1 — Create controlled dataset
    # --------------------------------------------------

    created_product_ids = []
    created_product_names = []

    # Use one unique token for the whole test dataset so the paginated query
    # can retrieve ONLY the products created by this test.
    search_token = f"GraphQL-Pagination-{generate_random_string(8)}"

    create_query = """
    mutation CreatePaginationProduct($name: String!) {
        createProduct(
            input: {
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

    for index in range(qty):
        product_name = safe_product_name(f"{search_token}-Product-{index}")

        create_response = graphql_client.execute(
            create_query,
            variables={"name": product_name},
        )

        # GraphQL can return HTTP 200 even when the operation failed.
        # Therefore both the GraphQL success flag and error collection
        # must be checked.
        assert create_response.ok, (
            f"❌ Product creation failed for '{product_name}'. "
            f"GraphQL errors: {create_response.errors}"
        )
        assert not create_response.errors, (
            f"❌ GraphQL errors while creating '{product_name}': "
            f"{create_response.errors}"
        )

        created_product = create_response.data["createProduct"]["product"]

        product_id = created_product["databaseId"]

        assert (
            product_id
        ), f"❌ Created product '{product_name}' did not return a databaseId"

        # Register the product with the EXISTING shared cleanup mechanism.
        # graphql_resources does not delete anything itself; it simply tells
        # shared_api_resources that this Product must be cleaned up later.
        graphql_resources(product_id)

        created_product_ids.append(product_id)
        created_product_names.append(product_name)

    logger.info(
        "Created %s products for pagination test: IDs=%s",
        len(created_product_ids),
        created_product_ids,
    )

    # --------------------------------------------------
    # Step 2 — Define paginated GraphQL query
    # --------------------------------------------------

    products_query = """
    query GetProductsPage(
        $first: Int!
        $after: String
        $search: String!
    ) {
        products(
            first: $first
            after: $after
            where: {
                search: $search
            }
        ) {
            nodes {
                databaseId
                name
            }
            pageInfo {
                hasNextPage
                endCursor
            }
        }
    }
    """

    # --------------------------------------------------
    # Step 3 — Traverse all GraphQL pages
    # --------------------------------------------------

    all_products = []
    cursor = None
    page_number = 0

    while True:
        page_number += 1

        logger.info(
            "Fetching GraphQL products page %s (first=%s, search=%s, after=%s)",
            page_number,
            first,
            search_token,
            cursor,
        )

        response = graphql_client.execute(
            products_query,
            variables={
                "first": first,
                "after": cursor,
                "search": search_token,
            },
        )

        # HTTP 200 alone is NOT sufficient for GraphQL.
        assert response.ok, (
            f"❌ GraphQL product page {page_number} failed. "
            f"HTTP={response.status_code}, errors={response.errors}"
        )
        assert not response.errors, (
            f"❌ GraphQL errors on product page {page_number}: " f"{response.errors}"
        )

        products_connection = response.data["products"]

        page_products = products_connection["nodes"]
        page_info = products_connection["pageInfo"]

        logger.info(
            "Page %s → %s products | hasNextPage=%s | endCursor=%s",
            page_number,
            len(page_products),
            page_info["hasNextPage"],
            page_info["endCursor"],
        )

        all_products.extend(page_products)

        # GraphQL tells us whether another page exists.
        if not page_info["hasNextPage"]:
            break

        # The cursor returned by this page becomes the `after` cursor
        # for the next request.
        cursor = page_info["endCursor"]

        assert cursor, (
            f"❌ GraphQL reported hasNextPage=True on page {page_number} "
            "but returned no endCursor"
        )

    # --------------------------------------------------
    # Step 4 — Basic response validation
    # --------------------------------------------------

    assert all_products, "❌ GraphQL returned no products"

    assert isinstance(
        all_products, list
    ), f"Expected product list, got: {type(all_products)}"

    logger.info(
        "GraphQL pagination returned %s products across %s pages",
        len(all_products),
        page_number,
    )

    # --------------------------------------------------
    # Step 5 — Verify deterministic result size
    # --------------------------------------------------

    assert len(all_products) == qty, (
        f"❌ Expected exactly {qty} products from the controlled dataset, "
        f"got {len(all_products)}"
    )

    # --------------------------------------------------
    # Step 6 — Verify pagination actually occurred
    # --------------------------------------------------

    assert page_number > 1, (
        "❌ Pagination did not occur — all products were returned "
        "in a single GraphQL page"
    )

    logger.info(
        "✅ Pagination confirmed: %s products retrieved across %s pages",
        len(all_products),
        page_number,
    )

    # --------------------------------------------------
    # Step 7 — Verify no duplicate products
    # --------------------------------------------------

    returned_ids = [product["databaseId"] for product in all_products]

    assert len(returned_ids) == len(
        set(returned_ids)
    ), "❌ Duplicate product IDs found across paginated GraphQL results"

    logger.info("✅ No duplicate products found across pages")

    # --------------------------------------------------
    # Step 8 — Verify every product created by this test
    #         was returned
    # --------------------------------------------------

    returned_id_set = set(returned_ids)

    missing_ids = set(created_product_ids) - returned_id_set

    assert not missing_ids, (
        f"❌ Products created by this test were missing from paginated "
        f"results: {sorted(missing_ids)}"
    )

    logger.info(
        "✅ All %s products created by this test were returned",
        qty,
    )

    # --------------------------------------------------
    # Step 9 — Verify returned product names
    # --------------------------------------------------

    returned_names = {product["name"] for product in all_products}

    missing_names = set(created_product_names) - returned_names

    assert not missing_names, (
        f"❌ Created products missing from paginated results: "
        f"{sorted(missing_names)}"
    )

    logger.info("🎯 GraphQL product pagination test completed successfully")
