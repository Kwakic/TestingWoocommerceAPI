"""
Test suite conftest.py

Loads framework-level shared plugins + specific plugins.

Shared plugins live inside the installable framework:
    - EcommerceAPI/plugins/
"""

pytest_plugins = [
    # -----------------------
    # Shared Framework Plugins
    # -----------------------
    "EcommerceAPI.plugins.logging_plugin",   # MUST load first
    "EcommerceAPI.plugins._config",
    "EcommerceAPI.plugins.reporting",
    "EcommerceAPI.plugins.allure_autogen",
    "EcommerceAPI.plugins.entities",  # <-- defines shared_api_resources
    "EcommerceAPI.plugins.db_fixtures",
    "EcommerceAPI.plugins.api_fixtures",  # <-- uses shared_api_resources

    # -----------------------
    # Customer-Specific Plugins (enable if needed)
    # -----------------------
    # "tests.customers.plugins._config",
    # "tests.customers.plugins.api_fixtures",
    # "tests.customers.plugins.entities",
]
