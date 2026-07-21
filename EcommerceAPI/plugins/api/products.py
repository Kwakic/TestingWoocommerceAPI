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
    * Validates structure + domain rules via validators
    * Registers created resources for cleanup via shared_api_resources

    Contract:
    * ALWAYS returns a valid product dict
    * NEVER returns HttpResponse
    * ALWAYS performs validation (transport + structure)

    Intended usage:
    * Positive (happy-path) tests
    * Scenarios where a valid product is required as a precondition

- product_api_raw (function):
    Provides direct access to the underlying APIClient.

    Behavior:
    * Skips helper logic and validation layers
    * Returns raw HttpResponse objects

    Intended usage:
    * Negative tests
    * Low-level API interaction
    * Debugging scenarios

Design notes
------------
* This plugin is DOMAIN-SPECIFIC (products only).
* Relies on `shared_api_resources` provided by the entities plugin.
* Uses helpers for payload generation and request execution.
* Uses validators for structure and business rule enforcement.
* Keeps test code clean by abstracting HTTP and validation details.

Notes
-----
- This plugin should NOT contain shared logic used by other domains.
- Each entity (customers, orders, etc.) should have its own plugin module.
- Follows the "thin fixture, rich helper" principle.
"""

from typing import Callable
import logging

import pytest

from EcommerceAPI.src.products.validators.product_validators import (
    assert_valid_product_response,
)

log = logging.getLogger(__name__)


# ---------------------------------------
# Fixture: create_valid_product
# ---------------------------------------
@pytest.fixture(scope="function")
def create_valid_product(shared_api_resources) -> Callable[..., dict]:
    """
    Factory fixture for creating a validated product.

    This fixture acts as a gatekeeper between the HTTP layer and tests.

    It:
    ✔ Calls helper (returns HttpResponse)
    ✔ Validates transport (status_code)
    ✔ Extracts JSON
    ✔ Validates structure + business rules
    ✔ Registers cleanup
    ✔ Returns a dict

    RETURN CONTRACT
    ---------------
    - ALWAYS returns dict
    - NEVER returns HttpResponse
    - NEVER returns invalid data
    """

    product_helper = shared_api_resources["products_helper"]
    register = shared_api_resources["register_resource"]

    def _create_product(skip_cleanup: bool = False, **kwargs) -> dict:
        """
        Create a valid product (happy-path only).

        Flow
        ----
        helper
            ↓
        HttpResponse
            ↓
        status validation
            ↓
        response.json
            ↓
        Pydantic validation
            ↓
        business validation
            ↓
        cleanup registration
            ↓
        return dict
        """

        # 1. Call helper
        response = product_helper.create_product(
            return_http_response=True,
            **kwargs,
        )

        # 2. Transport validation
        assert response.status_code == 201, (
            "POST /products creation failed. "
            f"Expected: 201, got {response.status_code}. "
            f"Response: {response.text}"
        )

        # 3. Extract JSON
        product = response.json

        # 4. Structure + business validation
        assert_valid_product_response(product)

        # 5. Cleanup registration
        if not skip_cleanup:
            register("products", product["id"])
            log.debug(
                "ℹ️ Registered product with ID=%s for cleanup.",
                product["id"],
            )
        else:
            log.debug(
                "ℹ️ Skipped registering product ID=%s for cleanup.",
                product["id"],
            )

        return product

    return _create_product


# ---------------------------------------
# Fixture: product_api_raw
# ---------------------------------------
@pytest.fixture(scope="function")
def product_api_raw(api_client):
    """
    Provides direct access to APIClient for products API calls.

    This fixture:

    - Returns HttpResponse
    - Skips helper layer
    - Performs no validation

    Intended for:
        * negative tests
        * debugging
        * low-level API interaction
    """
    return api_client
