# root/tests/coupons/conftest

from typing import TYPE_CHECKING
import pytest

if TYPE_CHECKING:
    from EcommerceAPI.src.coupons.helpers.coupons_helper import CouponsHelper
    from EcommerceAPI.src.coupons.dao.coupons_dao import CouponsDAO


# ---------------------------------------------------------------------------
# 🧩 Coupon Helper Fixture
# ---------------------------------------------------------------------------
"""
Coupon test fixtures (facade layer).

This file provides **explicit, ergonomic fixtures** for coupons-related tests.
Test authors should use THESE fixtures and should NOT care about:

- dynamic entity discovery
- EntitiesRegistry
- helper/DAO wiring
- cleanup internals

If you are writing tests under tests/coupons/, start here.
Advanced infrastructure logic lives in the shared framework layer.

Benefits:
    - Tests become trivial to read:
        coupon_helper = all_resources.coupons.helper → replaced by coupon_helper fixture
        dao = all_resources.coupons.dao → replaced by coupons_dao
    - IDEs see explicit fixtures, easing discovery and autocompletion when you
      add type hints (e.g., -> CouponsHelper).
"""


@pytest.fixture
def coupon_helper(all_resources) -> "CouponsHelper":
    """
    High-level API helper for coupons operations.

    Provides:
    - create_coupon(...)
    - get_coupon_by_id(...)
    - list_coupons_paginated(...)
    - update_coupon(...)
    - delete_coupon(...)
    - API + DB validation orchestration

    Backed by:
    - session-scoped APIClient
    - dynamic entity discovery
    - automatic cleanup integration

    Test authors should NEVER instantiate helpers directly.
    """
    return all_resources.coupons.helper


# ---------------------------------------------------------------------------
# 🧩 Coupon DAO Fixture
# ---------------------------------------------------------------------------
@pytest.fixture
def coupons_dao(all_resources) -> "CouponsDAO":
    """
    DAO for coupons-related database validators.

    Provides direct DB access for:
    - get_coupon_by_id(...)
    - get_coupon_by_code(...)
    - get_all_coupons(...)
    - get_coupon_meta(...)
    - get_coupon_metadata(...)
    - integrity checks

    Rules:
    - DAO is injected, never imported directly in tests
    - Helpers must NOT import DAOs internally
    """
    return all_resources.coupons.dao
