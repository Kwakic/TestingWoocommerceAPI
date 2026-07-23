"""
Framework entity metadata.

This module contains the architectural definition of every business
domain supported by the framework.

Unlike runtime discovery, entities listed here represent domains that
belong to the framework regardless of whether their implementation is
currently complete.

This registry is intentionally explicit.

Adding a new entity is considered an architectural change and therefore
requires updating this file during code review.
"""

from __future__ import annotations

# --------------------------------------------------
# Supported business domains
#
# This is the authoritative registry consumed by:
#
# • GitHub Actions matrix generation
# • Contract suites
# • Security suites
# • Documentation

# Entity metadata.
# Optional attributes override the framework defaults.
# If "team" is omitted, the framework assumes the owning
# team has the same name as the entity.
# --------------------------------------------------

FRAMEWORK_ENTITIES = (
    "customers",
    "orders",
    "products",
    "coupons",
)


def discover_framework_entities() -> list[str]:
    """
    Return every business domain officially supported by the framework.

    Unlike runtime discovery, this function performs no filesystem
    scanning and does not validate whether an entity has been fully
    implemented.

    It simply exposes the architectural registry maintained by the
    framework.

    Returns:
        Sorted list of supported framework entities.
    """
    return sorted(FRAMEWORK_ENTITIES)


# --------------------------------------------------
# Default metadata applied to every discovered entity.
# --------------------------------------------------

DEFAULT_ENTITY_METADATA = {
    "tier": "medium",
}

# --------------------------------------------------
# Per-entity overrides.
#
# Only specify values that differ from the defaults.
# --------------------------------------------------

ENTITY_METADATA = {
    # Critical customer-facing service.
    "customers": {
        "tier": "critical",
        "team": "commerce",
    },
    # Future examples:
    #
    # "orders": {
    #     "tier": "critical",
    # },
    #
    "products": {
        "tier": "high",
        "team": "catalog",
    },
}
