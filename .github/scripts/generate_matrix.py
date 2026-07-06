#!/usr/bin/env python3

from pathlib import Path
import json
import sys

# Imported after the repository root has been added to sys.path.


def main() -> None:
    """Generate the GitHub Actions matrix from the framework."""

    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root))

    from EcommerceAPI.plugins.entities import build_entity_matrix

    print(json.dumps(build_entity_matrix()))


if __name__ == "__main__":
    main()
