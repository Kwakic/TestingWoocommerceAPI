"""
Entity metadata used by CI, reporting and future deployment policies.

Only values that cannot be discovered automatically belong here.

Entity names are discovered dynamically by `discover_entity_names()`.
The owning team is derived from the entity name (Entity = Team).

This file should remain intentionally small.


An example for the future:

ENTITY_METADATA = {
    "customers": {
        "tier": "critical",
        "owner": "customers",
        "deployment_gate": True,
        "slack_channel": "#customers",
    }
}

"""

from __future__ import annotations

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
    },
    # Future examples:
    #
    # "orders": {
    #     "tier": "critical",
    # },
    #
    # "products": {
    #     "tier": "high",
    # },
}
