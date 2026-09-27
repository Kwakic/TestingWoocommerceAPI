"""GET /products integration test coverage.

This module verifies Product retrieval behavior through the public Product
domain fixture and keeps test-data setup separate from the GET operation
under test.

Coverage:
    - GET product by ID happy path
    - GET product by ID with API/DB consistency
    - GET non-existent product
    - GET product with populated fields

Test-data responsibility:
    - ``create_valid_product`` creates a valid Product through the standard
      Product Builder / Factory / Provisioner pipeline.
    - The fixture validates the creation response and registers the Product
      for automatic cleanup.
    - The GET tests themselves remain responsible for validating the GET
      operation and its response.

Negative tests may intentionally use direct scenario values when the invalid
or non-existent input itself is the behavior under test.
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
    Verify that a Product can be retrieved successfully by ID.

    Endpoint tested:
        GET /products/{id}

    Fixture responsibilities (``create_valid_product``):
        - POST /products
        - response validation (Pydantic)
        - automatic cleanup registration

    Test flow:
        1. Create a valid Product
        2. Retrieve the Product by ID
        3. Validate HTTP transport status
        4. Validate the Product response structure
        5. Verify the returned Product identity
    """

    # -------------------------------------------
    # 🛠 Step 1 — Create a valid Product
    # -------------------------------------------
    logger.info("🛠 Creating a test product.")

    # The fixture owns:
    #   - valid Product test-data generation
    #   - POST /products
    #   - creation response validation
    #   - automatic cleanup registration
    product = create_valid_product()

    product_id = product["id"]
    product_name = product["name"]

    # -------------------------------------------
    # 🔎 Step 2 — Retrieve Product via API
    # -------------------------------------------
    logger.info("🔎 Fetching product by ID: %s", product_id)

    # Request HttpResponse so the test can validate the HTTP status returned
    # by the GET operation under test.
    response = product_helper.get_product_by_id(
        product_id=product_id,
        return_http_response=True,
    )

    # -------------------------------------------
    # 🚦 Step 3 — Transport validation (FAIL FAST)
    # -------------------------------------------
    # The test owns the HTTP status assertion because GET /products/{id}
    # is the operation being tested.
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. " f"Response: {response.text}"
    )

    # -------------------------------------------
    # 📦 Step 4 — Response body validation
    # -------------------------------------------
    # Validators validate response data; they do not own HTTP transport
    # assertions.
    product_model = assert_product_retrieved_successfully(response)

    # -------------------------------------------
    # 🔍 Step 5 — Business validation
    # -------------------------------------------
    # Ensure the Product returned by GET is the Product created during setup.
    assert_product_identity(
        product_model,
        product_id,
        product_name,
    )

    logger.info(
        "✅ Fetched Product matches created one: ID=%s, Name=%s",
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
    Verify that a Product retrieved through the API matches its database record.

    Endpoint tested:
        GET /products/{id}

    Fixture responsibilities:
        - create a valid Product through the standard test-data pipeline
        - validate the creation response
        - register the Product for automatic cleanup

    Test flow:
        1. Create a valid Product
        2. Retrieve the Product through the API
        3. Validate the GET response structure
        4. Retrieve the same Product from the database
        5. Verify API data matches the database record
    """

    # -------------------------------------------
    # 🛠 Step 1 — Create a valid Product
    # -------------------------------------------
    logger.info("🛠 Creating a test product for API/DB consistency validation.")

    # The fixture handles Product test-data generation, provisioning,
    # creation-response validation, and ownership registration.
    product = create_valid_product()

    product_id = product["id"]

    # -------------------------------------------
    # 🔎 Step 2 — Retrieve Product via API
    # -------------------------------------------
    logger.info("🔎 Fetching product by ID: %s", product_id)

    response = product_helper.get_product_by_id(
        product_id=product_id,
        return_http_response=True,
    )

    # -------------------------------------------
    # 🚦 Step 3 — Transport validation (FAIL FAST)
    # -------------------------------------------
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. " f"Response: {response.text}"
    )

    # -------------------------------------------
    # 📦 Step 4 — Response body validation
    # -------------------------------------------
    product_model = assert_product_retrieved_successfully(response)

    # -------------------------------------------
    # 🗄 Step 5 — Retrieve Product from database
    # -------------------------------------------
    db_product = products_dao.get_product_by_id(product_id)

    # -------------------------------------------
    # 🔍 Step 6 — API vs DB consistency validation
    # -------------------------------------------
    assert_product_matches_db(
        product_model,
        db_product,
    )

    logger.info(
        "🎯 API/DB consistency validation complete for Product ID: %r",
        product_id,
    )


# ---------------------------------------
# ⚠️ Test: GET Non-Existent Product
# ---------------------------------------
@pytest.mark.negative
@pytest.mark.contract
@pytest.mark.regression
def test_get_nonexistent_product(product_helper):
    """
    Negative test for retrieving a non-existent Product.

    Endpoint tested:
        GET /products/{id}

    Test flow:
        1. Request a non-existent Product ID
        2. Validate API returns HTTP 404
        3. Validate the Product not-found error response
    """

    non_existent_product_id = 999999999

    logger.info(
        "🚫 Retrieving non-existent Product ID: %s",
        non_existent_product_id,
    )

    # No test-data provisioning is required here because the non-existent ID
    # is itself the scenario under test.
    response = product_helper.get_product_by_id(
        product_id=non_existent_product_id,
        return_http_response=True,
    )

    # -------------------------------------------
    # 🚦 Step 2 — Transport validation (FAIL FAST)
    # -------------------------------------------
    # The test owns the HTTP status assertion because the GET operation
    # is the behavior being verified.
    assert response.status_code == 404, (
        f"Expected 404, got {response.status_code}. " f"Response: {response.text}"
    )

    # -------------------------------------------
    # 📦 Step 3 — Error response validation
    # -------------------------------------------
    assert_product_not_found_error(response.json)

    logger.info(
        "✅ Product not-found error validated for ID: %s",
        non_existent_product_id,
    )


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
    Verify that GET by ID returns the populated Product fields supplied
    during test-data setup.

    Endpoint tested:
        GET /products/{id}

    Test-data responsibility:
        ``create_valid_product`` provisions the Product using the standard
        Product Builder / Factory / Provisioner pipeline.

    Test flow:
        1. Create a Product with explicitly populated fields
        2. Retrieve the Product by ID
        3. Validate the response structure
        4. Verify the populated fields were persisted and returned

    Only fields confirmed by the Product fixture/model should be asserted
    here.
    """

    # -------------------------------------------
    # 🛠 Step 1 — Create Product with scenario-specific data
    # -------------------------------------------
    product = create_valid_product(
        name="GET Populated Product",
        type="simple",
        regular_price="49.99",
        description="Product created for GET field validation.",
        short_description="GET populated fields test.",
        sku="GET-POPULATED-001",
    )

    product_id = product["id"]

    # The fixture handles the creation pipeline and cleanup. The test only
    # supplies the values that are relevant to this GET scenario.

    # -------------------------------------------
    # 🔎 Step 2 — Retrieve Product via API
    # -------------------------------------------
    response = product_helper.get_product_by_id(
        product_id=product_id,
        return_http_response=True,
    )

    # -------------------------------------------
    # 🚦 Step 3 — Transport validation (FAIL FAST)
    # -------------------------------------------
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. " f"Response: {response.text}"
    )

    # -------------------------------------------
    # 📦 Step 4 — Response body validation
    # -------------------------------------------
    product_model = assert_product_retrieved_successfully(response)

    # -------------------------------------------
    # 🔍 Step 5 — Business validation
    # -------------------------------------------
    assert product_model.id == product_id
    assert product_model.name == "GET Populated Product"
    assert product_model.type == "simple"
    assert product_model.regular_price == "49.99"

    # WordPress/WooCommerce may wrap descriptions in HTML (<p>...</p>).
    # Validate the persisted content without coupling the test to HTML formatting.
    assert "Product created for GET field validation." in product_model.description
    assert "GET populated fields test." in product_model.short_description

    assert product_model.sku == "GET-POPULATED-001"

    logger.info(
        "🎯 Populated Product GET validation complete for ID: %r",
        product_id,
    )
