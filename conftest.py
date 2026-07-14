"""
Test suite conftest.py

Loads framework-level shared plugins + specific plugins.

Shared plugins live inside the installable framework:
    - EcommerceAPI/plugins/
"""

pytest_plugins = [
    # -----------------------
    # Core Framework Plugins
    # -----------------------
    "EcommerceAPI.plugins.logging_plugin",  # MUST load first!!!
    "EcommerceAPI.plugins.config_pytest",
    "EcommerceAPI.plugins.reporting",
    "EcommerceAPI.plugins.allure_autogen",
    # -----------------------
    # Core Dependency Layer
    # -----------------------
    "EcommerceAPI.plugins.entities",  # <-- defines shared_api_resources
    "EcommerceAPI.plugins.db_fixtures",
    "EcommerceAPI.plugins.api_fixtures",  # <-- uses shared_api_resources
    # -----------------------
    # API Layer (split by domain)
    # -----------------------
    "EcommerceAPI.plugins.api.shared",
    "EcommerceAPI.plugins.api.customers",
    "EcommerceAPI.plugins.api.products",
    "EcommerceAPI.plugins.api.orders",
    "EcommerceAPI.plugins.api.coupons",
]
