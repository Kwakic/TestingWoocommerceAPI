"""
Shared pytest fixtures for Playwright UI tests.

This module owns the Playwright browser lifecycle for the UI test suite.

Architecture:

    Playwright
        │
        ▼
    Browser  ─────────────── session-scoped
        │
        ├── Browser Context ── function-scoped
        │        │
        │        └── Page ──── function-scoped
        │
        └── Browser Context
                 │
                 └── Page

Design principles:
    - One browser process is reused during the pytest session.
    - Every test receives a fresh Browser Context.
    - Every test receives a fresh Page.
    - Browser Context provides session/cookie/storage isolation.
    - Tests should never manage browser lifecycle themselves.
"""

from collections.abc import Generator

import pytest
from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright


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
    # 1. Start the Playwright driver context
    with sync_playwright() as playwright:
        # 2. Launch the browser
        browser = playwright.chromium.launch(headless=False)
        try:
            # 3. Hand control over to the caller
            yield browser
        finally:
            # 4. Clean up after the caller finishes
            browser.close()


@pytest.fixture
def context(browser: Browser) -> Generator[BrowserContext, None, None]:
    """
    Create an isolated Browser Context for a single test.

    A Browser Context behaves like an independent browser profile.
    Cookies, local storage, session storage, and authentication state
    are isolated from other contexts.

    This allows different tests — and eventually different users —
    to operate independently within the same browser process.

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

    Tests should normally depend on this fixture rather than creating
    Playwright pages directly. This keeps browser lifecycle management
    outside the test and allows the fixture architecture to evolve
    without changing individual tests.

    Args:
        context: Isolated Browser Context provided by the ``context``
            fixture.

    Yields:
        Page: Active Playwright page available to the test.
    """
    page = context.new_page()

    try:
        yield page
    finally:
        page.close()
