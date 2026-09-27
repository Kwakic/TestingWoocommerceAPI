"""GET /coupons integration test coverage.

This module verifies Coupon retrieval behavior through the public Coupon
domain fixture and keeps test-data setup separate from the GET operation
under test.

Coverage:
    - GET coupon by ID happy path
    - GET coupon by ID with API/DB consistency
    - GET non-existent coupon
    - GET coupon with populated fields

Test-data responsibility:
    - ``create_valid_coupon`` creates a valid Coupon through the standard
      Coupon Builder / Factory / Provisioner pipeline.
    - The fixture validates the creation response and registers the Coupon
      for automatic cleanup.
    - The GET tests themselves remain responsible for validating the GET
      operation and its response.

Negative tests may intentionally use direct scenario values when the invalid
or non-existent input itself is the behavior under test.
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

    Fixture responsibilities (``create_valid_coupon``):
        - create valid Coupon test data through the Builder / Factory path
        - POST /coupons through the Provisioner / Helper path
        - validate the creation response
        - register the Coupon for automatic cleanup

    Test flow:
        1. Create a valid Coupon
        2. Retrieve the Coupon by ID
        3. Validate the GET HTTP status
        4. Validate the Coupon response structure
        5. Verify the returned Coupon identity
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

    # Request HttpResponse so the test can validate the HTTP status returned
    # by the GET operation under test.
    response = coupon_helper.get_coupon_by_id(
        coupon_id=coupon_id,
        return_http_response=True,
    )

    # -------------------------------------------
    # Step 3 — Transport validation (FAIL FAST)
    # -------------------------------------------
    # The test owns the HTTP status assertion because GET /coupons/{id}
    # is the operation being tested.
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. " f"Response: {response.text}"
    )

    # -------------------------------------------
    # Step 4 — Response body validation
    # -------------------------------------------
    # Validators validate response data; they do not own HTTP transport
    # assertions.
    coupon_model = assert_coupon_retrieved_successfully(response)

    # -------------------------------------------
    # Step 5 — Business validation
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
    Verify that a Coupon retrieved through the API matches its database state.

    Endpoint tested:
        GET /coupons/{id}

    Test-data responsibility:
        ``create_valid_coupon`` provisions the Coupon using the standard
        Coupon Builder / Factory / Provisioner pipeline.

    Test flow:
        1. Create a Coupon with scenario-specific fields
        2. Retrieve the Coupon through the API
        3. Validate the GET HTTP status and response structure
        4. Retrieve the same Coupon from the database
        5. Verify API data matches the database state
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

    # The fixture handles Coupon test-data generation, provisioning,
    # creation-response validation, and ownership registration.
    coupon_id = coupon["id"]

    # The GET is the operation under test, so the test owns its HTTP status.
    response = coupon_helper.get_coupon_by_id(
        coupon_id=coupon_id,
        return_http_response=True,
    )

    # -------------------------------------------
    # 🚦 Transport validation (FAIL FAST)
    # -------------------------------------------
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. " f"Response: {response.text}"
    )

    # -------------------------------------------
    # 📦 Response body validation
    # -------------------------------------------
    coupon_model = assert_coupon_retrieved_successfully(response)

    # -------------------------------------------
    # 🗄 Retrieve Coupon from database
    # -------------------------------------------
    db_coupon = coupons_dao.get_coupon_by_id(coupon_id)
    db_coupon_meta = coupons_dao.get_coupon_metadata(coupon_id)

    assert_coupon_matches_db(
        coupon_model,
        db_coupon,
        db_coupon_meta,
    )

    logger.info(
        "🎯 API/DB consistency validation complete for Coupon ID: %r",
        coupon_id,
    )


# ---------------------------------------
# ⚠️ Test: GET Non-Existent Coupon
# ---------------------------------------
@pytest.mark.negative
@pytest.mark.contract
@pytest.mark.regression
def test_get_nonexistent_coupon(coupon_helper):
    """
    Negative test for retrieving a non-existent Coupon.

    Endpoint tested:
        GET /coupons/{id}

    Test flow:
        1. Request a non-existent Coupon ID
        2. Validate the API returns HTTP 404
        3. Validate the Coupon not-found error response
    """

    non_existent_coupon_id = 999999999

    # No test-data provisioning is required here because the non-existent ID
    # is itself the scenario under test.
    response = coupon_helper.get_coupon_by_id(
        coupon_id=non_existent_coupon_id,
        return_http_response=True,
    )

    # -------------------------------------------
    # 🚦 Transport validation (FAIL FAST)
    # -------------------------------------------
    # The test owns the HTTP status assertion because the GET operation
    # is the behavior being verified.
    assert response.status_code == 404, (
        f"Expected 404, got {response.status_code}. " f"Response: {response.text}"
    )

    # -------------------------------------------
    # 📦 Error response validation
    # -------------------------------------------
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
    Verify that GET by ID returns the populated Coupon fields supplied
    during test-data setup.

    Endpoint tested:
        GET /coupons/{id}

    Test-data responsibility:
        ``create_valid_coupon`` provisions the Coupon using the standard
        Coupon Builder / Factory / Provisioner pipeline.

    Test flow:
        1. Create a Coupon with explicitly populated fields
        2. Retrieve the Coupon by ID
        3. Validate the GET response
        4. Verify the populated fields were persisted and returned

    The test supplies only the fields relevant to this GET scenario.
    The Factory provides valid defaults for unspecified fields.
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

    # The fixture owns the creation pipeline, validation, and cleanup.
    # The test supplies only the fields relevant to this GET scenario.
    coupon_id = coupon["id"]

    response = coupon_helper.get_coupon_by_id(
        coupon_id=coupon_id,
        return_http_response=True,
    )

    # -------------------------------------------
    # 🚦 Transport validation (FAIL FAST)
    # -------------------------------------------
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. " f"Response: {response.text}"
    )

    # -------------------------------------------
    # 📦 Response body validation
    # -------------------------------------------
    coupon_model = assert_coupon_retrieved_successfully(response)

    # -------------------------------------------
    # 🔍 Business validation
    # -------------------------------------------
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
