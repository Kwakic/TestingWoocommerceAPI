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
