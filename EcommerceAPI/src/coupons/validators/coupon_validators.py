# EcommerceAPI/src/coupons/validators/coupon_validators.py

from __future__ import annotations

import logging
from typing import Any, Dict, List

from EcommerceAPI.src.core.http_response import HttpResponse
from EcommerceAPI.src.coupons.models.coupon_model import CouponModel
from EcommerceAPI.src.coupons.validators.coupon_db_validators import (
    assert_coupon_matches_db,
)


logger = logging.getLogger(__name__)


# ================================================================
# STRUCTURE VALIDATION
# ================================================================


def assert_valid_coupon_response(
    coupon: Dict[str, Any],
) -> CouponModel:
    """
    Validate the structure of a coupon API response.

    Pydantic is responsible for:
        - required fields
        - field types
        - nested metadata structure
        - optional fields

    Returns:
        CouponModel:
            Validated coupon model.

    Raises:
        pydantic.ValidationError:
            If the response structure is invalid.
    """

    coupon_model = CouponModel(**coupon)

    logger.info(
        "✅ Coupon structure valid: id=%s code=%s",
        coupon_model.id,
        coupon_model.code,
    )

    return coupon_model


# ================================================================
# DATASET VALIDATION
# ================================================================


def assert_single_coupon_by_id(
    coupons: List[Dict[str, Any]],
    coupon_id: int,
) -> CouponModel:
    """
    Validate that exactly one coupon exists for the given ID
    in a dataset response.

    Typical use case:
        GET /coupons

    Returns:
        CouponModel:
            The validated coupon.

    Raises:
        AssertionError:
            If zero or multiple matching coupons are found.
    """

    matches = [coupon for coupon in coupons if coupon.get("id") == coupon_id]

    assert len(matches) == 1, (
        f"Expected exactly one coupon with ID={coupon_id}, " f"found {len(matches)}"
    )

    coupon_model = assert_valid_coupon_response(matches[0])

    logger.info(
        "✅ Coupon found in dataset: id=%s code=%s",
        coupon_model.id,
        coupon_model.code,
    )

    return coupon_model


# ================================================================
# SUCCESSFUL RETRIEVAL
# ================================================================


def assert_coupon_retrieved_successfully(
    response: HttpResponse,
) -> CouponModel:
    """
    Validate successful GET /coupons/{id} response.

    Validation steps:
        1. HTTP status must be 200
        2. Response structure is validated by CouponModel

    Returns:
        CouponModel
    """

    assert response.status_code == 200, (
        f"GET /coupons failed. "
        f"Expected 200, got {response.status_code}. "
        f"Response: {response.text}"
    )

    data = response.json

    return assert_valid_coupon_response(data)


# ================================================================
# API + DATABASE VALIDATION
# ================================================================


def assert_coupon_exists_and_matches_api(
    coupons: List[Dict[str, Any]],
    coupon_id: int,
    db_coupon: Dict[str, Any],
    db_coupon_meta: Dict[str, Dict[str, Any]],
) -> None:
    """
    Validate that a coupon exists in the API response and
    matches the corresponding database record.

    Validation layers:

        1. API dataset validation
        2. Pydantic structure validation
        3. Database consistency validation
    """

    logger.debug(
        "⚙️ Validating coupon by ID=%s",
        coupon_id,
    )

    coupon = assert_single_coupon_by_id(
        coupons,
        coupon_id,
    )

    assert_coupon_matches_db(
        coupon,
        db_coupon,
        db_coupon_meta,
    )

    logger.info(
        "✅ Coupon matches database record (ID=%s)",
        coupon_id,
    )


# ================================================================
# BUSINESS / IDENTITY VALIDATION
# ================================================================


def assert_coupon_identity(
    coupon: CouponModel,
    expected_id: int,
    expected_code: str,
) -> None:
    """
    Validate that the returned coupon is the expected coupon.

    This is intentionally separate from Pydantic structure validation.

    Pydantic answers:
        "Is this a valid coupon object?"

    This validator answers:
        "Is this the coupon we expected?"
    """

    assert coupon.id == expected_id, (
        f"Coupon ID mismatch. " f"Expected {expected_id}, got {coupon.id}"
    )

    assert coupon.code == expected_code, (
        f"Coupon code mismatch. " f"Expected '{expected_code}', got '{coupon.code}'"
    )

    logger.info(
        "✅ Coupon identity verified: id=%s code=%s",
        coupon.id,
        coupon.code,
    )


# ================================================================
# GENERIC ERROR VALIDATION
# ================================================================


def assert_coupon_error_response(
    response: Dict[str, Any],
    expected_status: int | None = None,
) -> None:
    """
    Validate the standard WooCommerce error response structure.

    Expected shape:

        {
            "code": "...",
            "message": "...",
            "data": {
                "status": 400
            }
        }

    Args:
        response:
            Parsed JSON error response.

        expected_status:
            Optional expected HTTP status.
    """

    assert isinstance(response, dict), (
        f"Expected error response dict, " f"got {type(response)}"
    )

    assert "code" in response, f"Missing 'code' in error response: {response}"

    assert "message" in response, f"Missing 'message' in error response: {response}"

    assert "data" in response, f"Missing 'data' in error response: {response}"

    assert response["code"], "Error 'code' must not be empty"

    assert response["message"], "Error 'message' must not be empty"

    assert isinstance(response["data"], dict), (
        f"Expected 'data' to be dict, " f"got {type(response['data'])}"
    )

    assert (
        "status" in response["data"]
    ), f"Missing 'status' in response['data']: {response}"

    if expected_status is not None:
        assert response["data"]["status"] == expected_status, (
            f"Expected error status {expected_status}, "
            f"got {response['data']['status']}"
        )

    logger.info(
        "✅ Valid coupon error response: code=%s status=%s",
        response["code"],
        response["data"]["status"],
    )


# ================================================================
# CREATE FAILURE
# ================================================================


def assert_coupon_creation_failed(
    response: Dict[str, Any],
) -> None:
    """
    Validate a failed coupon creation response.

    This validator intentionally does not hard-code a particular
    WooCommerce error code or message.

    Specific scenarios should validate their expected error
    code/message separately when required.
    """

    assert_coupon_error_response(
        response,
        expected_status=400,
    )

    logger.info(
        "✅ Coupon creation failure validated: code=%s",
        response["code"],
    )
