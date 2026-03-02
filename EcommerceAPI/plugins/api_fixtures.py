"""
Plugin: small API fixtures (api_client and create_valid_customer factory).

This module provides a minimal, well-documented set of fixtures used by API tests.

Fixtures
--------
- api_client (session):
    Constructs a shared APIClient using a service-specific shared URL
    provided by the test layer (e.g. customers/orders/products).

    Design notes:
    * The plugin itself is service-agnostic.
    * The actual API shared URL is injected via the `api_base_url` fixture,
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
    Returns the low-level APIClient

Notes
-----
- The plugin expects the entities plugin to provide the `shared_api_resources` fixture.
- We avoid import-time side effects by lazily importing APIClient inside fixtures.
"""

from typing import Callable
import logging
import pytest

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # IDE-only: point to the test-level fixture so PyCharm can navigate to it. Do NOT import conftest at runtime!
    # TYPE_CHECKING imports are ignored at runtime, so they’re safe to add into framework code.
    from tests.conftest import api_base_url as _api_base_url_fixture

from EcommerceAPI.src.shared.helpers.cleanup_helpers import set_default_api_client
from EcommerceAPI.src.customers.schemas.customer_schema_validator import validate_customer_response_schema
from EcommerceAPI.src.customers.validators.customer_assertions import assert_valid_customer_response
from EcommerceAPI.src.clients.api_client import APIClient

log = logging.getLogger(__name__)


# -------------------------
# api_client fixture
# -------------------------
@pytest.fixture(scope="session")
def api_client(api_base_url: "_api_base_url_fixture"):
    """
    Provide a session-scoped APIClient instance (transport + orchestration layer).

    Parameters
    ----------
    api_base_url : str
        Service-specific API shared URL injected from the test layer
        (e.g. tests/customers/conftest.py).

    What it does:
    --------
    - Fails fast with a clear error if APIClient cannot be imported.
    - Wires the instance into legacy cleanup helpers (best-effort).
    """
    api_client = APIClient(base_url=api_base_url)

    # Best-effort wiring into legacy cleanup helpers.
    if callable(set_default_api_client):
        try:
            set_default_api_client(api_client)
        except Exception as exc:
            log.warning("Failed to wire default API client: %s", exc)

    return api_client


# ---------------------------------------
# Fixture: create_valid_customer
# ---------------------------------------
@pytest.fixture(scope="function")
def create_valid_customer(shared_api_resources) -> Callable[..., dict]:
    """
    This fixture acts as a "Gatekeeper" between the HTTP layer and tests.

    It:
    ✔ Calls helper (which returns HttpResponse)
    ✔ Validates transport (status_code)
    ✔ Extracts JSON safely
    ✔ Validates schema + domain rules
    ✔ Returns a clean dict for tests

    WHY:
    ----
    - Prevents tests from dealing with HTTP details
    - Ensures consistent validation across all tests
    - Fails fast on API issues
    - Guarantees that returned object is always valid

    RETURN CONTRACT:
    ----------------
    - ALWAYS returns dict
    - NEVER returns HttpResponse
    - NEVER returns invalid data

    WHEN TO USE:
    ------------
    ✅ Positive tests (happy path)
    ❌ Negative tests → use raw_customer_api

    EXAMPLE:
    --------
    customer = create_valid_customer()
    assert customer["email"]

    Args:
        shared_api_resources (dict): Injected resources containing helper, DAO, and cleanup registry.

    Returns:
        Callable[..., dict]: A function to create a customer with custom fields.

    How it works:
        Inside fixture: response = customer_helper.create_customer(return_response=True) --> returns HttpResponse
        Then: customer = response.json
              return customer --> So the FINAL output of fixture is: dict
        - Inside fixture → HttpResponse (temporary)
        - Outside fixture → dict (final contract)
    """
    customer_helper = shared_api_resources["customers_helper"]
    register = shared_api_resources["register_resource"]

    def _create_customer(skip_cleanup: bool = False, **kwargs) -> dict:
        """
        Create a valid customer (happy-path ONLY).

        🔥 CONTRACT (IMPORTANT):
        -----------------------
        - ALWAYS returns a valid customer dict
        - ALWAYS validates status_code == 201
        - ALWAYS validates schema + domain rules
        - NEVER returns HttpResponse
        - NEVER returns invalid data

        FLOW:
        -----
        1. Call helper → returns HttpResponse
        2. Validate status_code (fail-fast)
        3. Extract JSON
        4. Validate schema + domain
        5. Register cleanup

        Args:
            skip_cleanup (bool):
                If True → resource is NOT registered for cleanup

            **kwargs:
                Custom payload fields (email, password, etc.)

        Returns:
            dict: Validated customer object
                  Internally uses HttpResponse but never exposes it (for status code)

        Raises:
            AssertionError:
                If status_code != 201

            SchemaValidationError:
                If schema is invalid
        """
        # -----------------------------------------
        # 1️⃣ Call helper → HttpResponse
        # By setting flag "return_http_response=True" it returns HttpResponse necessary to validate status_code...
        # -----------------------------------------
        response = customer_helper.create_customer(
            return_http_response=True,
            **kwargs
        )

        # -----------------------------------------------------------------
        # 2️⃣ Transport validation (FAIL FAST) Status validated BEFORE JSON
        # -----------------------------------------------------------------
        assert response.status_code == 201, (
            f"Customer creation failed.\n"
            f"Expected: 201\n"
            f"Actual: {response.status_code}\n"
            f"Response: {response.json}"
        )

        # -----------------------------------------
        # 3️⃣ Extract JSON to validate body
        # -----------------------------------------
        customer = response.json
        # -----------------------------------------
        # 4️⃣ Schema + domain validation
        # -----------------------------------------
        validate_customer_response_schema(customer)
        assert_valid_customer_response(customer)

        # -----------------------------------------
        # 5️⃣ Cleanup registration
        # -----------------------------------------
        if not skip_cleanup:
            register("customers", customer["id"])
            log.debug("ℹ️ Registered customer with ID: %s for cleanup.", customer["id"])
        else:
            log.debug("ℹ️ Skipped registering customer %s for cleanup.", customer["id"])

        return customer
    return _create_customer


# ---------------------------------------
# Fixture: raw_customer_api (lazy import)
# ---------------------------------------
@pytest.fixture(scope="function")
def customer_api_raw(api_client):
    """
    Provides direct access to APIClient for customer API calls without helper/fixture validation.

    When to use:
        - Testing invalid payloads, malformed fields, or bad requests
        - Skips helper logic (no auto-generated data, no implicit validators)

    This fixture:
    - Returns HttpResponse (no validation)
    - Skips helper layer and fixture validation
    - Is suitable for:
        * negative tests
        * debugging scenarios
        * low-level API interaction

    Returns:
        HttpResponse (NOT requests.Response)

    Notes:
        - ⚠️ Not truly "raw" — still returns HttpResponse.
        - Response includes status_code, JSON, text, headers, etc.
        - For true raw requests.Response, use APIClient.request_raw()
    """
    return api_client
