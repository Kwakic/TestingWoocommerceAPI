# root/tests/conftest.py
import os
import importlib
import pytest

from pathlib import Path


@pytest.fixture(scope="session")
def api_base_url() -> str:
    """
    Global API shared URL resolver.

    Controlled via:
      SERVICE=customers|orders|products|...
      API_ENV=test|staging|prod
    """

    service = os.getenv("SERVICE", "customers").lower()
    env = os.getenv("API_ENV") or os.getenv("ENV", "test")
    env = env.lower()

    service_modules = {
        "customers": "tests.customers.configs.config_customers",
        "orders": "tests.orders.configs.config_orders",
        "products": "tests.products.configs.config_products",
        "coupons": "tests.coupons.configs.config_coupons",
    }

    if service not in service_modules:
        raise RuntimeError(
            f"Unknown SERVICE='{service}'. " f"Valid values: {list(service_modules)}"
        )

    module = importlib.import_module(service_modules[service])

    try:
        return module.API_HOSTS[env]
    except KeyError:
        raise RuntimeError(
            f"ENV='{env}' not defined in {service} API_HOSTS. "
            f"Available: {list(module.API_HOSTS.keys())}"
        )


def pytest_collection_modifyitems(config, items):
    """
    Automatically apply domain markers based on test folder.

    Because the tests are already organized by folder/domain pytest can automatically apply markers based on folder
    path.This reduces duplication and prevents mistakes.

    If a test file is inside: tests/customers/ pytest automatically adds:
        pytest.mark.customers

    Example:
        tests/customers/ → pytest.mark.customers
        tests/orders/    → pytest.mark.orders
        tests/shared/    → pytest.mark.shared
    """

    for item in items:
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
