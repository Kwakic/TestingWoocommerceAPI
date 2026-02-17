# tests/conftest.py
import os
import importlib
import pytest


@pytest.fixture(scope="session")
def api_base_url() -> str:
    """
    Global API shared URL resolver.

    Controlled via:
      SERVICE=customers|orders|products|...
      ENV=test|staging|prod
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
            f"Unknown SERVICE='{service}'. "
            f"Valid values: {list(service_modules)}"
        )

    module = importlib.import_module(service_modules[service])

    try:
        return module.API_HOSTS[env]
    except KeyError:
        raise RuntimeError(
            f"ENV='{env}' not defined in {service} API_HOSTS. "
            f"Available: {list(module.API_HOSTS.keys())}"
        )
