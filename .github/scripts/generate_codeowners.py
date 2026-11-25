"""Build the GitHub pull-request review rules in .github/CODEOWNERS.

Read entity-to-team and team-to-reviewer assignments from
EcommerceAPI/src/metadata/entity_metadata.py. The shared QA platform rule
covers the whole repository. Later rules assign each domain's directories
and individual files to its team's GitHub reviewer.

Run from the repository root:
    python .github/scripts/generate_codeowners.py          # Check the file
    python .github/scripts/generate_codeowners.py --write  # Regenerate it

Check mode exits silently on a match and fails if the file is missing or
out of date. Write mode replaces the file, including any hand edits.
Change the registry to reassign a team or reviewer. Change render_codeowners()
when domain-owned code moves to a path outside the existing patterns.

GitHub uses these rules to request human reviews. Pytest runs the automated
checks, and repository settings determine whether approval blocks a merge.
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def render_codeowners() -> str:
    """Return the generated file with the platform default before domain rules.

    GitHub uses the last matching rule for a changed file. A directory rule
    covers its descendants, so adding a DAO or helper under an existing
    entity package needs no new entry. The entity/team headings are comments
    for readers. The handle on each path rule identifies the GitHub reviewer.
    """
    from EcommerceAPI.src.metadata.entity_metadata import (
        ENTITY_METADATA,
        PLATFORM_TEAM,
        TEAM_REVIEWERS,
        discover_framework_entities,
        validate_ownership,
    )

    validate_ownership()
    platform = TEAM_REVIEWERS[PLATFORM_TEAM]
    lines = [
        "# GitHub uses this file to request a human review for changed paths.",
        "# Each rule lists a path pattern followed by its GitHub reviewer.",
        "# The last matching rule wins.",
        "# A trailing / covers the whole directory, including all subdirectories.",
        "# For example, /EcommerceAPI/src/entities/products/ covers its DAO and API.",
        "#",
        "# Change team or reviewer assignments in EcommerceAPI/src/metadata/entity_metadata.py.",
        "# Regenerate: python .github/scripts/generate_codeowners.py --write",
        "# Check:      python .github/scripts/generate_codeowners.py",
        "# Regeneration replaces hand edits. See the ownership guide for examples:",
        "# docs/framework/README_ENTITY_DISCOVER_ARCHITECTURE_GUIDE.md#read-a-codeowners-rule",
        "",
        f"# {PLATFORM_TEAM}: shared framework, CI, infrastructure, reporting and docs",
        f"* {platform}",
        f"/.github/ {platform}",
    ]
    for entity in discover_framework_entities():
        team = ENTITY_METADATA[entity]["team"]
        reviewer = TEAM_REVIEWERS[team]
        lines.extend(
            [
                "",
                f"# {entity} | {team}",
                f"/tests/{entity}/ {reviewer}",
                f"/EcommerceAPI/src/entities/{entity}/ {reviewer}",
                f"/EcommerceAPI/plugins/api/{entity}.py {reviewer}",
                f"/EcommerceAPI/src/test_data/*/{entity}/ {reviewer}",
                f"/docs/development/team-guides/README_{entity.upper()}.md {reviewer}",
            ]
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    """Compare the checked-in file, or replace it when --write is requested."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Update .github/CODEOWNERS in this checkout",
    )
    args = parser.parse_args()
    path = ROOT / ".github/CODEOWNERS"
    expected = render_codeowners()
    if args.write:
        path.write_text(expected, encoding="utf-8", newline="\n")
    elif not path.is_file() or path.read_text(encoding="utf-8") != expected:
        parser.exit(
            1,
            "Ownership rules have changed. Run python .github/scripts/generate_codeowners.py --write and review .github/CODEOWNERS.\n",
        )


if __name__ == "__main__":
    main()
