"""
Smoke test for creating a WooCommerce coupon.

This test verifies the complete coupon creation flow through the
domain fixture and confirms that the created coupon is persisted
correctly in the database.
"""

import logging

import pytest


from EcommerceAPI.src.coupons.validators.coupon_validators import (
    assert_coupon_exists_and_matches_api,
)


logger = logging.getLogger(__name__)  # Logging level is configured in pytest.ini

pytestmark = [pytest.mark.coupons, pytest.mark.integration]


# ---------------------------------------
# 🧪 Test: Minimal Coupon Creation
# ---------------------------------------
@pytest.mark.sanity
@pytest.mark.smoke
@pytest.mark.contract
def test_create_single_coupon(
    coupon_helper,
    coupons_dao,
    create_valid_coupon,
):
    """
    Create a coupon using the minimum valid payload.

    The `create_valid_coupon` fixture already performs:

        - POST /coupons
        - HTTP status code validation (201)
        - CouponModel/Pydantic response validation
        - Cleanup registration

    Test flow:

        1. Create a valid coupon
        2. Verify the created coupon is persisted correctly
           and matches the database record
        3. Log completion of the full validation flow

    API/DB validation is intentionally explicit in the test:
    the helper fetches API data, the DAO fetches database data, and the
    validator compares the already-fetched data.
    """

    # -------------------------------------------
    # Step 1 — Create coupon
    # -------------------------------------------
    logger.info("🛠 Creating a test coupon via factory fixture.")

    coupon = create_valid_coupon()

    coupon_id = coupon["id"]

    logger.info(
        "🎟 Created coupon ID=%r, code=%r",
        coupon_id,
        coupon["code"],
    )

    # -------------------------------------------
    # Step 2 — Verify API response matches DB
    # -------------------------------------------
    logger.info(
        "🔍 Verifying coupon ID=%r against the database.",
        coupon_id,
    )

    api_coupon = coupon_helper.get_coupon_by_id(coupon_id=coupon_id)
    api_coupons = [api_coupon] if api_coupon else []

    db_coupon = coupons_dao.get_coupon_by_id(coupon_id)
    db_coupon_meta = coupons_dao.get_coupon_metadata(coupon_id)

    assert_coupon_exists_and_matches_api(
        api_coupons,
        coupon_id,
        db_coupon,
        db_coupon_meta,
    )

    # -------------------------------------------
    # Step 3 — Final validation
    # -------------------------------------------
    logger.info(
        "🎯 Full coupon creation validation complete for ID=%r.",
        coupon_id,
    )


# ---------------------------------------
# 🚀 Test: Bulk Create Coupons
# ---------------------------------------
@pytest.mark.bulk
@pytest.mark.contract
@pytest.mark.regression
@pytest.mark.parametrize("qty", [1, 3, 5])
def test_bulk_create_coupons(
    qty,
    coupon_helper,
    coupons_dao,
    create_valid_coupon,
):
    """
    Create multiple coupons and verify each coupon exists in the API
    and matches its database record.

    The fixture owns:
        - POST /coupons
        - HTTP 201 validation
        - Pydantic response validation
        - cleanup registration

    The test owns the API/DB integration validation.
    """

    created_coupons = []

    for _ in range(qty):
        coupon = create_valid_coupon()
        created_coupons.append(coupon)

    for coupon in created_coupons:
        coupon_id = coupon["id"]

        api_coupon = coupon_helper.get_coupon_by_id(coupon_id=coupon_id)
        api_coupons = [api_coupon] if api_coupon else []

        db_coupon = coupons_dao.get_coupon_by_id(coupon_id)
        db_coupon_meta = coupons_dao.get_coupon_metadata(coupon_id)

        assert_coupon_exists_and_matches_api(
            api_coupons,
            coupon_id,
            db_coupon,
            db_coupon_meta,
        )


# ---------------------------------------
# 🧪 Test: Create Coupons With Valid
#          Discount Types
# ---------------------------------------
@pytest.mark.contract
@pytest.mark.regression
@pytest.mark.parametrize(
    "discount_type",
    [
        pytest.param("percent", id="percent"),
        pytest.param("fixed_cart", id="fixed-cart"),
        pytest.param("fixed_product", id="fixed-product"),
    ],
)
def test_create_coupon_with_valid_discount_type(
    discount_type,
    coupon_helper,
    coupons_dao,
    create_valid_coupon,
):
    """
    Verify that the coupon creation flow accepts the supported WooCommerce
    discount types.
    """

    coupon = create_valid_coupon(
        discount_type=discount_type,
        amount="10",
    )

    coupon_id = coupon["id"]

    api_coupon = coupon_helper.get_coupon_by_id(coupon_id=coupon_id)
    api_coupons = [api_coupon] if api_coupon else []

    db_coupon = coupons_dao.get_coupon_by_id(coupon_id)
    db_coupon_meta = coupons_dao.get_coupon_metadata(coupon_id)

    assert_coupon_exists_and_matches_api(
        api_coupons,
        coupon_id,
        db_coupon,
        db_coupon_meta,
    )


# ---------------------------------------
# 🧪 Test: Create Coupon With Restrictions
# ---------------------------------------
@pytest.mark.contract
@pytest.mark.regression
def test_create_coupon_with_valid_restrictions(
    coupon_helper,
    coupons_dao,
    create_valid_coupon,
):
    """
    Verify that common coupon restriction fields are accepted and persisted.
    """

    coupon = create_valid_coupon(
        discount_type="percent",
        amount="15",
        individual_use=True,
        free_shipping=True,
        exclude_sale_items=True,
        minimum_amount="20",
        maximum_amount="100",
    )

    coupon_id = coupon["id"]

    api_coupon = coupon_helper.get_coupon_by_id(coupon_id=coupon_id)
    api_coupons = [api_coupon] if api_coupon else []

    db_coupon = coupons_dao.get_coupon_by_id(coupon_id)
    db_coupon_meta = coupons_dao.get_coupon_metadata(coupon_id)

    assert_coupon_exists_and_matches_api(
        api_coupons,
        coupon_id,
        db_coupon,
        db_coupon_meta,
    )


