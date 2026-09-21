import pytest
import logging

from EcommerceAPI.src.products.validators.product_validators import (
    assert_product_exists_and_matches_api,
    assert_product_creation_failed,
)

# from jsonschema import validate
#
# from EcommerceAPI.src.utils.generic_utilities import generate_random_string
# from EcommerceAPI.src.customers.validators.customer_validators import (
#     assert_customer_creation_failed,
# )
#
# from tests.shared.contracts.error_schema import error_schema


logger = logging.getLogger(
    __name__
)  # logger.setLevel(logging.DEBUG) --> Already set in pytest.ini

pytestmark = [pytest.mark.products, pytest.mark.integration]


# ---------------------------
# 🧪 Test: Minimal Product Creation
# ---------------------------
@pytest.mark.sanity
@pytest.mark.smoke
@pytest.mark.contract
def test_create_single_simple_product(
    product_helper,
    products_dao,
    create_valid_product,
):
    """
    Create a simple product using the minimum valid payload.

    The fixture `create_valid_product` already performs:

        - POST /products
        - status code validation (201)
        - response structure validation (Pydantic)
        - cleanup registration

    Test flow:

        1. Create a simple product
        2. Fetch product via API
        3. Verify API data matches database record
    """

    # -------------------------------------------
    # Step 1 — Create product
    # -------------------------------------------
    logger.info("🛠 Creating a test product via factory fixture.")

    product = create_valid_product()

    product_id = product["id"]

    # -------------------------------------------
    # Step 2 — Verify API response matches DB
    # -------------------------------------------
    api_product = product_helper.get_product_by_id(product_id=product_id)
    db_product = products_dao.get_product_by_id(product_id)

    assert_product_exists_and_matches_api(
        [api_product],
        product_id,
        db_product,
    )

    logger.info(
        "🎯 Full validation complete for product ID: %r",
        product_id,
    )


# ---------------------------
# 🧪 Test: Bulk Product Creation
# ---------------------------
@pytest.mark.regression
@pytest.mark.contract
@pytest.mark.parametrize("product_count", [1, 3, 5])
def test_create_multiple_products(
    create_valid_product,
    product_count,
):
    """
    Verify that multiple valid products can be created successfully.

    Each product is created through the shared factory fixture, which owns
    POST status validation, response validation and cleanup registration.
    """

    created_products = [
        create_valid_product(name=f"Bulk Product {index + 1}")
        for index in range(product_count)
    ]

    assert len(created_products) == product_count

    product_ids = [product["id"] for product in created_products]

    assert len(set(product_ids)) == product_count


# ---------------------------
# 🧪 Test: Populated Product Creation
# ---------------------------
@pytest.mark.regression
@pytest.mark.contract
def test_create_product_with_populated_fields(
    product_helper,
    products_dao,
    create_valid_product,
):
    """
    Verify that commonly used product fields are accepted and persisted.
    """

    product = create_valid_product(
        name="Created Populated Product",
        type="simple",
        regular_price="49.99",
        description="Product created with populated fields.",
        short_description="Populated product test.",
        sku="CREATE-POPULATED-001",
    )

    product_id = product["id"]

    api_product = product_helper.get_product_by_id(product_id=product_id)
    db_product = products_dao.get_product_by_id(product_id)

    assert_product_exists_and_matches_api(
        [api_product],
        product_id,
        db_product,
    )

    assert api_product["name"] == "Created Populated Product"
    assert api_product["type"] == "simple"
    assert api_product["regular_price"] == "49.99"
    assert api_product["sku"] == "CREATE-POPULATED-001"


# ---------------------------------------------------------------------
# 🧪 Test: Product Pricing (regular price and sale price combinations)
# ---------------------------------------------------------------------
@pytest.mark.regression
@pytest.mark.contract
@pytest.mark.parametrize(
    "regular_price,sale_price",
    [
        ("10.00", None),
        ("49.99", "39.99"),
        ("100.00", "79.99"),
    ],
)
def test_create_product_with_valid_prices(
    product_helper,
    create_valid_product,
    regular_price,
    sale_price,
):
    """
    Verify that valid regular and sale prices are accepted during creation.
    """

    product = create_valid_product(
        name=f"Price Product {regular_price}",
        regular_price=regular_price,
        **({"sale_price": sale_price} if sale_price is not None else {}),
    )

    product_id = product["id"]

    api_product = product_helper.get_product_by_id(product_id=product_id)

    assert api_product["id"] == product_id
    assert api_product["regular_price"] == regular_price

    if sale_price is not None:
        assert api_product["sale_price"] == sale_price


# ---------------------------
# 🧪 Test: Product SKU
# ---------------------------
@pytest.mark.regression
@pytest.mark.contract
def test_create_product_with_unique_sku(
    product_helper,
    products_dao,
    create_valid_product,
):
    """
    Verify that a product can be created with a unique SKU and that the
    SKU is persisted through the API and database.
    """

    sku = "CREATE-SKU-001"

    product = create_valid_product(
        name="SKU Product",
        sku=sku,
    )

    product_id = product["id"]

    api_product = product_helper.get_product_by_id(product_id=product_id)
    db_product = products_dao.get_product_by_id(product_id)

    assert api_product["sku"] == sku

    assert_product_exists_and_matches_api(
        [api_product],
        product_id,
        db_product,
    )


# ---------------------------
# ⚠️ Test: Duplicate Product SKU
# ---------------------------
@pytest.mark.negative
@pytest.mark.contract
@pytest.mark.regression
def test_create_product_with_duplicate_sku(
    create_valid_product,
    product_api_raw,
):
    """
    Negative test: creating a second product with an existing SKU
    should be rejected by WooCommerce.

    The raw API fixture is used because this test must inspect the
    actual HTTP response from the failing POST.
    """

    sku = "DUPLICATE-SKU-001"

    # Create the valid precondition through the factory fixture.
    create_valid_product(
        name="Original SKU Product",
        sku=sku,
    )

    payload = {
        "name": "Duplicate SKU Product",
        "type": "simple",
        "sku": sku,
    }

    http_response = product_api_raw.post(
        endpoint="products",
        payload=payload,
    )

    assert http_response.status_code == 400, (
        f"Expected 400, got {http_response.status_code}. "
        f"Response: {http_response.text[:300]}"
    )

    response = http_response.json

    # The validator receives parsed JSON, not HttpResponse.
    assert_product_creation_failed(response)


# ---------------------------
# ⚠️ Test: Invalid Product Type
# ---------------------------
@pytest.mark.negative
@pytest.mark.contract
@pytest.mark.regression
def test_create_product_with_invalid_type(product_api_raw):
    """
    Negative test: an unsupported product type should be rejected
    by WooCommerce.
    """

    payload = {
        "name": "Invalid Type Product",
        "type": "invalid_product_type",
    }

    http_response = product_api_raw.post(
        endpoint="products",
        payload=payload,
    )

    assert http_response.status_code == 400, (
        f"Expected 400, got {http_response.status_code}. "
        f"Response: {http_response.text[:300]}"
    )

    response = http_response.json

    assert_product_creation_failed(response)
