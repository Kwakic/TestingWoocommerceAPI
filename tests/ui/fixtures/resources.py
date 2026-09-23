"""UI test resource lifecycle fixtures.

This module owns application-data teardown for resources explicitly created by
Playwright UI tests.

Browser state and application state are intentionally separate:
- browser.py owns BrowserContext/Page lifecycle;
- this module owns cleanup of test-created application resources.

Only resources explicitly registered by a test are eligible for cleanup.
Seeded/shared UI data is never discovered or deleted automatically.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Generator

import pytest

log = logging.getLogger(__name__)

ResourceRegistrar = Callable[[str, str], None]


@pytest.fixture
def customer_resource_helper(all_resources):
    """Provide the shared customer helper for UI resource identification.

    This fixture does not create or authenticate customers. It gives UI tests
    access to the framework-level customer helper so a resource created through
    the UI can be resolved by a stable business identifier such as email.
    Customer-domain fixtures remain owned by tests/customers/conftest.py.
    """
    return all_resources.customers.helper


@pytest.fixture(scope="function")
def ui_resources(
    all_resources,
) -> Generator[ResourceRegistrar, None, None]:
    """Register UI-created resources for function-scoped cleanup.

    Example:
        ui_resources("customers", customer_id)

    Only resources registered by the current test are cleaned up during
    teardown. Shared/seeded resources are never discovered automatically.
    """
    registered_resources: list[tuple[str, str]] = []

    def register(resource_type: str, resource_id: str) -> None:
        """Register one explicitly created resource for this test."""
        if not resource_type:
            raise ValueError("resource_type must not be empty")
        if not resource_id:
            raise ValueError("resource_id must not be empty")

        resource = (resource_type, str(resource_id))

        if resource in registered_resources:
            log.debug(
                "UI resource already registered: %s/%s",
                resource_type,
                resource_id,
            )
            return

        registered_resources.append(resource)
        log.debug(
            "Registered UI resource for cleanup: %s/%s",
            resource_type,
            resource_id,
        )

    yield register

    if not registered_resources:
        log.debug("No UI resources registered — skipping application teardown.")
        return

    log.info("🔧 Starting teardown of created UI resources...")

    cleanup_summary: list[str] = []

    # Group explicitly registered resources by entity so the UI teardown
    # follows the same lifecycle and logging model as API teardown.
    resources_by_type: dict[str, list[str]] = {}

    for resource_type, resource_id in registered_resources:
        resources_by_type.setdefault(resource_type, []).append(resource_id)

    for resource_type, resource_ids in resources_by_type.items():
        bundle = all_resources.entities.get(resource_type)

        if bundle is None:
            message = (
                f"Cannot clean up UI resource type '{resource_type}': "
                "entity is not registered."
            )
            log.error("❌ %s", message)
            cleanup_summary.append(f"❌ {message}")
            continue

        resource_label = (
            resource_type[:-1] if resource_type.endswith("s") else resource_type
        )

        log.info(
            "🧹 Cleaning up %s(s)... (%d queued)",
            resource_label,
            len(resource_ids),
        )

        # Reuse the framework's standard cleanup helper so UI-created
        # resources use the same deletion semantics as API-created resources.
        from EcommerceAPI.src.shared.helpers.cleanup_helpers import cleanup_items

        already_deleted_ids = set()
        total_created = len(set(resource_ids))

        cleanup_items(
            resource_type=resource_type,
            resource_ids=resource_ids,
            delete_method=bundle.delete_method,
            label=resource_label,
            summary_log=cleanup_summary,
            total_created=total_created,
            already_deleted_ids=already_deleted_ids,
        )

        for resource_id in resource_ids:
            all_resources.mark_deleted(resource_type, resource_id)

    created_counts = {
        resource_type: len(set(resource_ids))
        for resource_type, resource_ids in resources_by_type.items()
    }

    log.info(
        "\n🧹 ====================================== UI CLEANUP SUMMARY ======================================"
    )
    log.info("📊 Created during test run: %s", created_counts)
    log.info("🧾 Cleanup total summary:")
    for line in cleanup_summary:
        log.info("   • %s", line)
    log.info("✅ All UI test data cleanup completed.\n")
