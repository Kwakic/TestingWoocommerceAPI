"""Plugin: product-specific API fixtures (domain layer).

This module provides fixtures for interacting with the Products API domain.
It builds on top of shared infrastructure (api_client), domain helpers,
and the Product test-data/provisioning architecture.

Fixtures
--------
- create_valid_product (function):
    Factory fixture for creating a valid product (happy-path only).

    Behavior:
    * Builds valid Product creation data through `ProductBuilder`
    * Uses `ProductFactory` for unspecified valid defaults
    * Provisions the Product through `ProductProvisioner`
    * Validates HTTP transport (status_code == 201)
    * Extracts and returns the JSON payload as a dict
    * Validates schema + domain rules via validators
    * Registers created resources for cleanup via shared_api_resources

    Contract:
    * ALWAYS returns a valid product dict
    * NEVER returns HttpResponse
    * ALWAYS performs validation (transport + response structure)
    * Registers ownership unless `skip_cleanup=True`

    Intended usage:
    * Positive (happy-path) tests
    * Scenarios where a valid product is required as a precondition
    * Tests that need scenario-specific Product creation data

- product_api_raw (function):
    Provides direct access to the underlying APIClient.

    Behavior:
    * Bypasses ProductFactory and ProductBuilder
    * Bypasses ProductProvisioner and ProductsHelper
    * Performs no fixture-level response validation
    * Provides direct API control to the test

    Intended usage:
    * Negative tests (invalid payloads, edge cases)
    * Low-level API interaction
    * Debugging scenarios

Design notes
------------
* This plugin is DOMAIN-SPECIFIC (products only).
* Relies on `shared_api_resources` provided by the entities plugin.
* Uses ProductFactory/ProductBuilder for test-data preparation.
* Uses ProductProvisioner to cross the system boundary.
* Uses ProductsHelper for domain/API orchestration.
* Uses validators for response structure and business-rule enforcement.
* Registers only explicitly test-created Products for cleanup.
* Keeps the pytest fixture as the lifecycle gatekeeper between the
  test-data/provisioning layers and the test.

Notes
-----
- This plugin should NOT contain shared logic used by other domains.
- Each entity (customers, orders, etc.) should have its own plugin module.
- Test-data generation belongs to the Product Factory/Builder layer.
- System provisioning belongs to the Product Provisioner layer.
- API/domain orchestration belongs to the Products Helper layer.
- Fixture-level validation and ownership registration belong here.
- Negative tests should use `product_api_raw` when direct API control
  is required.
- Follows the "thin fixture, explicit lifecycle gatekeeper" principle.

Architecture
------------
    ProductBuilder
        ↓
    ProductFactory
        ↓
    ProductProvisioner
        ↓
    ProductsHelper
        ↓
    ProductsApi
        ↓
    WooCommerce
        ↓
    HttpResponse
        ↓
    Fixture validation
        ↓
    Ownership registration
        ↓
    validated Product dict
"""

from __future__ import annotations

from typing import Callable
import logging

import pytest

from EcommerceAPI.src.products.validators.product_validators import (
    assert_valid_product_response,
)

from EcommerceAPI.src.test_data.builders.products.product_builder import (
    ProductBuilder,
)

from EcommerceAPI.src.test_data.provisioning.products.product_provisioner import (
    ProductProvisioner,
)


log = logging.getLogger(__name__)


