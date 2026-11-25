"""Review ownership checks run in the normal PR unit lane without GitHub credentials."""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

from EcommerceAPI.plugins.entities import discover_entities
from EcommerceAPI.src.metadata import entity_metadata as registry
from EcommerceAPI.src.utils import db_utility

pytestmark = [pytest.mark.shared, pytest.mark.unit, pytest.mark.pr]

ROOT = Path(__file__).resolve().parents[3]


def test_entity_source_paths_have_registered_owners():
    # Include new domains added to one layer before they reach the CI matrix.
    sources = set()
    for layer in (
        "tests",
        "EcommerceAPI/src/entities",
        "EcommerceAPI/src/test_data/factories",
        "EcommerceAPI/src/test_data/builders",
        "EcommerceAPI/src/test_data/provisioning",
        "EcommerceAPI/src/test_data/seeds",
    ):
        for folder in (ROOT / layer).iterdir():
            if not folder.is_dir() or folder.name.startswith((".", "__")):
                continue
            if layer == "tests" and folder.name in {"ui", "shared"}:
                continue
            sources.add(folder.name)
    plugins = (ROOT / "EcommerceAPI/plugins/api").glob("*.py")
    sources.update(p.stem for p in plugins if not p.stem.startswith(("__", "shared_")))
    registry.validate_ownership(sources)


def test_runtime_bundles_have_registered_owners(monkeypatch):
    # The Orders DAO checks its storage mode during discovery. Keep that read offline.
    credentials = dict(
        user="unit",
        password="unit",
        host="localhost",
        port=3306,
        database="unit",
        table_prefix="wp_",
    )
    monkeypatch.setattr(db_utility, "get_db_credentials", lambda: credentials)
    monkeypatch.setattr(db_utility.DBUtility, "execute_select", lambda *args: [])
    bundles = discover_entities(Mock())
    assert bundles, "Expected runtime discovery to find a business entity."
    registry.validate_ownership(bundles)


def test_new_registered_entity_requires_explicit_ownership(monkeypatch):
    monkeypatch.setattr(
        registry, "FRAMEWORK_ENTITIES", (*registry.FRAMEWORK_ENTITIES, "inventory")
    )
    with pytest.raises(ValueError, match="Add an explicit team.*inventory"):
        registry.validate_ownership()


def test_unknown_metadata_and_unregistered_source(monkeypatch):
    with pytest.raises(ValueError, match="Unknown entities.*inventory"):
        registry.validate_ownership(["inventory"])
    monkeypatch.setitem(registry.ENTITY_METADATA, "returns", {"team": "commerce team"})
    with pytest.raises(ValueError, match="Unknown entities.*returns"):
        registry.validate_ownership()


@pytest.mark.parametrize("entry", [{}, {"team": "purchasing typo"}, {"team": []}, None])
def test_invalid_domain_team_is_actionable(monkeypatch, entry):
    monkeypatch.setitem(registry.ENTITY_METADATA, "orders", entry)
    with pytest.raises(ValueError, match="orders"):
        registry.validate_ownership()


def test_team_can_own_multiple_entities(monkeypatch):
    monkeypatch.setitem(registry.ENTITY_METADATA, "products", {"team": "commerce team"})
    registry.validate_ownership()


@pytest.mark.parametrize("reviewer", ["", "commerce team", "@", "@org/"])
def test_invalid_review_recipient(monkeypatch, reviewer):
    monkeypatch.setitem(registry.TEAM_REVIEWERS, "commerce team", reviewer)
    with pytest.raises(ValueError, match="GitHub.*commerce team"):
        registry.validate_ownership()


def test_platform_requires_a_reviewer(monkeypatch):
    monkeypatch.delitem(registry.TEAM_REVIEWERS, registry.PLATFORM_TEAM)
    with pytest.raises(ValueError, match="TEAM_REVIEWERS.*QA platform"):
        registry.validate_ownership()


def test_codeowners_matches_registry():
    result = subprocess.run(
        [sys.executable, ".github/scripts/generate_codeowners.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_stale_codeowners_fails_check_until_regenerated(tmp_path):
    github = tmp_path / ".github"
    scripts = github / "scripts"
    scripts.mkdir(parents=True)
    script = scripts / "generate_codeowners.py"
    shutil.copyfile(ROOT / ".github/scripts/generate_codeowners.py", script)
    checked_in = ROOT / ".github/CODEOWNERS"
    owners = github / "CODEOWNERS"
    owners.write_text("# Outdated review rules\n", encoding="utf-8")
    env = {**os.environ, "PYTHONPATH": str(ROOT)}

    def run(*args):
        return subprocess.run(
            [sys.executable, str(script), *args],
            env=env,
            capture_output=True,
            text=True,
        )

    result = run()
    assert result.returncode == 1
    assert "--write" in result.stderr
    assert run("--write").returncode == 0
    assert owners.read_text(encoding="utf-8") == checked_in.read_text(encoding="utf-8")
    assert run().returncode == 0
