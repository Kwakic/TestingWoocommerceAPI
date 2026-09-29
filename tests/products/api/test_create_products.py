"""Product creation integration tests.

Product creation flow used by valid-data tests:

    Test
      ↓
    create_valid_product fixture
      ↓
    ProductBuilder
      ↓
    ProductFactory
      ↓
    ProductProvisioner
      ↓
    ProductsHelper
      ↓
    ProductsApi
      ↓
    APIClient / HttpClient
      ↓
    WooCommerce

Responsibilities:

- ProductFactory generates valid Product creation data in memory.
- ProductBuilder customizes scenario-specific fields when required.
- ProductProvisioner sends the prepared Product data to the application.
- ProductsHelper orchestrates domain-level API operations.
- ProductsApi exposes the WooCommerce Product endpoint.
- The create_valid_product fixture validates the creation response and
  registers created Products for cleanup.

Tests should provide only scenario-specific data. They should not perform
test-data provisioning directly.

Negative tests may intentionally bypass the valid-data pipeline when the
invalid payload itself is the scenario under test.
"""

import pytest
import logging

from EcommerceAPI.src.products.validators.product_validators import (
    assert_product_exists_and_matches_api,
    assert_product_creation_failed,
)
from EcommerceAPI.src.test_data.factories.products.product_factory import ProductFactory

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
    logger.info("🛠 Creating a test product.")

    # By default, CustomerFactory generates the customer data.
    # To override a value for this scenario, pass it directly to the fixture:
    #
    #     customer = create_valid_customer(email="john.smith.12345@test.com")
    #
    # The fixture passes the override to CustomerBuilder → CustomerFactory.
    # Only the specified value is overridden; all other fields are generated.
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


@pytest.mark.regression
@pytest.mark.contract
def test_create_product_with_generated_sale_price(
    product_helper,
    create_valid_product,
):
    """
    Verify that a Product can be created with a sale price generated by
    ProductFactory and that the generated pricing relationship is accepted
    and persisted by WooCommerce.

    Test-data responsibility:

        ProductFactory
            ↓
        Generate regular_price / sale_price relationship

    Product creation responsibility:

        create_valid_product
            ↓
        ProductBuilder
            ↓
        ProductFactory
            ↓
        ProductProvisioner
            ↓
        ProductsHelper / ProductsApi
            ↓
        WooCommerce

    ProductFactory is used directly here only because the scenario explicitly
    requires a generated sale price.The test does not provision the Product
    through the Factory or Provisioner directly.

    The create_valid_product fixture remains responsible for:

        - building the final valid creation data
        - provisioning the Product
        - validating the HTTP 201 response
        - validating the response structure
        - registering the Product for cleanup
        - returning the created Product data

    This keeps test-data generation separate from Product API orchestration.

    Test flow:
        1. Generate a sale price from a known regular price.
        2. Create the Product through the standard Product fixture.
        3. Retrieve the created Product through the API.
        4. Verify the regular and generated sale prices.
        5. Verify that the sale price is lower than the regular price.
    """

    # ------------------------------------------------------------------
    # Step 1 — Arrange: generate scenario-specific pricing data
    # ------------------------------------------------------------------
    regular_price = 100.00

    # ProductFactory owns test-data generation. ProductsHelper must remain
    # responsible for API orchestration rather than generating test values.
    sale_price, discount_percentage = ProductFactory.generate_sale_price(regular_price)

    # ------------------------------------------------------------------
    # Step 2 — Act: create the Product through the standard fixture pipeline
    # ------------------------------------------------------------------
    product = create_valid_product(
        name="Generated Sale Price Product",
        regular_price=f"{regular_price:.2f}",
        sale_price=sale_price,
    )

    product_id = product["id"]

    # ------------------------------------------------------------------
    # Step 3 — Assert: verify the generated pricing persisted through API
    # ------------------------------------------------------------------
    api_product = product_helper.get_product_by_id(product_id=product_id)

    assert api_product["id"] == product_id
    assert api_product["regular_price"] == f"{regular_price:.2f}"
    assert api_product["sale_price"] == sale_price

    # The generated sale price must remain below the regular price.
    assert float(api_product["sale_price"]) < float(api_product["regular_price"])

    logger.info(
        "Generated sale price %.2f with %.2f%% discount.",
        float(sale_price),
        discount_percentage,
    )


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
