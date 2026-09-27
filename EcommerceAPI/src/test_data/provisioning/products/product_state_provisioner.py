"""
Product state provisioner.

This module is responsible for taking already-prepared Product state data
and applying that state to an existing Product in the real WooCommerce
environment through the existing ProductsHelper.

Architecture

Existing Product
↓
ProductStateProvisioner
↓
ProductsHelper
↓
ProductsApi
↓
WooCommerce

The state provisioner deliberately does NOT:

generate test data;

customize scenario data;

validate HTTP status codes;

validate response schemas;

register cleanup;

use pytest fixtures;

access the database directly.

The provisioner is intentionally separate from ProductProvisioner.

ProductProvisioner creates a new Product from creation data.
ProductStateProvisioner changes the state of an already-existing Product.

The state itself is prepared by ProductStateBuilder. The provisioner is
responsible only for crossing the system boundary and applying that prepared
state through the existing domain helper.

Flow

ProductStateBuilder → ProductStateProvisioner → ProductsHelper
→ ProductsApi → WooCommerce
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from EcommerceAPI.src.core.http_response import HttpResponse
from EcommerceAPI.src.products.helpers.products_helper import ProductsHelper


class ProductStateProvisioner:
    """

    Apply prepared state data to an existing WooCommerce Product.

    The state provisioner is the bridge between a test-data state definition
    and the real Product resource.

    It receives:

        - an existing Product ID;
        - already-prepared state data.

    It delegates the actual update operation to ProductsHelper and returns
    the framework ``HttpResponse`` so the caller (normally a pytest fixture)
    can apply the appropriate setup contract.

    Unlike ProductProvisioner, this class does not create a new Product.
    It operates only on a Product that already exists.

    The provisioner also deliberately does not generate or enrich the state.
    ProductStateBuilder is responsible for defining which fields a particular
    scenario wants to change.

    Example
    -------
        state = {
            "regular_price": "29.99",
        }

        provisioner = ProductStateProvisioner(product_helper)
        response = provisioner.provision(product_id, state)

    The caller remains responsible for:

        HttpResponse
            ↓
        expected status validation
            ↓
        response-body/domain validation

    This separation keeps the provisioner focused on system interaction while
    the fixture remains the test-facing validation and lifecycle boundary.
    """


def __init__(self, product_helper: ProductsHelper) -> None:
    """
    Initialize the Product state provisioner.

    The ProductsHelper is injected rather than created internally so that
    the provisioner remains independent from pytest fixtures and can be
    reused by different test setup paths.

    Args:
        product_helper:
            Existing domain helper responsible for Product API
            orchestration.
    """
    self.product_helper = product_helper


def provision(
    self,
    product_id: int,
    state: Mapping[str, Any],
) -> HttpResponse:
    """
    Apply prepared state data to an existing Product.

    This method is intentionally limited to input validation and
    delegation. It does not generate state, modify the prepared mapping,
    validate the HTTP response, or register resource ownership.

    Args:
        product_id:
            WooCommerce Product ID of the resource being modified.

        state:
            Prepared Product state data. Only fields explicitly included
            in this mapping are sent to ProductsHelper. The provisioner
            does not fill in unspecified fields.

    Returns:
        HttpResponse:
            Response from the Product update request.

    Raises:
        TypeError:
            If ``product_id`` is not an integer or ``state`` is not a
            mapping.

        ValueError:
            If ``product_id`` is not positive or ``state`` is empty.

    Notes:
        The provisioner intentionally does not validate the HTTP status.
        A setup caller may expect 200 for a successful WooCommerce update,
        but that transport assertion belongs to the caller/fixture.

    Flow:
        1. Validate the Product ID.
        2. Validate that prepared state is a mapping.
        3. Reject empty state.
        4. Delegate the update to ProductsHelper.
        5. Return the framework HttpResponse to the caller.
        :param state:
        :param product_id:
        :param self:
    """

    # 1. Validate the Product ID before crossing the system boundary.
    if not isinstance(product_id, int) or isinstance(product_id, bool):
        raise TypeError("product_id must be an integer.")

    if product_id <= 0:
        raise ValueError("product_id must be greater than zero.")

    # 2. State must already be prepared by ProductStateBuilder (or
    #    another valid state source). The provisioner does not build it.
    if not isinstance(state, Mapping):
        raise TypeError(
            "state must be a mapping containing the prepared product state."
        )

    # 3. An empty state would produce an invalid/no-op update and usually
    #    indicates that the scenario was not configured correctly.
    if not state:
        raise ValueError(
            "state cannot be empty. Prepare the product state before "
            "calling ProductStateProvisioner."
        )

    # 4. Delegate the actual update to the existing domain helper.
    #    return_http_response=True intentionally preserves the transport
    #    response for the caller/fixture to validate.
    return self.product_helper.update_product(
        product_id=product_id,
        payload=dict(state),
        return_http_response=True,
    )
