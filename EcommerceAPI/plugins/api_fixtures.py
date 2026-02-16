"""
Plugin: small API fixtures (request_utility and create_valid_customer factory).

This module provides a minimal, well-documented set of fixtures used by API tests.

Fixtures
--------
- request_utility (session):
    Constructs a shared RequestUtility client using a service-specific global URL
    provided by the test layer (e.g. customers/orders/products).

    Design notes:
    * The plugin itself is service-agnostic.
    * The actual API global URL is injected via the `api_base_url` fixture,
      which is defined in the microservice-level conftest (e.g. tests/customers/conftest.py).
    * This avoids hardcoding service names or doing brittle path-based detection.

- create_valid_customer (function):
    Factory that delegates to the customers_helper to create a valid customer
    (happy-path only). Preserves original behavior:
      * returns the created customer dict on success
      * returns exception.response_json for expected API errors
        (UnexpectedStatusCodeError, SchemaValidationError)
      * optionally validates the response via helper.assert_valid_customer_response
      * registers created resources for cleanup via shared_api_resources["register_resource"]

- raw_customer_api (function):
    Returns the low-level request_utility for negative/raw tests.

Notes
-----
- The plugin expects the entities plugin to provide the `shared_api_resources` fixture.
- We avoid import-time side effects by lazily importing RequestUtility inside fixtures.
"""

from typing import Callable
import logging
import pytest

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # IDE-only: point to the test-level fixture so PyCharm can navigate to it. Do NOT import conftest at runtime!
    # TYPE_CHECKING imports are ignored at runtime, so they’re safe to add into framework code.
    from tests.conftest import api_base_url as _api_base_url_fixture

from EcommerceAPI.src.utilities.exceptions import (
    SchemaValidationError,
    UnexpectedStatusCodeError,
)
from EcommerceAPI.src.helpers.shared.cleanup_helpers import set_default_request_utility
from EcommerceAPI.src.validators.customers.customer_schema_validator import validate_customer_response_schema
from EcommerceAPI.src.validators.customers.customer_assertions import assert_valid_customer_response

log = logging.getLogger(__name__)


# -------------------------
# request_utility fixture
# -------------------------
@pytest.fixture(scope="session")
def request_utility(api_base_url: "_api_base_url_fixture"):
    """
    Provide a session-scoped RequestUtility instance for tests and helpers.

    Parameters
    ----------
    api_base_url : str
        Service-specific API global URL injected from the test layer
        (e.g. tests/customers/conftest.py).

    What it does:
    --------
    - Lazily imports RequestUtility to avoid import-time side effects.
    - Fails fast with a clear error if RequestUtility cannot be imported.
    - Wires the instance into legacy cleanup helpers (best-effort).
    """
    try:
        from EcommerceAPI.src.utilities.requestsUtility import RequestUtility
    except ImportError as exc:
        raise RuntimeError(
            "RequestUtility not found. Ensure EcommerceAPI.src.utilities.requestsUtility is importable."
        ) from exc

    client = RequestUtility(base_url=api_base_url)

    # Best-effort wiring into legacy cleanup helpers.
    if callable(set_default_request_utility):
        try:
            set_default_request_utility(client)
        except Exception as exc:
            log.warning("Failed to wire default request utility: %s", exc)

    return client


# ---------------------------------------
# Fixture: create_valid_customer
# ---------------------------------------
@pytest.fixture(scope="function")
def create_valid_customer(shared_api_resources) -> Callable[..., dict]:
    """
    Factory fixture that creates a valid customer via the project's helper layer.

    This fixture is intended for happy-path tests. For negative tests that intentionally send invalid payloads, use
    the raw_customer_api fixture.

    Args:
        shared_api_resources (dict): Injected resources containing helper, DAO, and cleanup registry.

    Returns:
        Callable[..., dict]: A function to create a customer with custom fields.
    """
    customer_helper = shared_api_resources["customers_helper"]
    register = shared_api_resources["register_resource"]

    def _create_customer(skip_cleanup: bool = False, validate_response: bool = True, **kwargs) -> dict:
        """
        Factory method to create a WooCommerce customer with custom values.

        - It creates a customer using a helper (happy path only)
        - Registers the customer for teardown (unless skip_cleanup)
        - Handles API-level expected errors by returning the error response JSON

        Args:
            skip_cleanup (bool): If True, skip automatic cleanup registration.
            validate_response (bool): If True, assert response schema and critical fields.
            **kwargs: Custom fields to include in the customer payload, e.g., email, password, etc.

        Returns:
            dict: Parsed response from the API (customer object on success or error JSON on expected failure).
        """
        try:
            # Attempt to create customer through API helper
            customer = customer_helper.create_customer(**kwargs)
        except (UnexpectedStatusCodeError, SchemaValidationError) as e:
            # Expected API-level error — return response JSON for test assertions.
            log.warning("Caught API exception during create_customer; returning response JSON.")
            return e.response_json

        # For truly unexpected errors (network, coding bug, etc.), allow them to surface so tests/CI can fail fast.

        # Validate response schema and critical fields for happy-path tests
        # 1. First schema
        # 2. Then domain assertions
        if validate_response:
            validate_customer_response_schema(customer)
            assert_valid_customer_response(customer)

        if not skip_cleanup:
            register("customers", customer["id"])
            log.debug("Registered customer with ID: %s for cleanup.", customer["id"])
        else:
            log.debug("Skipped registering customer %s for cleanup.", customer["id"])

        return customer

    return _create_customer


# ---------------------------------------
# Fixture: raw_customer_api (lazy import)
# ---------------------------------------
@pytest.fixture(scope="function")
def raw_customer_api(request_utility):
    """
    Fixture providing low-level access to the customer API for negative tests and tests that need to inspect raw
    responses.

    When to use:
        - Use this fixture when testing invalid input payloads, malformed fields, or bad request bodies.
        - It skips helper logic like auto-generating emails or asserting 201 status codes.
        - Returns raw API responses (e.g., 400 errors) directly for assertion.
        - Uses the shared session-scoped request_utility fixture.
    """
    return request_utility
