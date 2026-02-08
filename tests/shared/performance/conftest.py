# import os
# import pytest
# from tests.customers.configs.config_customers import API_HOSTS
#
#
# @pytest.fixture(scope="session")
# def api_base_url() -> str:
#     """
#     Resolve and provide the base URL for the Customers API.
#
#     This fixture supplies the service-specific API base URL used by framework-level
#     fixtures (e.g. `request_utility`) and by tests under the customers domain.
#
#     Resolution logic:
#     -----------------
#     1. Read the target environment from the ENV environment variable.
#        - Defaults to "test" if ENV is not set.
#     2. Look up the corresponding base URL in `API_HOSTS`.
#     3. Fail fast with a clear error if the environment key is not defined.
#
#     Scope:
#     ------
#     Session-scoped to ensure a single, consistent base URL is used throughout
#     the entire test run for this service.
#
#     Typical usage:
#     --------------
#     This fixture is not usually requested directly by tests.
#     It is consumed indirectly by higher-level fixtures such as:
#
#         - request_utility
#
#     Example:
#     --------
#         def test_example(request_utility):
#             response = request_utility.get("customers")
#
#     Raises:
#     -------
#     RuntimeError:
#         If the ENV value does not exist in the API_HOSTS mapping.
#     """
#     env = os.getenv("ENV", "test").lower()
#
#     try:
#         return API_HOSTS[env]
#     except KeyError:
#         raise RuntimeError(
#             f"ENV='{env}' not found in customers API_HOSTS"
#         )

# 🔴 The Core Issue
#
# The all_resources fixture is not available because:
#
#     all_resources (entities.py) depends on...
#     shared_api_resources (entities.py) depends on...
#     request_utility (api_fixtures.py) depends on...
#     api_base_url ← Multiple definitions cause plugin load failure
#
# The duplicate api_base_url fixtures are causing the entire plugin chain to fail silently.








# 🔍 Key Discovery
#
# You have THREE api_base_url fixtures with the same name and scope:
#
#     tests/customers/conftest.py:14
#     tests/shared/preflight/conftest.py:7
#     tests/shared/performance/conftest.py:7
#
# This is causing fixture conflicts! Pytest doesn't know which one to use.
#
# But request_utility is missing entirely from the fixture list! ❌
# 🔴 The Root Problem
#
# The request_utility fixture in api_fixtures.py depends on api_base_url, but pytest is confused by multiple definitions, so the entire plugin chain fails to load.
# 🔧 Solution: Remove Duplicate Fixtures
# Step 1: Check the duplicate fixtures
# bash
#
# # Check preflight conftest
# cat tests/shared/preflight/conftest.py
#
# # Check performance conftest
# cat tests/shared/performance/conftest.py
#
# Step 2: Remove or Rename Duplicates
#
# Option A: Remove them (if they're identical to customers)
# bash
#
# # Backup first
# cp tests/shared/preflight/conftest.py tests/shared/preflight/conftest.py.bak
# cp tests/shared/performance/conftest.py tests/shared/performance/conftest.py.bak
#
# # Remove api_base_url fixtures from these files
# # Edit manually or use sed
#
# Option B: Rename them (if they need different URLs)
#
# Change them to be more specific:
# Python
#
# # In tests/shared/preflight/conftest.py
# @pytest.fixture(scope="session")
# def preflight_api_base_url() -> str:
#     # ...
#
# 🔧 Quick Fix: Let Customers Own api_base_url
#
# Since you're running customer tests, delete the duplicates from shared folders:
# Edit tests/shared/preflight/conftest.py:
# bash
#
# code tests/shared/preflight/conftest.py
#
# Remove or comment out the api_base_url fixture entirely.
# Edit tests/shared/performance/conftest.py:
# bash
#
# code tests/shared/performance/conftest.py
#
# Remove or comment out the api_base_url fixture entirely.
# 🎯 Why This Happens
#
# When pytest loads plugins, it discovers all conftest.py files in the test directory tree. Because you're running:
# bash
#
# pytest tests/customers/
#
# Pytest also loads:
#
#     tests/customers/conftest.py ✅
#     tests/shared/preflight/conftest.py ❌ (has duplicate)
#     tests/shared/performance/conftest.py ❌ (has duplicate)
#
# This causes fixture shadowing/conflicts.
# 🔧 Best Practice Solution
#
# Create a root-level api_base_url fixture that all tests can use:
# Edit root conftest.py (at project root):
#
# Add this at the bottom:
# Python
#
# @pytest.fixture(scope="session")
# def api_base_url() -> str:
#     """
#     Global API base URL resolver for all microservices.
#
#     Determines which API to test based on SERVICE and ENV variables.
#     """
#     import os
#
#     # Determine which service we're testing
#     service = os.getenv("SERVICE", "customers").lower()
#     env = os.getenv("API_ENV") or os.getenv("ENV", "test")
#     env = env.lower()
#
#     # Import the appropriate config
#     if service == "customers":
#         from tests.customers.configs.config_customers import API_HOSTS
#     elif service == "orders":
#         from tests.orders.configs.config_orders import API_HOSTS
#     elif service == "products":
#         from tests.products.configs.config_products import API_HOSTS
#     else:
#         raise RuntimeError(f"Unknown SERVICE: {service}")
#
#     try:
#         return API_HOSTS[env]
#     except KeyError:
#         raise RuntimeError(
#             f"ENV='{env}' not found in {service} API_HOSTS. "
#             f"Available: {list(API_HOSTS.keys())}"
#         )
#
# Then remove api_base_url from:
#
#     tests/customers/conftest.py
#     tests/shared/preflight/conftest.py
#     tests/shared/performance/conftest.py