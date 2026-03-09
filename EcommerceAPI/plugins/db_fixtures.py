"""
Plugin: database fixtures.

Provides session-scoped database utilities for integration tests.

Design principles:
- Single DB connection per test session.
- Environment is assumed to be pre-loaded (.env / CI).
- No service-specific logic.
- Safe to use across all microservices.
"""

import pytest
from EcommerceAPI.src.utilities.db_utility import DBUtility


@pytest.fixture(scope="session")
def db():
    """
    Provide a session-scoped database utility.

    Behavior:
      - Initializes DBUtility once per pytest session.
      - Yields the utility for use in tests/helpers.
      - Cleanup is handled internally by DBUtility (engine disposal, connections, etc).

    Assumptions:
      - ENV / MACHINE / DB credentials are already loaded.
    """
    db_util = DBUtility()
    yield db_util
    # DB engine/connection cleanup handled internally by DBUtility if necessary
