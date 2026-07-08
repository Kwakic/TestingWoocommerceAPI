# SECURITY TEST

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

Entities
~~~~~~~~

Every framework entity discovered through:

    discover_framework_entities()

is automatically included in the authentication matrix.

No entity list is maintained inside this test.

Methods
~~~~~~~

GET
POST
PUT
DELETE

Credential variants
~~~~~~~~~~~~~~~~~~~

• invalid key + invalid secret
• invalid key + valid secret
• valid key + invalid secret

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
from jsonschema import validate

from EcommerceAPI.src.utils.credentials_utility import get_wc_api_keys
from EcommerceAPI.src.clients.api_client import APIClient
from EcommerceAPI.src.auth.base_auth import AuthStrategy
from EcommerceAPI.src.metadata.entity_metadata import discover_framework_entities
from tests.shared.contracts.error_schema import error_schema


logger = logging.getLogger(__name__)

pytestmark = [
    pytest.mark.security,
    pytest.mark.negative,
    pytest.mark.contract,
    pytest.mark.shared,
]


# ------------------------------------------------------------------
# Test authentication strategy
# ------------------------------------------------------------------
class InvalidOAuthStrategy(AuthStrategy):
    """
    Test-only authentication strategy used to simulate invalid OAuth credentials.

    This overrides the framework's default OAuth strategy and injects
    intentionally invalid keys into the request.
    """

    def __init__(self, key: str, secret: str):
        from requests_oauthlib import OAuth1

        self.oauth = OAuth1(key, secret)

    def apply(self, request_kwargs):
        request_kwargs["auth"] = self.oauth
        return request_kwargs


# ------------------------------------------------------------------
# Framework entity discovery
#
# The entities plugin is the Single Source of Truth for supported framework entities.
#
# Authentication is a platform concern rather than an entity concern,
# therefore every discovered entity automatically participates in the authentication matrix.
#
# Adding a new entity requires NO changes to this test.
# ------------------------------------------------------------------

ENTITIES = discover_framework_entities()

# ------------------------------------------------------------------
# HTTP method matrix
#
# Tuple format:
#
#     (
#         HTTP method,
#         requires resource id,
#         requires request payload,
#     )
#
# This allows a single test implementation to validate every authentication scenario consistently.
# ------------------------------------------------------------------

METHOD_MATRIX = [
    ("get", False, False),
    ("post", False, True),
    ("put", True, True),
    ("delete", True, False),
]


# ------------------------------------------------------------------
# Authentication security test
# ------------------------------------------------------------------
@pytest.mark.parametrize("entity", ENTITIES)
@pytest.mark.parametrize("method, needs_id, needs_payload", METHOD_MATRIX)
@pytest.mark.parametrize(
    "auth_variant",
    [
        "invalid_key_and_secret",
        "invalid_key",
        "invalid_secret",
    ],
)
def test_authentication_rejects_invalid_credentials(
    api_client,
    entity,
    method,
    needs_id,
    needs_payload,
    auth_variant,
):
    """
    Ensure invalid OAuth credentials are rejected by all API endpoints.

    Design principle
    ----------------
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
    # Build invalid credential scenario
    # --------------------------------------------------------------

    creds = get_wc_api_keys()

    if auth_variant == "invalid_key_and_secret":
        invalid_key = "ck_invalid_key_123"
        invalid_secret = "cs_fake_secret_xyz"
        expected_message = "Consumer key is invalid."

    elif auth_variant == "invalid_key":
        invalid_key = "ck_invalid_key_123"
        invalid_secret = creds["wc_secret"]
        expected_message = "Consumer key is invalid."

    else:
        invalid_key = creds["wc_key"]
        invalid_secret = "cs_invalid_secret_456"
        expected_message = "Invalid signature - provided signature does not match."

    # --------------------------------------------------------------
    # Create isolated API client with invalid credentials
    # --------------------------------------------------------------

    base_url = api_client.base_url

    test_client = APIClient(
        base_url, auth_strategy=InvalidOAuthStrategy(invalid_key, invalid_secret)
    )

    # ------------------------------------------------------------------
    # Build the endpoint under test.
    #
    # PUT and DELETE require a resource identifier.
    # We intentionally inject a non-existent ID because authentication
    # should fail before resource existence is evaluated.
    # ------------------------------------------------------------------

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

    # POST / PUT require payloads.
    # We send an empty payload because authentication should fail
    # before payload validation occurs.
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
