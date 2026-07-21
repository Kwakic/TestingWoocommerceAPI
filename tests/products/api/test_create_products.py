import pytest
import logging

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
@pytest.mark.tcid("TCID-026")
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
    product_helper.assert_product_exists_and_matches_db(
        product_id=product_id,
        dao=products_dao,
    )

    logger.info(
        "🎯 Full validation complete for product ID: %r",
        product_id,
    )
