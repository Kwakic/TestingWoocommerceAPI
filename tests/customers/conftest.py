# import os
# import pytest
# from tests.customers.configs.config_customers import API_HOSTS

from typing import TYPE_CHECKING
import pytest

if TYPE_CHECKING:
    from EcommerceAPI.src.helpers.customers_helper import CustomersHelper
    from EcommerceAPI.src.dao.customers_dao import CustomersDAO


# @pytest.fixture(scope="session")
# def api_base_url() -> str:
#     """
#     Resolve and provide the base URL for the Customers API.
#
#     This session-scoped fixture determines which Customers API host to use
#     based on the current execution environment.
#
#     Resolution logic:
#     -----------------
#     - Reads the ENV environment variable (defaults to "test" if not set)
#     - Looks up the corresponding base URL in `API_HOSTS`
#     - Fails fast with a clear error if the environment is not defined
#
#     Why this fixture exists:
#     ------------------------
#     - Different microservices (customers, orders, products, etc.) use different base URLs
#     - Tests in folders like `preflight/` do not inherit customer-specific conftest files
#     - Defining this fixture locally ensures RequestUtility can always be constructed correctly
#
#     Expected ENV values:
#     --------------------
#     Values must match keys in `API_HOSTS`, for example:
#       - "test"
#       - "staging"
#       - "prod"
#
#     Raises:
#     -------
#     RuntimeError:
#         If ENV is set to a value that does not exist in API_HOSTS.
#
#     Returns:
#     --------
#     str
#         The resolved base URL for the Customers API.
#     """
#     env = os.getenv("ENV", "test").lower()
#
#     try:
#         return API_HOSTS[env]
#     except KeyError:
#         raise RuntimeError(
#             f"ENV='{env}' not found in customers API_HOSTS"
#         )


# ---------------------------------------------------------------------------
# 🧩 Customer Helper Fixture
# ---------------------------------------------------------------------------
"""
Customer test fixtures (facade layer).

This file provides **explicit, ergonomic fixtures** for customer-related tests.
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
    High-level API helper for customer operations.

    Provides:
    - create_customer(...)
    - call_get_customer_by_id(...)
    - call_list_all_customers_paginated(...)
    - schema & domain assertions

    Backed by:
    - session-scoped RequestUtility
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
    DAO for customer-related database assertions.

    Provides direct DB access for:
    - get_customer_by_id
    - get_customer_by_email
    - integrity checks

    Rules:
    - DAO is injected, never imported directly in tests
    - Helpers must NOT import DAOs internally
    """
    return all_resources.customers.dao
