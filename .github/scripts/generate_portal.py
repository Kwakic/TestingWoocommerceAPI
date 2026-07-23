#!/usr/bin/env python3
"""
Generate the GitHub Pages QA Portal.

The portal is generated from the reports currently published to the
GitHub Pages site.

Unlike the GitHub Actions matrix generator, this script intentionally
reflects only published reports rather than every framework entity.

Responsibilities
----------------
* Discover published entity reports.
* Read framework metadata (tier, etc.).
* Build a static QA Portal.
* Write ``site/index.html``.

This script is intentionally deterministic and contains no GitHub
Actions logic.


It follows the same philosophy of this framework:
-------------------------------------------------------------
Discovery
──────────────
discover_entities()

discover_entity_reports()

↓

Models
──────────────
Entity

Report

↓

Rendering
──────────────
build_entity_section()

build_html()

↓

Entry point
──────────────
main()
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import html
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from EcommerceAPI.src.metadata.entity_metadata import (  # noqa: E402
    DEFAULT_ENTITY_METADATA,
    ENTITY_METADATA,
)

SITE_ROOT = Path("site")

# ---------------------------------------------------------------------------
# Public report suites
#
# Display order defines the visual ordering within the generated portal.
# ---------------------------------------------------------------------------

PUBLIC_SUITES = (
    ("smoke", "🔥", "Smoke"),
    ("integration", "🔗", "Integration"),
    ("regression", "🔬", "Regression"),
    ("performance", "⏱️", "Performance"),
)

# ---------------------------------------------------------------------------
# Project links
# ---------------------------------------------------------------------------

GITHUB_REPOSITORY = "https://github.com/Kwakic/TestingWoocommerceAPI"

GITHUB_ACTIONS = f"{GITHUB_REPOSITORY}/actions"

DOCUMENTATION = f"{GITHUB_REPOSITORY}/blob/main/README.md"


# ===========================================================================
# Models
# ===========================================================================


@dataclass(slots=True, frozen=True)
class Report:
    """Represents one published Allure report."""

    suite: str
    icon: str
    title: str


@dataclass(slots=True)
class Entity:
    """Represents one framework entity displayed in the portal."""

    name: str
    tier: str
    reports: list[Report]


# ===========================================================================
# Discovery
# ===========================================================================


def get_entity_tier(entity_name: str) -> str:
    """
    Return the display tier for an entity.

    Framework defaults are merged with any entity-specific overrides.
    """

    metadata = DEFAULT_ENTITY_METADATA.copy()
    metadata.update(ENTITY_METADATA.get(entity_name, {}))

    return metadata["tier"].title()


def discover_entity_reports(entity_dir: Path) -> list[Report]:
    """
    Discover every published report belonging to an entity.

    Parameters
    ----------
    entity_dir:
        Entity directory inside the generated GitHub Pages site.

    Returns
    -------
    list[Report]
        Published reports in architectural display order.
    """

    reports: list[Report] = []

    for suite, icon, title in PUBLIC_SUITES:

        if (entity_dir / suite / "index.html").exists():
            reports.append(
                Report(
                    suite=suite,
                    icon=icon,
                    title=title,
                )
            )

    return reports


def discover_entities() -> list[Entity]:
    """
    Discover entities that currently publish reports.

    Entities without published reports are intentionally omitted from
    the portal to avoid broken links.
    """

    entities: list[Entity] = []

    if not SITE_ROOT.exists():
        return entities

    for entity_dir in sorted(SITE_ROOT.iterdir()):

        if not entity_dir.is_dir():
            continue

        reports = discover_entity_reports(entity_dir)

        if not reports:
            continue

        entities.append(
            Entity(
                name=entity_dir.name,
                tier=get_entity_tier(entity_dir.name),
                reports=reports,
            )
        )

    return entities


# ===========================================================================
# HTML generation
# ===========================================================================


def build_entity_section(entity: Entity) -> str:
    """
    Generate the HTML section representing one framework entity.
    """

    links = "\n".join(
        f"""
        <a class="report-link"
           href="./{entity.name}/{report.suite}/">
            {report.icon} {report.title}
        </a>
        """
        for report in entity.reports
    )

    return f"""
<section class="entity">

    <div class="entity-header">

        <h2>📦 {html.escape(entity.name.title())}</h2>

        <span class="tier {entity.tier.lower()}">
            {entity.tier}
        </span>

    </div>

    <div class="report-links">
        {links}
    </div>

</section>
"""


def build_html(entities: list[Entity]) -> str:
    """
    Build the complete QA Portal document.

    Parameters
    ----------
    entities:
        Published entities to display.

    Returns
    -------
    str
        Complete HTML document.
    """

    entity_sections = "\n".join(build_entity_section(entity) for entity in entities)

    return f"""<!DOCTYPE html>
    <html lang="en">

    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">

        <title>TestEcommerceAPI · QA Portal</title>

        <link rel="stylesheet" href="./style.css">
    </head>

    <body>

    <div class="container">

    <header>

    <h1>🧪 TestEcommerceAPI</h1>

    <p class="subtitle">
    API Test Automation Framework
    </p>

    </header>

    <section class="intro">

    <p>
    This portal is generated automatically during GitHub Pages deployment.
    Only reports currently published are displayed.
    </p>

    </section>

    {entity_sections}

    <section class="links">

    <h2>Project Links</h2>

    <ul>

    <li>
    <a href="{GITHUB_ACTIONS}">
    GitHub Actions
    </a>
    </li>

    <li>
    <a href="{DOCUMENTATION}">
    Project Documentation
    </a>
    </li>

    </ul>

    </section>

    <footer>

    Generated automatically during GitHub Pages deployment.

    </footer>

    </div>

    </body>

    </html>
    """


def main() -> None:
    """Generate the QA Portal."""

    entities = discover_entities()

    SITE_ROOT.mkdir(parents=True, exist_ok=True)

    output = SITE_ROOT / "index.html"
    output.write_text(build_html(entities), encoding="utf-8")

    print(f"Generated {output}")


if __name__ == "__main__":
    main()
