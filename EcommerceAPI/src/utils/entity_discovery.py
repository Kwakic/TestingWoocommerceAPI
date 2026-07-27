# team_discover.py

"""
Entity discovery utilities.

The framework derives the owning business entity dynamically from
pytest nodeids. No hardcoded entity list is required.

Examples:
    - "tests/customers/api/test_x.py::test_y" -> "customers"
    - "tests\\customers\\api\\test_x.py::test_y" -> "customers"
      (Windows-style paths)
    - "tests/shared/preflight/test_logging.py::test_globals" -> "shared"

Discovery rules:
- The entity is the first path segment immediately below `tests/`.
- Tests under `tests/shared/...` belong to the shared framework entity.
- The function is defensive: it accepts None/empty input and
  normalizes Windows and POSIX paths.

Public API:
- extract_entity_from_nodeid(nodeid) -> Optional[str]
- extract_entity (alias)
"""

from __future__ import annotations

from typing import Optional

__all__ = ["extract_entity_from_nodeid", "extract_entity"]


def extract_entity_from_nodeid(nodeid: Optional[str]) -> Optional[str]:
    """
    Extract the business entity from a pytest nodeid.

    Args:
        nodeid:
            Pytest nodeid
            (e.g. "tests/customers/api/test_x.py::test_y").

    Returns:
        The business entity (the first directory immediately below
        `tests/`), or None if it cannot be determined.

        Examples:
            tests/customers/... -> "customers"
            tests/orders/...    -> "orders"
            tests/shared/...    -> "shared"
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
extract_entity = extract_entity_from_nodeid
