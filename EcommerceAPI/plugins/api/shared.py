"""
Plugin: shared API infrastructure fixtures (service-agnostic).

This module provides foundational API fixtures used across all entity domains
(customers, products, orders, etc.).

Fixtures
--------
- api_client (session):
    Constructs a shared APIClient instance using a service-specific base URL
    provided by the test layer.

    Design notes:
    * This plugin is completely service-agnostic.
    * The API base URL is injected via the `api_base_url` fixture,
      which must be defined at the test layer (e.g. tests/customers/conftest.py).
    * This avoids hardcoding service names or relying on brittle path-based logic.
    * The client acts as the transport/orchestration layer for all API interactions.

    Responsibilities:
    * Centralized HTTP communication
    * Reusable across all entity domains
    * Acts as a dependency for domain-specific fixtures (customers, products, etc.)

Notes
-----
- This plugin contains NO domain logic (no customers/products/etc.).
- Domain-specific behavior must live in dedicated plugins (e.g. api/customers.py).
- Designed to be stable, minimal, and reusable across all services.
- Can be extended in the future with cross-cutting concerns
  (auth, retries, headers, tracing, etc.).
"""

import logging
import pytest

from EcommerceAPI.src.shared.helpers.cleanup_helpers import set_default_api_client

from EcommerceAPI.src.clients.api_client import APIClient

log = logging.getLogger(__name__)


# -------------------------
# api_client fixture
# -------------------------
@pytest.fixture(scope="session")
def api_client(api_base_url: str):
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
