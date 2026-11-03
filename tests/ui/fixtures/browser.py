"""UI environment fixtures.

Browser, BrowserContext, and Page lifecycles are provided by
``pytest-playwright``. Keeping those fixtures plugin-managed enables its
per-test diagnostics (including failure-only Trace Viewer output) while
preserving a fresh isolated context and page for each test.
"""

import os
import re
import shutil
from collections.abc import Callable, Generator, Iterator
from contextlib import AbstractContextManager, contextmanager
from pathlib import Path

import pytest
from playwright.sync_api import BrowserContext

from tests.ui.config.config_ui import UI_HOSTS


@pytest.fixture(scope="session")
def ui_base_url() -> str:
    """Return the storefront URL configured for the active UI environment.

    The UI framework follows the same ``API_ENV`` convention as the API test
    framework. If it is not set, the local ``test`` environment is used.

    Raises:
        ValueError: If ``API_ENV`` does not correspond to a configured UI
            environment.
    """
    environment = os.getenv("API_ENV", "test")

    try:
        return UI_HOSTS[environment]
    except KeyError as exc:
        supported_environments = ", ".join(sorted(UI_HOSTS))
        raise ValueError(
            f"Unsupported UI environment '{environment}'. "
            f"Supported environments: {supported_environments}"
        ) from exc


@pytest.fixture
def trace_custom_context(
    request: pytest.FixtureRequest,
    tmp_path: Path,
) -> Iterator[Callable[[BrowserContext, str], AbstractContextManager[None]]]:
    """Trace an explicitly managed context using pytest-playwright settings.

    Most tests should use pytest-playwright's ``context`` and ``page``
    fixtures, which are traced automatically by ``--tracing``. This helper is
    for exceptional tests that must launch their own context (for example, a
    persistent profile restart scenario). With ``retain-on-failure``, it keeps
    every recorded phase only when the complete test fails.
    """
    tracing_mode = request.config.getoption("tracing", default="off")
    output_dir = Path(request.config.getoption("output", default="test-results"))
    test_id = re.sub(r"[^A-Za-z0-9_.-]+", "_", request.node.nodeid)
    temporary_dir = tmp_path / "playwright-traces"
    temporary_traces: list[Path] = []

    @contextmanager
    def record(
        context: BrowserContext,
        phase: str,
    ) -> Generator[None, None, None]:
        if tracing_mode == "off":
            yield
            return

        temporary_dir.mkdir(parents=True, exist_ok=True)
        context.tracing.start(screenshots=True, snapshots=True, sources=True)
        trace_path = temporary_dir / f"{phase}.zip"
        try:
            yield
        except BaseException:
            context.tracing.stop(path=trace_path)
            temporary_traces.append(trace_path)
            raise
        else:
            # Keep each phase temporarily until pytest knows whether the
            # whole test passed. A later phase may fail and need both traces.
            context.tracing.stop(path=trace_path)
            temporary_traces.append(trace_path)

    yield record

    call_report = getattr(request.node, "rep_call", None)
    setup_report = getattr(request.node, "rep_setup", None)
    test_failed = bool(call_report and call_report.failed) or bool(
        setup_report and setup_report.failed
    )
    retain_traces = tracing_mode == "on" or (
        tracing_mode == "retain-on-failure" and test_failed
    )

    if retain_traces and temporary_traces:
        destination = output_dir / "custom-traces" / test_id
        destination.mkdir(parents=True, exist_ok=True)
        for trace_path in temporary_traces:
            shutil.move(str(trace_path), str(destination / trace_path.name))
