"""
Smoke test for creating a WooCommerce coupon.

This test verifies the complete coupon creation flow through the
domain fixture and confirms that the created coupon is persisted
correctly in the database.
"""

import logging

import pytest


logger = logging.getLogger(__name__)  # Logging level is configured in pytest.ini

pytestmark = [pytest.mark.coupons, pytest.mark.integration]


# ---------------------------------------
# 🧪 Test: Minimal Coupon Creation
# ---------------------------------------
@pytest.mark.tcid("TCID-XXX")
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

    The test intentionally keeps assertions and workflow orchestration
    in the appropriate framework layers rather than duplicating them here.
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

    coupon_helper.assert_coupon_exists_and_matches_db(
        coupon_id=coupon_id,
        dao=coupons_dao,
    )

    # -------------------------------------------
    # Step 3 — Final validation
    # -------------------------------------------
    logger.info(
        "🎯 Full coupon creation validation complete for ID=%r.",
        coupon_id,
    )
