"""Exercise the real pytest and xdist reporting hooks without a WooCommerce site."""

import os
import subprocess
import sys
from types import SimpleNamespace

import pytest

from EcommerceAPI.plugins import cleanup_reporting

pytestmark = [pytest.mark.shared, pytest.mark.unit, pytest.mark.pr]


@pytest.mark.parametrize("workers,exit_code", [(1, 0), (1, 1), (2, 1)])
def test_session_summary_across_modules(tmp_path, pytestconfig, workers, exit_code):
    (tmp_path / "conftest.py").write_text(
        """\
from types import SimpleNamespace
import pytest
from EcommerceAPI.plugins import entities
pytest_plugins = [
    "EcommerceAPI.plugins.cleanup_reporting",
    "EcommerceAPI.plugins.entities",
    "tests.ui.fixtures.resources",
]

@pytest.fixture(scope="module")
def api_client():
    def delete(endpoint, params):
        assert params == {"force": True}
        status = {"coupons/1": 200, "coupons/2": 404, "coupons/3": 204,
                  "customers/9": 403}[endpoint]
        return SimpleNamespace(status_code=status)

    bundle = entities.EntityBundle(object(), object(), delete)
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(entities, "discover_entities", lambda _: dict(coupons=bundle, customers=bundle))
        yield object()
"""
    )
    (tmp_path / "test_create.py").write_text(
        """\
def test_create(shared_api_resources):
    register = shared_api_resources["register_resource"]
    register("coupons", 1)
    register("coupons", 1)
    register("coupons", 2)
    register("customers", 9)
"""
    )
    (tmp_path / "test_ui.py").write_text(
        """\
def test_ui(all_resources, ui_resources):
    ui_resources("coupons", "3")
    all_resources.register("coupons", "3")
    all_resources.register("coupons", "4")
    all_resources.mark_deleted("coupons", "4")
    all_resources.register("unknown", "7")
"""
        + ("    assert False, 'intentional test failure'\n" if exit_code else "")
    )
    args = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "--log-cli-level=INFO",
        "--show-capture=no",
    ]
    if workers > 1:
        args.extend(["-p", "xdist.plugin", "-n", str(workers), "--dist=loadfile"])
    result = subprocess.run(
        args,
        cwd=tmp_path,
        env={
            **os.environ,
            "PYTHONPATH": str(pytestconfig.rootpath),
            "PYTEST_ADDOPTS": "",
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
            "PYTHONIOENCODING": "utf-8",
            "API_ENV": "docker",
            "DOCKER_INFRA": "reuse",
        },
        capture_output=True,
        encoding="utf-8",
        timeout=60,
    )
    assert result.returncode == exit_code, result.stdout + result.stderr
    assert result.stdout.count("SESSION CLEANUP SUMMARY") == 1, result.stdout
    summary = result.stdout.split("SESSION CLEANUP SUMMARY")[1]
    assert f"Workers: {workers} | API_ENV=docker | DOCKER_INFRA=reuse" in summary
    rows = [line.split() for line in summary.splitlines()]
    assert ["Entity", "Registered", "Deleted", "Missing", "Failed", "Skipped"] in rows
    assert ["coupons", "4", "2", "1", "0", "2"] in rows
    assert ["customers", "1", "0", "0", "1", "0"] in rows
    assert ["unknown", "1", "0", "0", "0", "1"] in rows
    assert ["Total", "6", "2", "1", "1", "3"] in rows
    if workers == 1:
        assert result.stdout.count("🧹 ==================== API CLEANUP SUMMARY") == 2
        assert result.stdout.count("🧹 ==================== UI CLEANUP SUMMARY") == 1


def test_missing_worker_report_is_disclosed_and_repeated_delivery_is_idempotent():
    config = SimpleNamespace(stash=pytest.Stash())
    node = SimpleNamespace(config=config, gateway=SimpleNamespace(id="gw0"))
    node.workeroutput = {"ecommerce_cleanup": {"orders": (["1"], {"deleted": 1})}}
    cleanup_reporting.pytest_testnodedown(node, error=None)
    cleanup_reporting.pytest_testnodedown(node, error="keyboard-interrupt")
    lost = SimpleNamespace(config=config, gateway=SimpleNamespace(id="gw1"))
    cleanup_reporting.pytest_testnodedown(lost, error="worker lost")
    lines = []
    terminal = SimpleNamespace(
        write_sep=lambda sep, title: lines.append(title), write_line=lines.append
    )
    cleanup_reporting.pytest_terminal_summary(terminal, config)
    assert "Partial totals. No cleanup report from: gw1" in lines
    assert ["Total", "1", "1", "0", "0", "0"] in [line.split() for line in lines]


def test_no_banner_when_nothing_was_registered():
    config = SimpleNamespace(stash=pytest.Stash())
    terminal = SimpleNamespace(write_sep=lambda *_: pytest.fail("unexpected banner"))
    cleanup_reporting.pytest_terminal_summary(terminal, config)
