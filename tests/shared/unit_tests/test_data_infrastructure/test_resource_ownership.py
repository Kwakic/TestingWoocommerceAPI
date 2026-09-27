"""Unit tests for the test-data ownership boundary.

These tests verify that the ownership registry only tracks resources that
were explicitly registered by the test lifecycle.

The registry does not delete resources itself. Actual deletion remains the
responsibility of the existing entity cleanup mechanism.
"""

from EcommerceAPI.src.test_data.ownership.resource_ownership import (
    ResourceOwnershipRegistry,
)


def test_register_resource_tracks_owned_id():
    registry = ResourceOwnershipRegistry()

    registry.register("customers", 123)

    assert registry.owned_ids("customers") == ["123"]


def test_duplicate_registration_is_idempotent():
    registry = ResourceOwnershipRegistry()

    registry.register("customers", 123)
    registry.register("customers", 123)

    assert registry.owned_ids("customers") == ["123"]
    assert registry.counts() == {"customers": 1}


def test_mark_deleted_removes_resource_from_cleanup_candidates():
    registry = ResourceOwnershipRegistry()

    registry.register("customers", 123)
    registry.mark_deleted("customers", 123)

    assert registry.owned_ids("customers") == []
    assert registry.all_ids("customers") == ["123"]


def test_unregistered_resource_is_not_cleaned():
    registry = ResourceOwnershipRegistry()

    registry.mark_deleted("customers", 999)

    assert registry.owned_ids("customers") == []
    assert registry.all_ids("customers") == []


def test_registered_seed_like_resource_is_only_owned_when_explicitly_registered():
    """Ensure existing seed data is never implicitly claimed by test cleanup."""
    registry = ResourceOwnershipRegistry()

    assert registry.owned_ids("customers") == []

    registry.register("customers", 123)

    assert registry.owned_ids("customers") == ["123"]
