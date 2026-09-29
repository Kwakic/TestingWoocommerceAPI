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
    Create a Coupon using the minimum scenario-specific input.

    The test does not build or provision the Coupon directly. The
    `create_valid_coupon` fixture owns the valid-data pipeline:

        create_valid_coupon
            ↓
        CouponBuilder
            ↓
        CouponFactory
            ↓
        CouponProvisioner
            ↓
        CouponsHelper / CouponsApi
            ↓
        WooCommerce

    The fixture also owns:
        - POST /coupons
        - HTTP 201 validation
        - Coupon response validation
        - cleanup registration

    Test flow:
        1. Create a valid Coupon through the standard fixture.
        2. Retrieve the Coupon through the API.
        3. Retrieve the Coupon from the database.
        4. Verify that API and database data match.

    API/DB validation remains explicit in the test because it is the
    purpose of this integration scenario.
    """

    # ------------------------------------------------------------------
    # Step 1 — Arrange: create a valid Coupon through the standard fixture
    # ------------------------------------------------------------------
    # No scenario-specific fields are required here. CouponFactory supplies
    # the complete valid creation data through CouponBuilder.
    logger.info("🛠 Creating a test coupon.")

    # By default, CustomerFactory generates the customer data.
    # To override a value for this scenario, pass it directly to the fixture:
    #
    #     customer = create_valid_customer(email="john.smith.12345@test.com")
    #
    # The fixture passes the override to CustomerBuilder → CustomerFactory.
    # Only the specified value is overridden; all other fields are generated.
    coupon = create_valid_coupon()

    coupon_id = coupon["id"]

    logger.info(
        "🎟 Created coupon ID=%r, code=%r",
        coupon_id,
        coupon["code"],
    )

    # ------------------------------------------------------------------
    # Step 2 — Assert: verify API and database consistency
    # ------------------------------------------------------------------
    # The fixture has already validated the creation response. This test
    # performs the additional integration check between API and database.
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

    # ------------------------------------------------------------------
    # Step 3 — Final validation
    # ------------------------------------------------------------------
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
    Create multiple valid Coupons and verify each Coupon exists through
    the API and matches its database record.

    Each Coupon is created through the standard valid-data fixture:

        create_valid_coupon
            ↓
        CouponBuilder
            ↓
        CouponFactory
            ↓
        CouponProvisioner
            ↓
        CouponsHelper / CouponsApi
            ↓
        WooCommerce

    The fixture owns:
        - valid-data construction
        - POST /coupons
        - HTTP 201 validation
        - response validation
        - cleanup registration

    The test owns the API/DB integration validation.
    """

    # ------------------------------------------------------------------
    # Step 1 — Arrange: create the requested number of valid Coupons
    # ------------------------------------------------------------------
    # No valid Coupon data is generated in the test. Each creation goes
    # through the same factory-backed fixture and is registered for cleanup.
    created_coupons = [create_valid_coupon() for _ in range(qty)]

    # ------------------------------------------------------------------
    # Step 2 — Assert: verify each Coupon through API and database
    # ------------------------------------------------------------------
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
    Verify that supported WooCommerce discount types can be supplied as
    scenario-specific Coupon creation data.

    The test owns only the `discount_type` and `amount` scenario values.
    Valid defaults and provisioning remain the responsibility of the
    standard `create_valid_coupon` pipeline.
    """

    # Only the scenario-specific discount type and amount are supplied here.
    # CouponBuilder forwards these overrides to CouponFactory, which supplies
    # any remaining valid defaults.
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
    Verify that common Coupon restriction fields are accepted and persisted.

    The test supplies only the restriction scenario. CouponFactory provides
    all other valid defaults and the fixture owns provisioning, response
    validation, and cleanup.
    """

    # The test owns the restriction scenario only. All other valid Coupon
    # creation data is supplied by the standard factory-backed fixture.
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
    Negative test: creating a second Coupon with an existing Coupon code
    should be rejected by WooCommerce.

    This test intentionally combines two flows:

        1. Valid precondition:
           create_valid_coupon
               ↓
           CouponBuilder / CouponFactory
               ↓
           CouponProvisioner
               ↓
           WooCommerce

        2. Negative operation under test:
           coupon_api_raw
               ↓
           POST /coupons with duplicate code
               ↓
           WooCommerce
               ↓
           HTTP 400

    The first Coupon is created through the normal valid-data pipeline so it
    is owned and cleaned up by the fixture. The duplicate payload bypasses
    the valid-data pipeline because the invalid condition is the scenario
    being tested.
    """

    # Create the valid precondition through the standard test-data pipeline.
    # This Coupon is explicitly owned by the test and will be cleaned up by
    # the fixture after the test completes.
    existing_coupon = create_valid_coupon()
    code = existing_coupon["code"]

    # The duplicate-code payload is intentionally constructed here because
    # the invalid condition itself is the scenario under test. It must bypass
    # the valid-data Factory/Builder/Provisioner pipeline.
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

    # The exact WooCommerce error code/message can vary by WooCommerce
    # version, so this test focuses on the transport contract and standard
    # error shape.
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
    Verify that valid Coupon amounts can be supplied as scenario-specific
    creation data and are persisted correctly.

    CouponFactory remains responsible for all unspecified valid defaults.
    """

    # `amount` is the scenario-specific value under test. The fixture supplies
    # the remaining valid Coupon creation data.
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
    Verify that Coupon usage-limit fields are accepted and persisted.

    The test supplies only the usage-limit scenario; the standard fixture
    remains responsible for valid-data construction and provisioning.
    """

    # These usage-limit fields define the scenario; valid defaults are still
    # provided by CouponFactory through the standard fixture pipeline.
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
    Verify that a Coupon accepts a valid future expiration date.

    The expiration value is the only scenario-specific creation data supplied
    by this test; the standard fixture handles the remaining valid defaults,
    provisioning, validation, and cleanup.
    """

    # The expiration date is the only scenario-specific value supplied here.
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
    Verify that a Coupon accepts email restrictions and returns them through
    the API.

    The email list is scenario-specific data. The standard fixture remains
    responsible for the valid creation pipeline and cleanup.
    """

    emails = [
        "customer1@example.com",
        "customer2@example.com",
    ]

    # Email restrictions are scenario-specific data; valid Coupon defaults
    # continue to come from CouponFactory through the fixture.
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
