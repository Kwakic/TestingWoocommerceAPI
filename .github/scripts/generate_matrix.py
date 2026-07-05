#!/usr/bin/env python3

from pathlib import Path
import sys
import json

from EcommerceAPI.plugins.entities import discover_entity_names

# --------------------------------------------------
# Make the repository root importable.
#
# Repository
# ├── .github/scripts/generate_matrix.py
# └── EcommerceAPI/
#
# Running this script directly makes Python start from
# .github/scripts, so we prepend the repository root.
# --------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

matrix = {
    "entity": discover_entity_names(),
}

print(json.dumps(matrix))
