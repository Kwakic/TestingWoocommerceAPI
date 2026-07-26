# root/tests/conftest.py
import os

import pytest

from pathlib import Path

from EcommerceAPI.src.configs.config_loader import get_api_host


@pytest.fixture(scope="session")
def api_base_url() -> str:
    """
    Return the API base URL for the current test session.

    The URL is resolved automatically from:

    - the active service
    - the current API_ENV

    The returned value is shared by all tests in the session.
    """

    return get_api_host(os.getenv("SERVICE", "customers"))


def pytest_collection_modifyitems(config, items):
    """
    Automatically assign entity markers to collected tests.

    Tests are organised by directory, so the framework can determine the
    appropriate marker without requiring every test file to declare it
    manually.

    For example:

        tests/customers/  → @pytest.mark.customers
        tests/products/   → @pytest.mark.products
        tests/orders/     → @pytest.mark.orders

    This keeps the test suite consistent and avoids duplicated markers
    throughout the project.
    """

    for item in items:
        # Derive markers from the test's location in the repository.
        path = Path(str(item.fspath))

        parts = path.parts

        if "customers" in parts:
            item.add_marker(pytest.mark.customers)

        if "orders" in parts:
            item.add_marker(pytest.mark.orders)

        if "products" in parts:
            item.add_marker(pytest.mark.products)

        if "coupons" in parts:
            item.add_marker(pytest.mark.coupons)

        if "shared" in parts:
            item.add_marker(pytest.mark.shared)

        if "performance" in parts:
            item.add_marker(pytest.mark.performance)

        if "security" in parts:
            item.add_marker(pytest.mark.security)

        if "preflight" in parts:
            item.add_marker(pytest.mark.preflight)
