# EcommerceAPI/src/validators/products/product_validators.py
# business validation
"""
Product Validation Layer

This module contains domain-level validators for the Products API.

Responsibilities
----------------
• Validate API response structure using Pydantic
• Validate dataset responses (list endpoints)
• Validate business rules
• Validate API + database consistency

Important design rule:
Validators ONLY validate data.

They must NOT:
    - call APIs
    - query databases
    - orchestrate workflows

Data fetching is handled by:
    Tests or Helpers.

Architecture
------------
TEST / HELPER
      ↓
API CLIENT
      ↓
HttpResponse
      ↓
VALIDATORS
      ↓
Pydantic Models
      ↓
DB Validators

assert_valid_product_response → Structure validation (STRUCTURE)
assert_single_product_by_email → API validation (DATASET)
assert_product_creation_failed → error validation (SCENARIOS)
assert_product_not_found_error → error validation (SCENARIOS)
assert_product_error_response → error validation (BASE)
assert_product_retrieved_successfully → Transport validation (TRANSPORT)
assert_product_exists_and_matches_api → API + DB validation (INTEGRATION)
assert_product_identity() → Identity validation (BUSINESS)

"""

from typing import List, Dict, Any
import logging

from EcommerceAPI.src.core.http_response import HttpResponse
from EcommerceAPI.src.products.validators.product_db_validators import (
    assert_product_matches_db,
)


from EcommerceAPI.src.products.models.product_model import ProductModel

logger = logging.getLogger(__name__)


# -------------------------------------------------------
# 🧱 STRUCTURE VALIDATION
# -------------------------------------------------------
def assert_valid_product_response(product: Dict[str, Any]) -> ProductModel:
    """
    Validate the structure of a products API response.

    This function performs **structure validation** using the Pydantic
    `ProductModel`.

    Purpose:
        - Ensure required fields exist
        - Ensure correct field types
        - Validate email format

    Args:
        product:
            Raw products dictionary returned by the API.

    Returns:
        ProductModel:
            Validated products object.

    Raises:
        ValidationError:
            If the response structure is invalid.
    """
    # Pydantic parses and validates the dictionary.
    # If anything is wrong (missing fields, wrong types, invalid email) Pydantic raises a ValidationError immediately.
    product_model = ProductModel(
        **product
    )  # This is a dictionary unpacking. Take all key-value pairs from the
    # products dict and pass them as named arguments.

    logger.info(
        "✅ Product structure valid: id=%s, email=%s",
        product_model.id,
        product_model.email,
    )

    # -------------------------------------------------------
    # 📦 Return typed object
    # -------------------------------------------------------
    # Returning the model allows downstream validators to safely access fields using dot notation.
    return product_model  # example: ProductModel(id=1452, email='testuser_cfitmuyfvq@supersqa.com',
    # username='testuser_cfitmuyfvq')


def assert_single_product_by_email(
    products: List[Dict[str, Any]], email: str
) -> ProductModel:
    """
    Validate that exactly ONE products exists for a given email in a dataset response (list endpoint).

    Typical use cases:
        - GET /products
        - GET /products?email=
        - paginated dataset responses

    This validator performs:
        1. Filter dataset by email
        2. Ensure exactly one match exists
        3. Validate structure using Pydantic

    Returns:
        ProductModel (validated object)
    """

    matches = [c for c in products if c.get("email") == email]

    assert (
        len(matches) == 1
    ), f"❌ Expected 1 products for {email}, found {len(matches)}"

    # Validate structure via Pydantic
    product_model = assert_valid_product_response(matches[0])

    logger.info(
        "✅ Product found in dataset: id=%s email=%s",
        product_model.id,
        product_model.email,
    )

    return product_model


def assert_product_creation_failed(response: dict):
    """
    Validate products creation failure (business + contract level).

    IMPORTANT:
    - This function expects a parsed JSON dict (NOT HttpResponse)
    - Status code must be validated BEFORE calling this function

    Validates:
        - error code
        - error message
        - response data structure

    Expected response structure:
    {
        "code": "...",
        "message": "...",
        "data": {"status": 400}
    }
    """

    # Base error contract validation
    assert_product_error_response(response)

    assert (
        response["data"]["status"] == 400
    ), f"Expected status 400, got {response['data']['status']}"

    assert response["code"] == "registration-error-email-exists", (
        f"Invalid Error code. Current: '{response['code']}', "
        f"Expected: 'registration-error-email-exists'"
    )

    assert "An account is already registered" in str(response["message"])


def assert_product_not_found_error(response):
    """
    Validate error returned when product does not exist.
    """

    VALID_ERROR_CODES = {
        "wc_user_invalid_id",
        "woocommerce_rest_invalid_id",
    }

    VALID_MESSAGES = {
        "Invalid user ID.",
        "Invalid resource ID.",
    }

    assert_product_error_response(response)

    assert (
        response["data"]["status"] == 404
    ), f"Expected status 404, got {response['data']['status']}"

    # assert response["code"] == "wc_user_invalid_id", (
    #     f"Invalid Error code. Current: '{response['code']}', "
    #     f"Expected: 'wc_user_invalid_id'"
    # )

    assert response["code"] in VALID_ERROR_CODES, (
        f"Invalid Error code. Current: '{response['code']}', "
        f"Expected one of: {sorted(VALID_ERROR_CODES)}"
    )

    # assert response["message"] == "Invalid user ID.", (
    #     f"Invalid Error message. Current: '{response['message']}', "
    #     f"Expected: 'Invalid user ID.'"
    # )

    assert response["message"] in VALID_MESSAGES, (
        f"Invalid Error message. Current: '{response['message']}', "
        f"Expected one of: {sorted(VALID_MESSAGES)}"
    )

    # or
    # assert isinstance(response["message"], str)
    # assert response["message"].strip(), "Error message must not be empty"


