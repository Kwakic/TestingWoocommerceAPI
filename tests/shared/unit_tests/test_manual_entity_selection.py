"""Check the manual CI form and entity selection without a WooCommerce stack."""

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from EcommerceAPI.plugins.entities import build_entity_matrix

pytestmark = [pytest.mark.shared, pytest.mark.unit, pytest.mark.pr]

ROOT = Path(__file__).resolve().parents[3]


def generate(*args):
    return subprocess.run(
        [sys.executable, ".github/scripts/generate_matrix.py", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


def test_form_offers_all_registered_entities():
    workflow = ROOT / ".github/workflows/manual-entity-tests.yml"
    form = yaml.load(workflow.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    choices = form["on"]["workflow_dispatch"]["inputs"]["entity"]["options"]
    entities = [entry["entity"] for entry in build_entity_matrix()["include"]]
    assert sorted(choices) == sorted(["all", *entities])


@pytest.mark.parametrize("args", [(), ("--entity", "all")], ids=["default", "all"])
def test_all_preserves_the_existing_matrix(args):
    result = generate(*args)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == build_entity_matrix()


@pytest.mark.parametrize(
    "entry", build_entity_matrix()["include"], ids=lambda entry: entry["entity"]
)
def test_one_entity_keeps_its_registry_metadata(entry):
    result = generate("--entity", entry["entity"])
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {"include": [entry]}


def test_unregistered_entity_fails_without_a_matrix():
    result = generate("--entity", "shared")
    assert result.returncode != 0
    assert "invalid choice" in result.stderr
    assert result.stdout == ""
