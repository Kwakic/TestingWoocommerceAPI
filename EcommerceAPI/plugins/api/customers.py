"""
Plugin: customer-specific API fixtures (domain layer).

This module provides fixtures for interacting with the Customers API domain.
It builds on top of shared infrastructure (api_client) and domain helpers.

Fixtures
--------
- create_valid_customer (function):
    Factory fixture for creating a valid customer (happy-path only).

    Behavior:
    * Delegates customer creation to `customers_helper`
    * Validates HTTP transport (status_code == 201)
    * Extracts and returns JSON payload as a dict
    * Validates schema + domain rules via validators
    * Registers created resources for cleanup via shared_api_resources

    Contract:
    * ALWAYS returns a valid customer dict
    * NEVER returns HttpResponse
    * ALWAYS performs validation (transport + schema)

    Intended usage:
    * Positive (happy-path) tests
    * Scenarios where a valid customer is required as a precondition

- customer_api_raw (function):
    Provides direct access to the underlying APIClient.

    Behavior:
    * Skips helper logic and validation layers
    * Returns raw HttpResponse objects

    Intended usage:
    * Negative tests (invalid payloads, edge cases)
    * Low-level API interaction
    * Debugging scenarios

Design notes
------------
* This plugin is DOMAIN-SPECIFIC (customers only).
* Relies on `shared_api_resources` provided by the entities plugin.
* Uses helpers for payload generation and request execution.
* Uses validators for schema and business rule enforcement.
* Keeps test code clean by abstracting HTTP and validation details.

Notes
-----
- This plugin should NOT contain shared logic used by other domains.
- Each entity (products, orders, etc.) should have its own plugin module.
- Follows the "thin fixture, rich helper" principle.
- Ensures strong separation between:
    transport layer (APIClient),
    domain logic (helpers),
    and test interface (fixtures).
"""

from typing import Callable
import logging
import pytest

# from EcommerceAPI.src.shared.helpers.cleanup_helpers import set_default_api_client
from EcommerceAPI.src.customers.validators.customer_validators import (
    assert_valid_customer_response,
)

from EcommerceAPI.src.test_data.builders.customers.customer_builder import (
    CustomerBuilder,
)
from EcommerceAPI.src.test_data.provisioning.customers.customer_provisioner import (
    CustomerProvisioner,
)

# from EcommerceAPI.src.clients.api_client import APIClient

log = logging.getLogger(__name__)


# ---------------------------------------
# Fixture: create_valid_customer
# ---------------------------------------
@pytest.fixture(scope="function")
def create_valid_customer(shared_api_resources) -> Callable[..., dict]:
    """
    This fixture acts as the test-facing "Gatekeeper" between the
    test-data/provisioning layers and tests.

    It:
    ✔ Builds valid customer creation data through CustomerBuilder
    ✔ Provisions the customer through CustomerProvisioner
    ✔ Receives the HttpResponse from the provisioning flow
    ✔ Validates the setup transport status (201)
    ✔ Extracts and validates the response body
    ✔ Registers the created resource for cleanup
    ✔ Returns a clean dict to the test

    IMPORTANT:
    ----------
    Helper response mode (return_http_response=True) is still used by
    tests when they need to inspect the HTTP response of the operation
    under test. The valid-data fixture receives its HttpResponse from
    CustomerProvisioner instead of requesting response mode directly
    from CustomersHelper.

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
    customers = create_valid_customer()
    assert customers["email"]

    Args:
        shared_api_resources (dict): Injected resources containing helper,
            DAO, and cleanup registry.

    Returns:
        Callable[..., dict]: A function to create a customer with custom fields.

    How it works:
        CustomerBuilder
            ↓
        CustomerProvisioner
            ↓
        CustomersHelper / API
            ↓
        HttpResponse
            ↓
        Fixture validation + ownership registration
            ↓
        validated customer dict
    """
    customer_helper = shared_api_resources["customers_helper"]
    register = shared_api_resources["register_resource"]

    def _create_customer(skip_cleanup: bool = False, **kwargs) -> dict:
        """
        Create a valid customers (happy-path ONLY).

        🔥 CONTRACT (IMPORTANT):
        -----------------------
        - ALWAYS returns a valid customers dict
        - ALWAYS validates status_code == 201
        - ALWAYS validates schema + domain rules
        - NEVER returns HttpResponse
        - NEVER returns invalid data

        FLOW:
        -----
        1. Build valid creation data
        2. Provision through CustomerProvisioner
        3. Validate setup status_code == 201
        4. Extract JSON
        5. Validate schema + domain
        6. Register cleanup

            Builder
              ↓
        CustomerProvisioner
              ↓
        CustomersHelper / API
              ↓
        HttpResponse
              ↓
        status validation
              ↓
        response.json
              ↓
        Pydantic / domain validation
              ↓
        cleanup registration
              ↓
        return dict to test




        Args:
            skip_cleanup (bool):
                If True → resource is NOT registered for cleanup

            **kwargs:
                Custom payload fields (email, password, etc.)

        Returns:
            dict: Validated customer object.
                  The fixture uses the HttpResponse internally to validate
                  the setup contract but never exposes it to the test.

        Raises:
            AssertionError:
                If status_code != 201

            SchemaValidationError:
                If schema is invalid
        """
        # -----------------------------------------
        # 1️⃣ Build and provision customer
        # -----------------------------------------
        # CustomerBuilder generates valid creation data in memory.
        # CustomerProvisioner crosses the system boundary through the
        # existing CustomersHelper/API architecture and returns the
        # HttpResponse needed by this fixture's setup contract.
        customer_data = CustomerBuilder().with_fields(**kwargs).build()
        customer_provisioner = CustomerProvisioner(customer_helper)
        response = customer_provisioner.provision(customer_data)

        # -----------------------------------------------------------------
        # 2️⃣ Transport validation (FAIL FAST) — setup contract
        # -----------------------------------------------------------------
        assert response.status_code == 201, (
            "POST /customers creation failed. "
            f"Expected: 201, got {response.status_code}. "
            f"Response: {response.text}"
        )
        # Note: Using response.text:
        # Customer updating failed. Expected 200, got 400.
        # Response: {"code":"rest_invalid_param","message":"Invalid parameter(s): billing",...}
        # This shows exactly what the server returned.
        # Problem with response.json. If the API returns something that is not JSON (very common when PHP crashes
        # or proxies break), then: response.json
        # will be: None
        # and you lose useful debugging info.

        # -----------------------------------------
        # 3️⃣ Extract JSON to validate body
        # -----------------------------------------
        customer = response.json
        # -----------------------------------------
        # 4️⃣ Structure + business validation via Pydantic
        # -----------------------------------------
        assert_valid_customer_response(customer)

        # -----------------------------------------
        # 5️⃣ Cleanup registration
        # -----------------------------------------
        if not skip_cleanup:
            register("customers", customer["id"])
            log.debug("ℹ️ Registered customers with ID: %s for cleanup.", customer["id"])
        else:
            log.debug("ℹ️ Skipped registering customers %s for cleanup.", customer["id"])

        return customer

    return _create_customer


# ---------------------------------------
# Fixture: raw_customer_api (lazy import)
# ---------------------------------------
@pytest.fixture(scope="function")
def customer_api_raw(api_client):
    """
    Provides direct access to APIClient for customers API calls without helper/fixture validation.

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
