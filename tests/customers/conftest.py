# root/tests/customers/conftest

from typing import TYPE_CHECKING
import pytest

if TYPE_CHECKING:
    from EcommerceAPI.src.customers.helpers.customers_helper import CustomersHelper
    from EcommerceAPI.src.customers.dao.customers_dao import CustomersDAO


# ---------------------------------------------------------------------------
# 🧩 Customer Helper Fixture
# ---------------------------------------------------------------------------
"""
Customer test fixtures (facade layer).

This file provides **explicit, ergonomic fixtures** for customers-related tests.
Test authors should use THESE fixtures and should NOT care about:

- dynamic entity discovery
- EntitiesRegistry
- helper/DAO wiring
- cleanup internals

If you are writing tests under tests/customers/, start here.
Advanced infrastructure logic lives in the shared framework layer.

Benefits:
    - Tests become trivial to read:
        customer_helper = all_resources.customers.helper → replaced by customer_helper fixture
        dao = all_resources.customers.dao → replaced by customers_dao
    - IDEs see explicit fixtures, easing discovery and autocompletion when you add type hints (e.g., -> CustomersHelper).

"""


@pytest.fixture
def customer_helper(all_resources) -> "CustomersHelper":
    """
    High-level API helper for customers operations.

    Provides:
    - create_customer(...)
    - call_get_customer_by_id(...)
    - call_list_all_customers_paginated(...)
    - schema & domain validators

    Backed by:
    - session-scoped APIClient
    - dynamic entity discovery
    - automatic cleanup integration

    Test authors should NEVER instantiate helpers directly.
    """
    return all_resources.customers.helper


# ---------------------------------------------------------------------------
# 🧩 Customer DAO Fixture
# ---------------------------------------------------------------------------
@pytest.fixture
def customers_dao(all_resources) -> "CustomersDAO":
    """
    DAO for customers-related database validators.

    Provides direct DB access for:
    - get_customer_by_id
    - get_customer_by_email
    - integrity checks

    Rules:
    - DAO is injected, never imported directly in tests
    - Helpers must NOT import DAOs internally
    """
    return all_resources.customers.dao
