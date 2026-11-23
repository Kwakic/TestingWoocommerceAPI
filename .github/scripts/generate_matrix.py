#!/usr/bin/env python3

import argparse
import json
import sys
from pathlib import Path

# Imported after the repository root has been added to sys.path.


def main() -> None:
    """Generate the GitHub Actions matrix from the framework."""

    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root))

    from EcommerceAPI.plugins.entities import build_entity_matrix

    matrix = build_entity_matrix()
    entries = matrix["include"]
    parser = argparse.ArgumentParser(description="Select framework entities for CI.")
    parser.add_argument(
        "--entity",
        choices=["all", *(entry["entity"] for entry in entries)],
        default="all",
        help="Return one registry entry, or the full matrix (default).",
    )
    entity = parser.parse_args().entity
    if entity != "all":
        matrix["include"] = [entry for entry in entries if entry["entity"] == entity]
    print(json.dumps(matrix))


if __name__ == "__main__":
    main()
