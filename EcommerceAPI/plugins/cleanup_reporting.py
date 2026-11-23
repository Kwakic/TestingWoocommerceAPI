"""Consolidate fixture cleanup results in the pytest controller."""

import os
from collections import Counter, defaultdict
from dataclasses import dataclass, field

import pytest


@dataclass
class EntityCleanup:
    registered: set[str] = field(default_factory=set)
    outcomes: Counter[str] = field(default_factory=Counter)


_TOTALS = pytest.StashKey[defaultdict[str, EntityCleanup]]()
_WORKERS = pytest.StashKey[dict[str, bool]]()
_WORKER_OUTPUT = "ecommerce_cleanup"
_COLUMNS = ("deleted", "missing", "failed", "skipped")


@pytest.fixture(scope="session")
def cleanup_totals(pytestconfig):
    """Reporting state only. Ownership and DELETEs stay in the existing fixtures."""
    return pytestconfig.stash.setdefault(_TOTALS, defaultdict(EntityCleanup))


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session):
    # xdist sends workeroutput after session finalizers have finished.
    output = getattr(session.config, "workeroutput", None)
    if output is not None:
        output[_WORKER_OUTPUT] = {
            entity: (sorted(result.registered), dict(result.outcomes))
            for entity, result in session.config.stash.get(_TOTALS, {}).items()
        }


@pytest.hookimpl(optionalhook=True)
def pytest_testnodedown(node, error):
    workers = node.config.stash.setdefault(_WORKERS, {})
    worker = node.gateway.id
    if workers.get(worker):
        return  # xdist can notify twice for an interrupted worker.
    report = getattr(node, "workeroutput", {}).get(_WORKER_OUTPUT)
    workers[worker] = report is not None
    if report is None:
        return

    totals = node.config.stash.setdefault(_TOTALS, defaultdict(EntityCleanup))
    for entity, (registered, outcomes) in report.items():
        totals[entity].registered.update(registered)
        totals[entity].outcomes.update(outcomes)


def pytest_terminal_summary(terminalreporter, config):
    if hasattr(config, "workerinput"):
        return
    totals = config.stash.get(_TOTALS, {})
    workers = config.stash.get(_WORKERS, {})
    missing_workers = sorted(
        worker for worker, reported in workers.items() if not reported
    )
    if not totals and not missing_workers:
        return

    terminalreporter.write_sep("=", "🧹 SESSION CLEANUP SUMMARY")
    context = [f"Workers: {len(workers) or 1}"]
    if profile := os.environ.get("API_ENV"):
        context.append(f"API_ENV={profile}")
        if profile == "docker" and (mode := os.environ.get("DOCKER_INFRA")):
            context.append(f"DOCKER_INFRA={mode}")
    terminalreporter.write_line(" | ".join(context))
    if missing_workers:
        terminalreporter.write_line(
            "Partial totals. No cleanup report from: " + ", ".join(missing_workers)
        )
    if not totals:
        return

    terminalreporter.write_line(
        "Registered counts unique IDs. Outcomes count fixture actions."
    )
    entity_width = max(len("Entity"), max(map(len, totals)))
    row = f"{{:<{entity_width}}}  {{:>10}}  {{:>7}}  {{:>7}}  {{:>6}}  {{:>7}}"
    terminalreporter.write_line(
        row.format("Entity", "Registered", *(c.title() for c in _COLUMNS))
    )
    overall = Counter()
    for entity, result in sorted(totals.items()):
        terminalreporter.write_line(
            row.format(
                entity, len(result.registered), *(result.outcomes[c] for c in _COLUMNS)
            )
        )
        overall["registered"] += len(result.registered)
        overall.update(result.outcomes)
    terminalreporter.write_line(
        row.format("Total", overall["registered"], *(overall[c] for c in _COLUMNS))
    )
