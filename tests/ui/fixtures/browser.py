"""
Browser and environment fixtures for Playwright UI tests. (Browser Context + Page + UI environment URL)

This module owns the low-level Playwright lifecycle used by the UI test
framework.

Architecture:

    Playwright
        |
        v
    Browser
        |
        +-- Browser Context ---- function-scoped
                 |
                 +-- Page -------- function-scoped

Design principles:

    - The browser process is managed by pytest-playwright.
    - Every test receives a fresh Browser Context.
    - Every test receives a fresh Page.
    - Browser Context is the primary isolation boundary between tests.
    - Cookies, local storage, session storage, and authentication state are
      isolated between tests.
    - Tests never create or close Browser, BrowserContext, or Page objects
      themselves.
    - The active UI environment follows the project's API_ENV convention.
"""

import os
from collections.abc import Generator

import pytest
from playwright.sync_api import Browser, BrowserContext, Page

from tests.ui.config.config_ui import UI_HOSTS


@pytest.fixture
def context(browser: Browser) -> Generator[BrowserContext, None, None]:
    """
    Create an isolated Playwright Browser Context for one test.

    A Browser Context behaves like an independent browser profile. Each
    context has its own cookies, local storage, session storage, and
    authentication state.

    Creating a new context for every test prevents authentication state from
    leaking between tests. This is particularly important for UI tests that
    exercise different customer profiles or access roles.

    The Browser instance itself is provided and managed by pytest-playwright.
    This fixture owns only the lifecycle of the test-scoped Browser Context.

    Args:
        browser: Browser instance provided by pytest-playwright.

    Yields:
        BrowserContext: Isolated context available to the current test.

    """
    context = browser.new_context()

    try:
        yield context
    finally:
        context.close()


@pytest.fixture
def page(context: BrowserContext) -> Generator[Page, None, None]:
    """
    Create an isolated Playwright Page for one test.

    The page belongs to the test-scoped Browser Context created by the
    ``context`` fixture.

    Role and profile fixtures build on this generic page fixture. They should
    authenticate or configure the page but must not create their own browser
    lifecycle.

    Args:
        context: Isolated Browser Context provided by the ``context`` fixture.

    Yields:
        Page: Active Playwright page for the current test.

    """
    page = context.new_page()

    try:
        yield page
    finally:
        page.close()


@pytest.fixture(scope="session")
def ui_base_url() -> str:
    """
    Return the base URL for the active UI test environment.

    The UI framework uses the same ``API_ENV`` convention as the API test
    framework. The environment determines which storefront the Playwright
    tests exercise.

    ``API_ENV`` is intentionally resolved once per test session because the
    target environment should remain constant for the complete pytest run.

    If ``API_ENV`` is not provided, ``test`` is used as the default environment.

    Returns:
        str: Storefront base URL configured for the active environment.

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