# ---------------------------------------
# Fixture: create_valid_product
# ---------------------------------------
@pytest.fixture(scope="function")
def create_valid_product(shared_api_resources) -> Callable[..., dict]:
    """
    This fixture acts as the test-facing "Gatekeeper" between the
    test-data/provisioning layers and tests.

    It:
        ✔ Builds valid Product creation data through ProductBuilder
        ✔ Uses ProductFactory for unspecified valid defaults
        ✔ Provisions the Product through ProductProvisioner
        ✔ Receives the HttpResponse from the provisioning flow
        ✔ Validates the setup transport status (201)
        ✔ Extracts and validates the response body
        ✔ Registers the created resource for cleanup
        ✔ Returns a clean dict to the test

    IMPORTANT:
    ----------
    The Product test-data architecture prepares the creation payload before
    it reaches the ProductsHelper.

    ProductBuilder
        ↓
    ProductFactory
        ↓
    ProductProvisioner
        ↓
    ProductsHelper / API
        ↓
    HttpResponse

    The fixture receives that HttpResponse so it can enforce the setup
    contract before exposing the Product to the test.

    RETURN CONTRACT:
    ----------------
    - ALWAYS returns dict
    - NEVER returns HttpResponse
    - NEVER returns invalid data
    - Registers ownership unless skip_cleanup=True

    WHEN TO USE:
    ------------
    ✅ Positive tests (happy path)
    ✅ Tests requiring a valid Product as a precondition

    ❌ Negative tests → use product_api_raw

    EXAMPLE:
    --------
    product = create_valid_product()
    assert product["name"]

    Args:
        shared_api_resources (dict):
            Injected shared resources containing the ProductsHelper and
            ownership registry.

    Returns:
        Callable[..., dict]:
            A function that creates a Product with optional
            scenario-specific fields.

    How it works:
        ProductBuilder
            ↓
        ProductFactory
            ↓
        ProductProvisioner
            ↓
        ProductsHelper / API
            ↓
        HttpResponse
            ↓
        Fixture validation + ownership registration
            ↓
        validated Product dict
    """
    product_helper = shared_api_resources["products_helper"]
    register = shared_api_resources["register_resource"]

    product_provisioner = ProductProvisioner(product_helper)

    def _create_product(skip_cleanup: bool = False, **kwargs) -> dict:
        """
        Create a valid Product (happy-path ONLY).

        🔥 CONTRACT (IMPORTANT):
        -------------------------
        - ALWAYS returns a valid Product dict
        - ALWAYS validates status_code == 201
        - ALWAYS validates the Product response
        - NEVER returns HttpResponse
        - NEVER returns invalid data
        - Registers the Product for cleanup unless skip_cleanup=True

        FLOW:
        -----
        1. Build scenario-specific creation data
        2. Apply ProductFactory defaults
        3. Provision through ProductProvisioner
        4. Validate setup status_code == 201
        5. Extract JSON
        6. Validate response structure + domain rules
        7. Register cleanup
        8. Return validated Product dict

            ProductBuilder
                ↓
            ProductFactory
                ↓
            ProductProvisioner
                ↓
            ProductsHelper / API
                ↓
            HttpResponse
                ↓
            status validation
                ↓
            response.json
                ↓
            Product validation
                ↓
            cleanup registration
                ↓
            return dict to test

        Args:
            skip_cleanup (bool):
                If True → Product is NOT registered for cleanup.

            **kwargs:
                Scenario-specific Product creation fields, such as:
                name, sku, type, regular_price, sale_price,
                description, or short_description.

                Any field not supplied here is generated/provided by
                ProductFactory through ProductBuilder.

        Returns:
            dict:
                Validated Product object.

                The fixture uses the HttpResponse internally to validate
                the setup contract but never exposes it to the test.

        Raises:
            AssertionError:
                If status_code != 201.

            SchemaValidationError:
                If the Product response fails the configured response
                validation.
        """

        # -----------------------------------------
        # 1️⃣ Build Product creation data
        # -----------------------------------------
        # ProductBuilder collects scenario-specific overrides.
        # ProductFactory supplies all unspecified valid defaults.
        product_data = ProductBuilder().with_fields(**kwargs).build()

        # -----------------------------------------
        # 2️⃣ Provision Product
        # -----------------------------------------
        # ProductProvisioner crosses the system boundary through the
        # existing ProductsHelper/API architecture and returns the
        # HttpResponse required by this fixture's setup contract.
        response = product_provisioner.provision(product_data)

        # -----------------------------------------
        # 3️⃣ Transport validation (FAIL FAST)
        # -----------------------------------------
        # The setup operation must successfully create the Product.
        # response.text is deliberately included because it preserves the
        # server's actual error body when creation fails.
        assert response.status_code == 201, (
            "POST /products creation failed. "
            f"Expected: 201, got {response.status_code}. "
            f"Response: {response.text}"
        )

        # -----------------------------------------
        # 4️⃣ Extract JSON to validate body
        # -----------------------------------------
        product = response.json

        # -----------------------------------------
        # 5️⃣ Structure + business validation
        # -----------------------------------------
        # Validate the Product returned by WooCommerce before exposing it
        # to the test.
        assert_valid_product_response(product)

        # -----------------------------------------
        # 6️⃣ Cleanup registration
        # -----------------------------------------
        # Only explicitly test-created resources are registered.
        # Seeded/shared resources are not registered by this fixture.
        if not skip_cleanup:
            register("products", product["id"])
            log.debug(
                "ℹ️ Registered product with ID: %s for cleanup.",
                product["id"],
            )
        else:
            log.debug(
                "ℹ️ Skipped registering product %s for cleanup.",
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
    Provides direct access to APIClient for Products API calls without
    Product test-data/provisioning or fixture validation.

    When to use:
        - Testing invalid payloads, malformed fields, or bad requests
        - Testing edge cases that deliberately bypass valid-data setup
        - Low-level API interaction
        - Debugging API behavior

    This fixture:
        - Returns the API client's HttpResponse
        - Skips ProductFactory
        - Skips ProductBuilder
        - Skips ProductProvisioner
        - Skips ProductsHelper
        - Performs no fixture-level response validation

    IMPORTANT:
        The fixture is intentionally outside the normal positive-test
        architecture. Negative tests often need complete control over the
        payload and therefore must not be forced through valid test-data
        generation.

    Returns:
        HttpResponse:
            The response produced by the underlying APIClient.

    Notes:
        - ⚠️ "Raw" means raw from the Product fixture architecture;
          it still uses the project's APIClient/HttpResponse abstraction.
        - This fixture should not be used when a valid Product precondition
          is required. Use create_valid_product instead.
    """
    return api_client
