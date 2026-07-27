import os
from pathlib import Path

import pytest

from EcommerceAPI.src.configs.config_loader import get_api_host
from EcommerceAPI.src.metadata.entity_metadata import discover_framework_entities
from EcommerceAPI.src.utils.entity_discovery import extract_entity_from_nodeid


@pytest.fixture(scope="session")
def api_base_url() -> str:
    """
    Return the API base URL for the current test session.

    The URL is resolved automatically from:

    - the active service
    - the current API_ENV

    The returned value is shared by all tests in the session.
    """
    return get_api_host(os.getenv("SERVICE", "customers"))


# ----------------------------------------------------------------------
# Framework-level execution suites.
#
# Keys represent the directory names under tests/shared/.
# Values represent the pytest marker applied to tests in that directory.
#
# Example:
#
#   tests/shared/contracts/  -> @pytest.mark.contract
#   tests/shared/security/   -> @pytest.mark.security
#   tests/shared/preflight/  -> @pytest.mark.preflight
#
# Performance is intentionally excluded because performance tests belong
# to each individual business entity (e.g. tests/customers/performance/).
# ----------------------------------------------------------------------
FRAMEWORK_SUITE_MARKERS = {
    "contracts": "contract",
    "security": "security",
    "preflight": "preflight",
}


def pytest_collection_modifyitems(config, items):
    """
    Automatically assign pytest markers using the framework discovery
    architecture.

    Two independent discovery mechanisms are used:

    1. Entity ownership discovery
       Determines which business entity owns a test.
       The entity is extracted from the pytest nodeid and validated
       against the framework's architectural registry.

    2. Suite discovery
       Detects framework execution suites from the test directory
       structure.

    This implementation avoids hardcoded business entities while keeping
    pytest collection aligned with the framework's Single Source of Truth.
    """

    # Architectural registry of supported business entities.
    framework_entities = set(discover_framework_entities())

    for item in items:

        # ----------------------------------------------------------
        # Business entity ownership discovery
        #
        # Example:
        #
        #   tests/customers/api/test_create_customer.py
        #          │
        #          ▼
        #      customers
        #
        # Every registered entity automatically receives its
        # corresponding pytest marker.
        # ----------------------------------------------------------
        entity = extract_entity_from_nodeid(item.nodeid)

        if entity and entity in framework_entities:
            item.add_marker(getattr(pytest.mark, entity))

        parts = Path(str(item.fspath)).parts

        # ----------------------------------------------------------
        # Entity performance discovery
        #
        # Performance tests live inside each business entity:
        #
        #   tests/customers/performance/
        #   tests/products/performance/
        #
        # therefore this marker is inferred directly from the path.
        # ----------------------------------------------------------
        if "performance" in parts:
            item.add_marker(pytest.mark.performance)

        # ----------------------------------------------------------
        # Shared framework suite discovery
        #
        # Framework suites execute independently from entity-specific
        # test suites.
        #
        # The repository directory name does not always match the
        # pytest marker. For example:
        #
        #   tests/shared/contracts/ -> @pytest.mark.contract
        #
        # Therefore we map directory names to their corresponding
        # pytest markers.
        # ----------------------------------------------------------
        for directory, marker in FRAMEWORK_SUITE_MARKERS.items():
            if directory in parts:
                item.add_marker(getattr(pytest.mark, marker))