def assert_product_retrieved_successfully(response: HttpResponse) -> ProductModel:
    """
    Validate successful GET /products/{id} response.

    Steps:
        1. Validate HTTP status code
        2. Validate response structure using Pydantic

    Returns:
        ProductModel
    """

    assert (
        response.status_code == 200
    ), f"GET /products fetching failed. Expected 200, got {response.status_code}. Response: {response.text}"

    data = response.json

    # 🔒 Structure validation via Pydantic
    product_model = assert_valid_product_response(data)

    return product_model


def assert_product_exists_and_matches_api(
    products: List[Dict[str, Any]],
    email: str,
    db_product: Dict[str, Any],
) -> None:
    """
    Validate that the returned products matches the expected identity.

    Used when a single products object should be returned by the API.

    This validator performs two layers of validation:

    1️⃣ API VALIDATION
        - Ensures exactly one products exists in the dataset
        - Validates structure via Pydantic
        - Returns a typed ProductModel

    2️⃣ DATABASE VALIDATION
        - Confirms API data matches the database record

    This validator is commonly used in integration and end-to-end tests where both API and DB correctness
    must be verified.

    Args:
        products:
            Dataset returned by API (GET /products).

        email:
            Expected products email.

        db_product:
            Database record retrieved via DAO.

    Raises:
        AssertionError:
            If API data or DB data are inconsistent.
    """

    logger.debug("⚙️ Validating existence of products by email: %s", email)

    # -------------------------------------------------------
    # 1️⃣ DATASET VALIDATION
    # -------------------------------------------------------
    # Ensure exactly one products exists in API dataset and validate structure using Pydantic.
    product = assert_single_product_by_email(products, email)

    logger.info(
        "✅ Product found in API response (id=%s, email=%s)",
        product.id,
        product.email,
    )

    # -------------------------------------------------------
    # 2️⃣ DATABASE VALIDATION
    # -------------------------------------------------------
    # Compare API response with database record
    assert_product_matches_db(product, db_product)

    logger.info("✅ Product matches database record (ID=%s)", db_product["ID"])


# -------------------------------------------------------
# 🧠 BUSINESS VALIDATION
# -------------------------------------------------------
def assert_product_identity(
    product: ProductModel, expected_id: int, expected_email: str
) -> None:
    """
    Validate that the returned products matches the expected identity.

    This validator ensures that the API returned the correct resource.

    Typical use cases:
        - GET /products/{id}
        - GET /products?email=
        - responses where a SINGLE products object is expected

    Why this validator exists:
        - Removes duplicated validators across tests
        - Improves readability for junior engineers
        - Provides consistent error messages
        - Works with validated Pydantic models

    Args:
        product (ProductModel):
            Validated products object returned by API.

        expected_id (int):
            ID of the products that should have been returned.

        expected_email (str):
            Email of the products that should have been returned.

    Raises:
        AssertionError:
            If returned products does not match expected identity.
    """

    # -------------------------------------------------------
    # Validate products ID
    # -------------------------------------------------------
    assert (
        product.id == expected_id
    ), f"❌ Product ID mismatch: expected {expected_id}, got {product.id}"

    # -------------------------------------------------------
    # Validate products email
    # -------------------------------------------------------
    assert (
        product.email == expected_email
    ), f"❌ Product email mismatch: expected {expected_email}, got {product.email}"

    logger.info(
        "✅ Product identity verified (id=%s, email=%s)", product.id, product.email
    )


# -------------------------------------------------------
# 🚨 GENERIC ERROR VALIDATION
# -------------------------------------------------------
def assert_product_error_response(
    response: dict, expected_status: int | None = None
) -> None:
    """
    Validate the standard WooCommerce error response structure.

    This validator ensures the API returned a valid error payload.

    Expected structure:

    {
        "code": "...",
        "message": "...",
        "data": {
            "status": 400
        }
    }

    Args:
        response:
            Parsed JSON error response returned by the API.

        expected_status:
            Optional expected HTTP status code (e.g. 400, 404).

    Raises:
        AssertionError if the error structure is invalid.
    """

    # -------------------------------------------------------
    # Basic contract validation
    # -------------------------------------------------------
    assert isinstance(
        response, dict
    ), f"❌ Expected error response dict, got: {type(response)}"
    assert "code" in response, f"❌ Missing 'code' in response: {response}"
    assert "message" in response, f"❌ Missing 'message' in response: {response}"
    assert "data" in response, f"❌ Missing 'data' in response: {response}"

    # -------------------------------------------------------
    # Ensure values are not empty
    # -------------------------------------------------------
    assert response["code"], "❌ Error 'code' must not be empty"
    assert response["message"], "❌ Error 'message' must not be empty"

    # -------------------------------------------------------
    # Check HTTP status
    # -------------------------------------------------------
    assert (
        "status" in response["data"]
    ), f"❌ Missing 'status' in response['data']: {response}"

    logger.info(
        "✅ Valid error response received (code=%s status=%s)",
        response["code"],
        response["data"]["status"],
    )
