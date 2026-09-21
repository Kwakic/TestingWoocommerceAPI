"""GET /products test coverage.

Covers:
- GET product by ID happy path
- GET product by ID with API/DB consistency
- GET non-existent product
- GET product with populated fields
"""

import logging

import pytest

from EcommerceAPI.src.products.validators.product_validators import (
    assert_product_identity,
    assert_product_not_found_error,
    assert_product_retrieved_successfully,
)
from EcommerceAPI.src.products.validators.product_db_validators import (
    assert_product_matches_db,
)

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.products, pytest.mark.integration]


# ---------------------------------------
# 🧪 Test: GET Product By ID
# ---------------------------------------
@pytest.mark.sanity
@pytest.mark.smoke
@pytest.mark.contract
def test_get_product_by_id(
    product_helper,
    create_valid_product,
):
    """
    Verify that a product can be retrieved successfully by ID.
    """

    product = create_valid_product()

    product_id = product["id"]
    product_name = product["name"]

    response = product_helper.get_product_by_id(
        product_id=product_id,
        return_http_response=True,
    )

    product_model = assert_product_retrieved_successfully(response)

    assert_product_identity(
        product_model,
        product_id,
        product_name,
    )


# ---------------------------------------
# 🧪 Test: GET Product By ID — API/DB Consistency
# ---------------------------------------
@pytest.mark.integration
@pytest.mark.contract
def test_get_product_by_id_matches_db(
    product_helper,
    products_dao,
    create_valid_product,
):
    """
    Verify that a product retrieved through the API matches its database record.
    """

    product = create_valid_product()

    product_id = product["id"]

    response = product_helper.get_product_by_id(
        product_id=product_id,
        return_http_response=True,
    )

    product_model = assert_product_retrieved_successfully(response)

    db_product = products_dao.get_product_by_id(product_id)

    assert_product_matches_db(
        product_model,
        db_product,
    )


# ---------------------------------------
# 🧪 Test: GET Non-Existent Product
# ---------------------------------------
@pytest.mark.integration
@pytest.mark.contract
def test_get_nonexistent_product(product_helper):
    """
    Verify that requesting a product ID that does not exist returns 404
    with the expected WooCommerce error response.
    """

    non_existent_product_id = 999999999

    response = product_helper.get_product_by_id(
        product_id=non_existent_product_id,
        return_http_response=True,
    )

    assert response.status_code == 404, (
        f"Expected 404, got {response.status_code}. " f"Response: {response.text}"
    )

    assert_product_not_found_error(response.json)


# ---------------------------------------
# 🧪 Test: GET Product With Populated Fields
# ---------------------------------------
@pytest.mark.integration
@pytest.mark.contract
def test_get_product_with_populated_fields(
    product_helper,
    create_valid_product,
):
    """
    Verify that GET by ID returns the populated product fields supplied at creation.

    Only fields confirmed by the product fixture/model should be asserted here.
    """

    product = create_valid_product(
        name="GET Populated Product",
        type="simple",
        regular_price="49.99",
        description="Product created for GET field validation.",
        short_description="GET populated fields test.",
        sku="GET-POPULATED-001",
    )

    product_id = product["id"]

    response = product_helper.get_product_by_id(
        product_id=product_id,
        return_http_response=True,
    )

    product_model = assert_product_retrieved_successfully(response)

    assert product_model.id == product_id
    assert product_model.name == "GET Populated Product"
    assert product_model.type == "simple"
    assert product_model.regular_price == "49.99"

    # WordPress/WooCommerce may wrap descriptions in HTML (<p>...</p>).
    # Validate the persisted content without coupling the test to HTML formatting.
    assert "Product created for GET field validation." in product_model.description
    assert "GET populated fields test." in product_model.short_description

    assert product_model.sku == "GET-POPULATED-001"
