"""
Plugin: product-specific API fixtures (domain layer).

This module provides fixtures for interacting with the Products API domain.
It builds on top of shared infrastructure (api_client) and domain helpers.

Fixtures
--------
- create_valid_product (function):
    Factory fixture for creating a valid product (happy-path only).

    Behavior:
    * Delegates product creation to `products_helper`
    * Validates HTTP transport (status_code == 201)
    * Extracts and returns JSON payload as a dict
    * Validates schema + domain rules via validators
    * Registers created resources for cleanup via shared_api_resources

    Contract:
    * ALWAYS returns a valid product dict
    * NEVER returns HttpResponse
    * ALWAYS performs validation (transport + schema)

    Intended usage:
    * Positive (happy-path) tests
    * Scenarios where a valid product is required as a precondition

- product_api_raw (function):
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
* This plugin is DOMAIN-SPECIFIC (products only).
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
from EcommerceAPI.src.products.validators.product_validators import (
    assert_valid_product_response,
)


# from EcommerceAPI.src.clients.api_client import APIClient

log = logging.getLogger(__name__)


# ---------------------------------------
# Fixture: create_valid_product
# ---------------------------------------
@pytest.fixture(scope="function")
def create_valid_product(shared_api_resources) -> Callable[..., dict]:
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
    ❌ Negative tests → use raw_product_api

    EXAMPLE:
    --------
    products = create_valid_product()
    assert products["email"]

    Args:
        shared_api_resources (dict): Injected resources containing helper, DAO, and cleanup registry.

    Returns:
        Callable[..., dict]: A function to create a products with custom fields.

    How it works:
        Inside fixture: response = product_helper.create_product(return_response=True) --> returns HttpResponse
        Then: products = response.json
              return products --> So the FINAL output of fixture is: dict
        - Inside fixture → HttpResponse (temporary)
        - Outside fixture → dict (final contract)
    """
    product_helper = shared_api_resources["products_helper"]
    register = shared_api_resources["register_resource"]

    def _create_product(skip_cleanup: bool = False, **kwargs) -> dict:
        """
        Create a valid products (happy-path ONLY).

        🔥 CONTRACT (IMPORTANT):
        -----------------------
        - ALWAYS returns a valid products dict
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
            dict: Validated products object
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
        response = product_helper.create_product(return_http_response=True, **kwargs)

        # -----------------------------------------------------------------
        # 2️⃣ Transport validation (FAIL FAST) Status validated BEFORE JSON
        # -----------------------------------------------------------------
        assert response.status_code == 201, (
            f" POST /Products creation failed."
            f"Expected: 201, got {response.status_code}"
            f"Response: {response.text}"
        )
        # Note: Using response.text:
        # Product updating failed. Expected 200, got 400.
        # Response: {"code":"rest_invalid_param","message":"Invalid parameter(s): billing",...}
        # This shows exactly what the server returned.
        # Problem with response.json. If the API returns something that is not JSON (very common when PHP crashes
        # or proxies break), then: response.json
        # will be: None
        # and you lose useful debugging info.

        # -----------------------------------------
        # 3️⃣ Extract JSON to validate body
        # -----------------------------------------
        product = response.json
        # -----------------------------------------
        # 4️⃣ Structure + business validation via Pydantic
        # -----------------------------------------
        assert_valid_product_response(product)

        # -----------------------------------------
        # 5️⃣ Cleanup registration
        # -----------------------------------------
        if not skip_cleanup:
            register("products", product["id"])
            log.debug("ℹ️ Registered products with ID: %s for cleanup.", product["id"])
        else:
            log.debug("ℹ️ Skipped registering products %s for cleanup.", product["id"])

        return product

    return _create_product


# ---------------------------------------
# Fixture: raw_product_api (lazy import)
# ---------------------------------------
@pytest.fixture(scope="function")
def product_api_raw(api_client):
    """
    Provides direct access to APIClient for products API calls without helper/fixture validation.

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
