# Order test fixtures (facade layer).

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from src.entities.orders import OrdersDAO
    from src.entities.orders.helpers.orders_helper import OrdersHelper

# ---------------------------------------------------------------------------
# 🧩 Orders Helper Fixture
# ---------------------------------------------------------------------------
"""
Order test fixtures (facade layer).

This file provides **explicit, ergonomic fixtures** for orders-related tests.
Test authors should use THESE fixtures and should NOT care about:

- dynamic entity discovery
- EntitiesRegistry
- helper/DAO wiring
- cleanup internals

If you are writing tests under tests/orders/, start here.
Advanced infrastructure logic lives in the shared framework layer.

Benefits:
    - Tests become trivial to read:
        order_helper = all_resources.orders.helper → replaced by orders_helper fixture
        dao = all_resources.orders.dao → replaced by orders_dao
    - IDEs see explicit fixtures, easing discovery and autocompletion when you add type hints (e.g., -> OrdersHelper).

"""


@pytest.fixture
def order_helper(all_resources) -> "OrdersHelper":
    """Provide the OrdersHelper for Order API operations.

    The helper is discovered and configured by the shared framework fixture.
    """
    return all_resources.orders.helper


# ---------------------------------------------------------------------------
# Order DAO Fixture
# ---------------------------------------------------------------------------
@pytest.fixture
def orders_dao(all_resources) -> "OrdersDAO":
    """Provide the OrdersDAO for Order database validation.

    The DAO is discovered and configured by the shared framework fixture.
    """
    return all_resources.orders.dao
