"""Explicit ownership tracking for test-created resources.

This module records which resources were deliberately created by the current
test lifecycle and therefore may be cleaned up.

It does not perform API calls or delete resources itself. The existing entity
cleanup mechanism remains responsible for actual resource deletion.

ResourceOwnershipRegistry handles:
- explicit resource registration
- duplicate registration protection
- marking resources already deleted
- identifying resources that still require cleanup
- exposing ownership state for the cleanup lifecycle
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OwnedResource:
    """Describe a resource explicitly owned by the current test lifecycle."""

    resource_type: str
    resource_id: str
    deleted: bool = False


class ResourceOwnershipRegistry:
    """Track resources explicitly created by tests.

    The registry is intentionally small. It is an ownership boundary, not a
    replacement for the framework's existing cleanup implementation.
    """

    def __init__(self) -> None:
        self._resources: dict[str, dict[str, OwnedResource]] = {}

    def register(self, resource_type: str, resource_id: str | int) -> None:
        """Register a resource as owned by the current test lifecycle."""
        if not resource_type:
            raise ValueError("resource_type must not be empty")

        if resource_id is None:
            raise ValueError("resource_id must not be None")

        normalized_id = str(resource_id)
        resources = self._resources.setdefault(resource_type, {})

        if normalized_id in resources:
            return

        resources[normalized_id] = OwnedResource(
            resource_type=resource_type,
            resource_id=normalized_id,
        )

    def mark_deleted(self, resource_type: str, resource_id: str | int) -> None:
        """Mark an owned resource as already deleted."""
        normalized_id = str(resource_id)
        resources = self._resources.get(resource_type)

        if not resources or normalized_id not in resources:
            return

        resources[normalized_id] = OwnedResource(
            resource_type=resource_type,
            resource_id=normalized_id,
            deleted=True,
        )

    def owned_ids(self, resource_type: str) -> list[str]:
        """Return currently owned resource IDs that still require cleanup."""
        resources = self._resources.get(resource_type, {})
        return [
            resource.resource_id
            for resource in resources.values()
            if not resource.deleted
        ]

    def all_ids(self, resource_type: str) -> list[str]:
        """Return every registered resource ID, including deleted resources."""
        return list(self._resources.get(resource_type, {}).keys())

    def snapshot(self) -> dict[str, list[OwnedResource]]:
        """Return a copy of the current ownership state."""
        return {
            resource_type: list(resources.values())
            for resource_type, resources in self._resources.items()
        }

    def has_resources(self) -> bool:
        """Return whether at least one resource has been registered."""
        return any(self._resources.values())

    def counts(self) -> dict[str, int]:
        """Return the number of registered resources by resource type."""
        return {
            resource_type: len(resources)
            for resource_type, resources in self._resources.items()
        }
