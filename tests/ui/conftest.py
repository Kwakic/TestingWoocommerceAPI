"""
Shared pytest fixtures for Playwright UI tests.

This module owns the browser lifecycle and provides role-oriented fixtures
for the UI test suite.

Architecture:

    Playwright
        │
        ▼
    Browser  ─────────────── session-scoped
        │
        └── Browser Context ── function-scoped
                 │
                 └── Page ──── function-scoped
                         │
                         ├── guest_page
                         └── customer_page (future)

Design principles:
    - One browser process is reused during the pytest session.
    - Every test receives a fresh Browser Context.
    - Every test receives a fresh Page.
    - Browser Context provides session/cookie/storage isolation.
    - Role-specific fixtures build on the generic page fixture.
    - Tests should not manage browser lifecycle themselves.
    - Authentication details belong in role fixtures, not individual tests.
"""

import pytest
import os

from collections.abc import Generator
from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

from tests.ui.config.config_ui import UI_HOSTS


@pytest.fixture(scope="session")
def browser() -> Generator[Browser, None, None]:
    """
    Start and manage the Playwright browser for the test session.

    The browser is created once and reused by all UI tests in the
    pytest session. Individual tests receive isolated Browser Contexts
    rather than launching a new browser process for every test.

    Yields:
        Browser: Active browser instance available to dependent fixtures.
    """
    # Start the Playwright driver and launch the browser once per session.
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)

        try:
            yield browser
        finally:
            browser.close()


@pytest.fixture
def context(browser: Browser) -> Generator[BrowserContext, None, None]:
    """
    Create an isolated Browser Context for a single test.

    A Browser Context behaves like an independent browser profile.
    Cookies, local storage, session storage, and authentication state
    are isolated from other contexts.

    This is the isolation boundary between different tests and,
    eventually, different user roles.

    Args:
        browser: Browser instance provided by the session-scoped
            ``browser`` fixture.

    Yields:
        BrowserContext: Isolated context available to the test.
    """
    context = browser.new_context()

    try:
        yield context
    finally:
        context.close()


@pytest.fixture
def page(context: BrowserContext) -> Generator[Page, None, None]:
    """
    Create a new browser page for a single test.

    The page belongs to the test's isolated Browser Context.

    This is the generic low-level page fixture. Role-specific fixtures
    such as ``guest_page`` and ``customer_page`` should build on top of
    this fixture rather than creating their own browser lifecycle.

    Args:
        context: Isolated Browser Context provided by the generic fixture.

    Yields:
        Page: Active Playwright page available to the test.
    """
    page = context.new_page()

    try:
        yield page
    finally:
        page.close()


@pytest.fixture(scope="session")
def ui_base_url() -> str:
    """
    Return the storefront base URL for the current UI test session.

    The active environment is selected using the same ``API_ENV``
    convention used by the API framework.

    Returns:
        str: Base URL of the WooCommerce storefront.
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
def guest_page(page: Page) -> Page:
    """
    Provide a page representing an unauthenticated storefront user.

    Guest tests intentionally use a fresh page and isolated browser context.
    No authentication state is applied.

    Args:
        page: Fresh page provided by the generic ``page`` fixture.

    Returns:
        Page: Page representing a guest storefront session.
    """
    return page


# ---------------------------------------------------------------------------
# Future authenticated roles
# ---------------------------------------------------------------------------
#
# Customer authentication should be implemented here once the login flow
# and dedicated test-account strategy are established. Tests should not
# contain username/password handling or login selectors.
#
# @pytest.fixture
# def customer_page(page: Page) -> Generator[Page, None, None]:
#     """
#     Provide a page authenticated as a WooCommerce customer.
#
#     The fixture will own the customer login/session setup so that tests
#     can focus on customer behavior rather than authentication mechanics.
#     """
#     # TODO: Authenticate using the dedicated customer test account.
#     yield page
#
#
# Admin role is intentionally kept as a reminder for future multi-role
# end-to-end scenarios (for example: API creates product → Admin UI
# verifies product → Storefront customer purchases product).
#
# @pytest.fixture
# def admin_page(page: Page) -> Generator[Page, None, None]:
#     """
#     Provide a page authenticated as a WooCommerce/WordPress administrator.
#
#     This role is reserved for future administrative UI and cross-role
#     end-to-end scenarios.
#     """
#     # TODO: Implement administrator authentication when admin UI coverage
#     # becomes part of the framework.
#     yield page
