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

import re
from collections.abc import Iterable

# --------------------------------------------------
# Supported business domains
#
# This is the authoritative registry consumed by:
#
# • GitHub Actions matrix generation
# • Contract suites
# • Security suites
# • Documentation

# Every business entity declares its logical owning team in ENTITY_METADATA.
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
# Required ownership and optional criticality overrides.
# --------------------------------------------------

ENTITY_METADATA = {
    # Critical customer-facing service.
    "customers": {
        "tier": "tier: critical",
        "team": "commerce team",
    },
    "orders": {
        "tier": "tier: critical",
        "team": "purchase team",
    },
    "coupons": {
        "tier": "tier: low",
        "team": "promo team",
    },
    "products": {
        "tier": "tier: high",
        "team": "catalog team",
    },
}


# Logical responsibilities and their GitHub review recipients. On a personal
# repository the same maintainer can review on behalf of several teams.
PLATFORM_TEAM = "QA platform"
TEAM_REVIEWERS = {
    PLATFORM_TEAM: "@Kwakic",
    "commerce team": "@Kwakic",
    "purchase team": "@Kwakic",
    "catalog team": "@Kwakic",
    "promo team": "@Kwakic",
}


def validate_ownership(discovered: Iterable[str] = ()) -> None:
    """Fail before emitting a CI matrix or CODEOWNERS with incomplete ownership."""
    entities = set(FRAMEWORK_ENTITIES)
    if len(entities) != len(FRAMEWORK_ENTITIES):
        raise ValueError("Remove duplicate entries from FRAMEWORK_ENTITIES.")
    for entity in entities:
        if (
            not isinstance(entity, str)
            or not re.fullmatch(r"[a-z][a-z0-9_-]*", entity)
            or entity
            in {
                "all",
                "ui",
                "shared",
            }
        ):
            raise ValueError(
                f"Invalid business entity {entity!r} in FRAMEWORK_ENTITIES."
            )

    unknown = (set(ENTITY_METADATA) | set(discovered)) - entities
    if unknown:
        raise ValueError(
            f"Unknown entities {sorted(unknown)}. Update FRAMEWORK_ENTITIES or correct the names."
        )
    missing = entities - ENTITY_METADATA.keys()
    if missing:
        raise ValueError(
            f"Add an explicit team in ENTITY_METADATA for {sorted(missing)}."
        )

    if PLATFORM_TEAM not in TEAM_REVIEWERS:
        raise ValueError(f"Add a TEAM_REVIEWERS entry for {PLATFORM_TEAM!r}.")
    for team, reviewer in TEAM_REVIEWERS.items():
        if (
            not isinstance(team, str)
            or not team
            or not team.isprintable()
            or team.strip() != team
        ):
            raise ValueError(f"Invalid team name {team!r} in TEAM_REVIEWERS.")
        if not isinstance(reviewer, str) or not re.fullmatch(
            r"@[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*(?:/[A-Za-z0-9][A-Za-z0-9_-]*)?", reviewer
        ):
            raise ValueError(
                f"Set a GitHub @user or @org/team reviewer for {team!r} in TEAM_REVIEWERS."
            )
    for entity, metadata in ENTITY_METADATA.items():
        if not isinstance(metadata, dict):
            raise ValueError(
                f"Provide a metadata mapping with a team for {entity!r} in ENTITY_METADATA."
            )
        team = metadata.get("team")
        if not isinstance(team, str) or team not in TEAM_REVIEWERS:
            raise ValueError(
                f"Set ENTITY_METADATA[{entity!r}]['team'] to a team defined in TEAM_REVIEWERS; got {team!r}."
            )