# ---------------------------------------
# ⚠️ Test: Duplicate Coupon Code
# ---------------------------------------


@pytest.mark.negative
@pytest.mark.contract
@pytest.mark.regression
def test_create_coupon_fails_for_existing_code(
    create_valid_coupon,
    coupon_api_raw,
):
    """
    Negative test: creating a second coupon with an existing coupon code
    should be rejected by WooCommerce.
    """

    existing_coupon = create_valid_coupon()
    code = existing_coupon["code"]

    payload = {
        "code": code,
        "discount_type": "percent",
        "amount": "10",
    }

    http_response = coupon_api_raw.post(
        endpoint="coupons",
        payload=payload,
    )

    assert http_response.status_code == 400, (
        f"Expected 400, got {http_response.status_code}. "
        f"Response: {http_response.text[:300]}"
    )

    response = http_response.json

    # The exact WooCommerce error code/message can vary by WooCommerce version,
    # so this test focuses on the transport contract and standard error shape.
    assert isinstance(
        response, dict
    ), f"Expected JSON error object, got: {type(response)}"
    assert "code" in response, f"Missing 'code' in response: {response}"
    assert "message" in response, f"Missing 'message' in response: {response}"
    assert "data" in response, f"Missing 'data' in response: {response}"
    assert (
        response["data"]["status"] == 400
    ), f"Expected error payload status 400, got {response['data'].get('status')}"


# ---------------------------------------
# 🧪 Test: Create Coupons With Valid Amounts
# ---------------------------------------
@pytest.mark.contract
@pytest.mark.regression
@pytest.mark.parametrize(
    "amount",
    [
        pytest.param("0.01", id="minimum-decimal"),
        pytest.param("1", id="integer"),
        pytest.param("10.50", id="decimal"),
        pytest.param("100", id="large-integer"),
    ],
)
def test_create_coupon_with_valid_amount(
    amount,
    coupon_helper,
    coupons_dao,
    create_valid_coupon,
):
    """
    Verify that valid coupon amounts are accepted and persisted correctly.
    """

    coupon = create_valid_coupon(
        discount_type="percent",
        amount=amount,
    )

    coupon_id = coupon["id"]

    api_coupon = coupon_helper.get_coupon_by_id(coupon_id=coupon_id)
    api_coupons = [api_coupon] if api_coupon else []

    db_coupon = coupons_dao.get_coupon_by_id(coupon_id)
    db_coupon_meta = coupons_dao.get_coupon_metadata(coupon_id)

    assert_coupon_exists_and_matches_api(
        api_coupons,
        coupon_id,
        db_coupon,
        db_coupon_meta,
    )


# ---------------------------------------
# 🧪 Test: Create Coupon With Usage Limits
# ---------------------------------------
@pytest.mark.contract
@pytest.mark.regression
def test_create_coupon_with_usage_limits(
    coupon_helper,
    coupons_dao,
    create_valid_coupon,
):
    """
    Verify that coupon usage-limit fields are accepted and persisted.
    """

    coupon = create_valid_coupon(
        usage_limit=10,
        usage_limit_per_user=2,
        limit_usage_to_x_items=3,
    )

    coupon_id = coupon["id"]

    api_coupon = coupon_helper.get_coupon_by_id(coupon_id=coupon_id)
    api_coupons = [api_coupon] if api_coupon else []

    db_coupon = coupons_dao.get_coupon_by_id(coupon_id)
    db_coupon_meta = coupons_dao.get_coupon_metadata(coupon_id)

    assert_coupon_exists_and_matches_api(
        api_coupons,
        coupon_id,
        db_coupon,
        db_coupon_meta,
    )


# ---------------------------------------
# 🧪 Test: Create Coupon With Expiration Date
# ---------------------------------------
@pytest.mark.contract
@pytest.mark.regression
def test_create_coupon_with_expiration_date(
    coupon_helper,
    create_valid_coupon,
):
    """
    Verify that a coupon accepts a valid future expiration date.
    """

    coupon = create_valid_coupon(
        date_expires="2030-12-31T23:59:59",
    )

    coupon_id = coupon["id"]

    api_coupon = coupon_helper.get_coupon_by_id(coupon_id=coupon_id)

    assert (
        api_coupon is not None
    ), f"Expected coupon ID={coupon_id} to be retrievable from the API."
    assert api_coupon[
        "date_expires"
    ], f"Expected coupon ID={coupon_id} to have an expiration date."


# ---------------------------------------
# 🧪 Test: Create Coupon With Email Restrictions
# ---------------------------------------
@pytest.mark.contract
@pytest.mark.regression
def test_create_coupon_with_email_restrictions(
    coupon_helper,
    create_valid_coupon,
):
    """
    Verify that a coupon accepts email restrictions and returns them via the API.
    """

    emails = [
        "customer1@example.com",
        "customer2@example.com",
    ]

    coupon = create_valid_coupon(
        email_restrictions=emails,
    )

    coupon_id = coupon["id"]

    api_coupon = coupon_helper.get_coupon_by_id(coupon_id=coupon_id)

    assert (
        api_coupon is not None
    ), f"Expected coupon ID={coupon_id} to be retrievable from the API."
    assert api_coupon["email_restrictions"] == emails, (
        f"Expected email restrictions {emails}, "
        f"got {api_coupon.get('email_restrictions')}"
    )
