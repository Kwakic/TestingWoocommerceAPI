"""
Smoke test for retrieving a WooCommerce coupon by ID.

This test verifies that a previously created coupon can be
retrieved successfully using its WooCommerce coupon ID.
"""

import logging

import pytest

from EcommerceAPI.src.coupons.validators.coupon_validators import (
    assert_coupon_identity,
    assert_coupon_retrieved_successfully,
    assert_coupon_error_response,
)
from EcommerceAPI.src.coupons.validators.coupon_db_validators import (
    assert_coupon_matches_db,
)


logger = logging.getLogger(__name__)  # Logging level is configured in pytest.ini

pytestmark = [pytest.mark.coupons, pytest.mark.integration]


# ---------------------------------------
# 🧪 Test: Get Coupon by ID
# ---------------------------------------
@pytest.mark.sanity
@pytest.mark.smoke
@pytest.mark.contract
def test_get_coupon_by_id(
    coupon_helper,
    create_valid_coupon,
):
    """
    Verify that a coupon can be retrieved by ID.

    Endpoint tested:
        GET /coupons/{id}

    Fixture responsibilities:
        - POST /coupons
        - response validation (Pydantic)
        - cleanup registration

    Test flow:

        1. Create a valid coupon
        2. Retrieve the coupon by ID
        3. Validate response status and structure
        4. Verify returned coupon identity
    """

    # -------------------------------------------
    # Step 1 — Create a valid coupon
    # -------------------------------------------
    logger.info("🛠 Creating a test coupon.")

    coupon = create_valid_coupon()

    coupon_id = coupon["id"]
    coupon_code = coupon["code"]

    logger.info(
        "🎟 Created coupon ID=%r, code=%r",
        coupon_id,
        coupon_code,
    )

    # -------------------------------------------
    # Step 2 — Retrieve coupon by ID
    # -------------------------------------------
    logger.info(
        "🔎 Fetching coupon by ID: %r",
        coupon_id,
    )

    # Request the HttpResponse wrapper so the validator
    # can validate the HTTP status code.
    response = coupon_helper.get_coupon_by_id(
        coupon_id,
        return_http_response=True,
    )

    # -------------------------------------------
    # Step 3 — Validate response
    # -------------------------------------------
    # Validates:
    #   - HTTP 200
    #   - response structure
    #   - CouponModel/Pydantic schema
    coupon_model = assert_coupon_retrieved_successfully(response)

    # -------------------------------------------
    # Step 4 — Verify coupon identity
    # -------------------------------------------
    # Ensure the coupon returned by GET is the
    # same coupon that was created in Step 1.
    assert_coupon_identity(
        coupon_model,
        coupon_id,
        coupon_code,
    )

    logger.info(
        "✅ Retrieved coupon matches created coupon: ID=%s, code=%s",
        coupon_id,
        coupon_code,
    )

    logger.info(
        "🎯 Coupon GET-by-ID validation complete for ID=%r.",
        coupon_id,
    )


# ---------------------------------------
# 🧪 Test: GET Coupon By ID — API/DB Consistency
# ---------------------------------------
@pytest.mark.integration
@pytest.mark.contract
def test_get_coupon_by_id_matches_db(
    coupon_helper,
    coupons_dao,
    create_valid_coupon,
):
    """
    Verify that a coupon retrieved through the API matches its database state.
    """

    coupon = create_valid_coupon(
        discount_type="percent",
        amount="15",
        usage_limit=10,
        usage_limit_per_user=2,
        limit_usage_to_x_items=3,
        free_shipping=True,
        minimum_amount="20",
        maximum_amount="100",
    )

    coupon_id = coupon["id"]
    response = coupon_helper.get_coupon_by_id(
        coupon_id=coupon_id,
        return_http_response=True,
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. " f"Response: {response.text}"
    )

    coupon_model = assert_coupon_retrieved_successfully(response)

    db_coupon = coupons_dao.get_coupon_by_id(coupon_id)
    db_coupon_meta = coupons_dao.get_coupon_metadata(coupon_id)

    assert_coupon_matches_db(
        coupon_model,
        db_coupon,
        db_coupon_meta,
    )


# ---------------------------------------
# 🧪 Test: GET Non-Existent Coupon
# ---------------------------------------
@pytest.mark.integration
@pytest.mark.contract
def test_get_nonexistent_coupon(coupon_helper):
    """
    Verify that requesting a coupon ID that does not exist returns 404
    with a valid WooCommerce error response.
    """

    non_existent_coupon_id = 999999999

    response = coupon_helper.get_coupon_by_id(
        coupon_id=non_existent_coupon_id,
        return_http_response=True,
    )

    assert response.status_code == 404, (
        f"Expected 404, got {response.status_code}. " f"Response: {response.text}"
    )

    assert_coupon_error_response(response.json, expected_status=404)


# ---------------------------------------
# 🧪 Test: GET Coupon With Populated Fields
# ---------------------------------------
@pytest.mark.integration
@pytest.mark.contract
def test_get_coupon_with_populated_fields(
    coupon_helper,
    create_valid_coupon,
):
    """
    Verify that GET by ID returns the populated coupon fields supplied at creation.
    """

    coupon = create_valid_coupon(
        discount_type="percent",
        amount="25.50",
        individual_use=True,
        free_shipping=True,
        exclude_sale_items=True,
        usage_limit=10,
        usage_limit_per_user=2,
        limit_usage_to_x_items=3,
        minimum_amount="20",
        maximum_amount="100",
        email_restrictions=[
            "customer1@example.com",
            "customer2@example.com",
        ],
        date_expires="2030-12-31T23:59:59",
    )

    coupon_id = coupon["id"]

    response = coupon_helper.get_coupon_by_id(
        coupon_id=coupon_id,
        return_http_response=True,
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. " f"Response: {response.text}"
    )

    coupon_model = assert_coupon_retrieved_successfully(response)

    assert coupon_model.id == coupon_id
    assert coupon_model.code == coupon["code"]
    assert coupon_model.discount_type == "percent"
    assert coupon_model.amount == "25.50"
    assert coupon_model.individual_use is True
    assert coupon_model.free_shipping is True
    assert coupon_model.exclude_sale_items is True
    assert coupon_model.usage_limit == 10
    assert coupon_model.usage_limit_per_user == 2
    assert coupon_model.limit_usage_to_x_items == 3
    assert coupon_model.minimum_amount == "20.00"
    assert coupon_model.maximum_amount == "100.00"
    assert coupon_model.email_restrictions == [
        "customer1@example.com",
        "customer2@example.com",
    ]
    assert coupon_model.date_expires == "2030-12-31T23:59:59"
