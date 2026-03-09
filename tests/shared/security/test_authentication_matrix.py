"""
Authentication Security Test Matrix

Purpose
-------
Verify that all WooCommerce API endpoints reject invalid OAuth credentials.

This is a **framework-level security test** and therefore lives under:

    tests/shared/security/

It must NOT rely on domain fixtures such as customer_helper or order_helper.

Instead it tests the transport layer directly using APIClient.

Coverage
--------
Entities:
    customers
    products
    orders
    coupons

Methods:
    GET
    POST
    PUT
    DELETE

Credential variants:
    invalid key + invalid secret
    invalid key + valid secret
    valid key + invalid secret

Total tests matrix executed:

4 entities
× 4 methods
× 3 auth scenarios
= 48 security tests

"""

import os
import pytest
import logging
from typing import Any, Dict
from requests_oauthlib import OAuth1
from jsonschema import validate

from EcommerceAPI.src.utilities.credentials_utility import get_wc_api_keys
from tests.shared.contracts.error_schema import error_schema
from EcommerceAPI.src.clients.api_client import APIClient

logger = logging.getLogger(__name__)

pytestmark = [
    pytest.mark.security,
    pytest.mark.negative,
]


# ------------------------------------------------------------------
# Entities covered by the authentication matrix
# ------------------------------------------------------------------

ENTITIES = [
    "customers",
    "products",
    "orders",
    "coupons",
]


# ------------------------------------------------------------------
# HTTP method matrix
# ------------------------------------------------------------------

METHOD_MATRIX = [
    ("get", False, False),
    ("post", False, True),
    ("put", True, True),
    ("delete", True, False),
]


# ------------------------------------------------------------------
# Invalid credential combinations
# ------------------------------------------------------------------

def invalid_auth_cases():
    """
    Generate invalid OAuth credential scenarios.

    Returns
    -------
    list[tuple]
        (consumer_key, consumer_secret, expected_error_message)
    """
    creds = get_wc_api_keys()

    return [
        ("ck_invalid_key_123", "cs_fake_secret_xyz", "Consumer key is invalid."),
        ("ck_invalid_key_123", creds["wc_secret"], "Consumer key is invalid."),
        (
            creds["wc_key"],
            "cs_invalid_secret_456",
            "Invalid signature - provided signature does not match.",
        ),
    ]


# ------------------------------------------------------------------
# Authentication security test
# ------------------------------------------------------------------

@pytest.mark.parametrize("entity", ENTITIES)
@pytest.mark.parametrize("method, needs_id, needs_payload", METHOD_MATRIX)
@pytest.mark.parametrize(
    "invalid_key, invalid_secret, expected_message",
    invalid_auth_cases(),
)
def test_authentication_rejects_invalid_credentials(
    api_client,
    entity,
    method,
    needs_id,
    needs_payload,
    invalid_key,
    invalid_secret,
    expected_message,
):
    """
    Ensure invalid OAuth credentials are rejected by all API endpoints.

    Design principle:
    ----------------------------
    We create an isolated APIClient with invalid credentials instead of
    mutating the shared pytest api_client fixture.

    This prevents authentication state leaking across tests.

    Validation layers
    -----------------
    1. Transport validation → HTTP 401
    2. Schema validation    → error response structure
    3. Business validation  → error code + message
    """

    # --------------------------------------------------------------
    # Production safety guard
    # --------------------------------------------------------------
    if os.getenv("ENV") == "prod" and method in ("post", "put", "delete"):
        pytest.skip("Skipping destructive auth tests in production")

    # --------------------------------------------------------------
    # Create isolated API client
    # --------------------------------------------------------------
    # APIClient loads valid credentials from environment automatically.
    # We override the OAuth1 credentials to simulate invalid authentication.

    base_url = api_client.base_url
    test_client = APIClient(base_url)

    test_client.auth = OAuth1(invalid_key, invalid_secret)

    # --------------------------------------------------------------
    # Build endpoint
    # --------------------------------------------------------------
    endpoint = entity

    # Some endpoints require a resource identifier.
    # We inject a fake ID because authentication should fail before
    # resource validation occurs.
    if needs_id:
        endpoint = f"{endpoint}/999999"

    # --------------------------------------------------------------
    # Build request arguments dynamically
    # --------------------------------------------------------------
    kwargs: Dict[str, Any] = {"endpoint": endpoint}

    # POST / PUT require payloads. We send an empty payload because
    # authentication should fail before payload validation.
    if needs_payload:
        kwargs["payload"] = {}

    # --------------------------------------------------------------
    # Execute request dynamically
    # --------------------------------------------------------------
    method_func = getattr(test_client, method)
    response = method_func(**kwargs)

    logger.info(
        "%s %s → invalid key=%s",
        method.upper(),
        endpoint,
        invalid_key,
    )

    # --------------------------------------------------------------
    # Transport validation
    # --------------------------------------------------------------
    assert response.status_code == 401

    # --------------------------------------------------------------
    # Extract JSON response
    # --------------------------------------------------------------
    assert response.json, "Expected JSON authentication error response"
    body = response.json

    # --------------------------------------------------------------
    # Schema validation
    # --------------------------------------------------------------
    validate(instance=body, schema=error_schema)

    # --------------------------------------------------------------
    # Business validation
    # --------------------------------------------------------------
    assert body["code"] == "woocommerce_rest_authentication_error"
    assert body["message"] == expected_message
    assert body["data"]["status"] == 401

