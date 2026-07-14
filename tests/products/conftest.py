# root/tests/products/conftest

from typing import TYPE_CHECKING
import pytest

if TYPE_CHECKING:
    from EcommerceAPI.src.products.helpers.products_helper import ProductsHelper
    from EcommerceAPI.src.products.dao.products_dao import ProductsDAO


# ---------------------------------------------------------------------------
# 🧩 Products Helper Fixture
# ---------------------------------------------------------------------------
"""
Product test fixtures (facade layer).

This file provides **explicit, ergonomic fixtures** for products-related tests.
Test authors should use THESE fixtures and should NOT care about:

- dynamic entity discovery
- EntitiesRegistry
- helper/DAO wiring
- cleanup internals

If you are writing tests under tests/products/, start here.
Advanced infrastructure logic lives in the shared framework layer.

Benefits:
    - Tests become trivial to read:
        product_helper = all_resources.products.helper → replaced by product_helper fixture
        dao = all_resources.products.dao → replaced by products_dao
    - IDEs see explicit fixtures, easing discovery and autocompletion when you add type hints (e.g., -> ProductsHelper).

"""


@pytest.fixture
def product_helper(all_resources) -> "ProductsHelper":
    """
    High-level API helper for products operations.

    Provides:
    - create_product(...)
    - call_get_product_by_id(...)
    - call_list_all_products_paginated(...)
    - schema & domain validators

    Backed by:
    - session-scoped APIClient
    - dynamic entity discovery
    - automatic cleanup integration

    Test authors should NEVER instantiate helpers directly.
    """
    return all_resources.products.helper


# ---------------------------------------------------------------------------
# 🧩 Product DAO Fixture
# ---------------------------------------------------------------------------
@pytest.fixture
def products_dao(all_resources) -> "ProductsDAO":
    """
    DAO for products-related database validators.

    Provides direct DB access for:
    - get_product_by_id
    - get_product_by_email
    - integrity checks

    Rules:
    - DAO is injected, never imported directly in tests
    - Helpers must NOT import DAOs internally
    """
    return all_resources.products.dao
