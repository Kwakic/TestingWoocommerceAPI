# team_discover.py

"""
Team discovery utilities.

A "team" is inferred dynamically from pytest nodeids.
No hardcoded team list is required.

Examples:
    - "tests/customers/api/test_x.py::test_y" -> "customers"
    - "tests\\customers\\api\\test_x.py::test_y" -> "customers"  (Windows-style paths)
    - "tests/shared/utils/test_z.py::test_a" -> "shared"

Rules:
- Team is the first path segment immediately under a `tests/` directory.
- Tests under `tests/shared/...` are treated as a real team ("shared").
- The function is defensive: it accepts None/empty input and normalizes backslashes.

Public API:
- extract_team_from_nodeid(nodeid) -> Optional[str]
- extract_team (alias)
"""
from __future__ import annotations

from typing import Optional

__all__ = ["extract_team_from_nodeid", "extract_team"]


def extract_team_from_nodeid(nodeid: Optional[str]) -> Optional[str]:
    """
    Extract the team name from a pytest nodeid.

    Args:
        nodeid: pytest nodeid string
                (e.g. "tests/customers/api/test_x.py::test_y").

    Returns:
        The team name (first segment after `tests/`), or None if it cannot be determined.
        Shared tests return the explicit team name "shared".
    """
    if not nodeid:
        return None

    # Strip parametrization / test part and normalize path
    path_part = nodeid.split("::", 1)[0].strip()
    if not path_part:
        return None

    # Normalize Windows paths to POSIX-style
    normalized = path_part.replace("\\", "/")

    # Split and remove empty segments
    parts = [p for p in normalized.split("/") if p]

    try:
        idx = parts.index("tests")
        team = parts[idx + 1].strip()
        return team or None
    except (ValueError, IndexError):
        return None


# Convenience alias
extract_team = extract_team_from_nodeid
