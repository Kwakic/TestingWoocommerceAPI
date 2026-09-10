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
from playwright.sync_api import Browser, BrowserContext, Page

from tests.ui.config.config_ui import UI_HOSTS


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


@pytest.fixture
def ui_role_page(request: pytest.FixtureRequest) -> Page:
    """
    Provide the Playwright page associated with the requested UI role.

    The role is selected through pytest parametrization. Role-specific
    fixtures own authentication and session setup, while this fixture
    provides a common interface to UI tests.

    Currently supported:
        - guest

    Future roles:
        - customer
        - admin

    Returns:
        Page: Playwright page configured for the requested role.
    """
    role = request.param

    role_fixtures = {
        "guest": "guest_page",
        # "customer": "customer_page",
        # "admin": "admin_page",
    }

    try:
        fixture_name = role_fixtures[role]
    except KeyError as exc:
        supported_roles = ", ".join(role_fixtures)
        raise ValueError(
            f"Unsupported UI role '{role}'. " f"Supported roles: {supported_roles}"
        ) from exc

    return request.getfixturevalue(fixture_name)


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


"""
The bug isn't in the test file — it's in ui_role_page inside conftest.py.

🔍 The exact culprit
python
@pytest.fixture
def ui_role_page(request: pytest.FixtureRequest) -> Page:
    role = request.param
    role_fixtures = {"guest": "guest_page"}
    fixture_name = role_fixtures[role]
    return request.getfixturevalue(fixture_name)

👉 ui_role_page only declares request as a parameter.

👉 It pulls in guest_page dynamically via request.getfixturevalue(...), not as a function parameter.

🧠 Why that breaks browser parametrization

🎯 pytest builds its fixture dependency graph by scanning declared function parameters only — recursively, at collection time.

🎯 request.getfixturevalue() runs inside the fixture body, at runtime — pytest's collector never sees it.

🎯 So for any test using ui_role_page, the chain guest_page → page → context → browser → browser_type → browser_name is completely invisible to metafunc.fixturenames.

🎯 pytest-playwright's pytest_generate_tests hook checks exactly that list to decide whether to parametrize browser_name — since it's missing, the hook skips it, and pytest falls back to calling the real browser_name fixture function... which is the one that emits the warning.

⚠️ This is bigger than a noisy warning

📌 Since browser_name never gets parametrized, your test does not run once per browser.

📌 It silently runs only once, using browsers[0] (whatever's first in your --browser list) — any additional --browser values are quietly ignored for every test going through ui_role_page.

📌 So if you ever run --browser chromium --browser firefox, you're not getting Firefox coverage on this test, even though it looks like you configured it.

✅ The fix

Add browser_name as an explicit (unused) parameter — this exposes the dependency chain to pytest's collector without changing any behavior:

python
@pytest.fixture
def ui_role_page(
    request: pytest.FixtureRequest,
    browser_name: str,  # 👈 makes the browser chain visible to pytest_generate_tests
) -> Page:
    role = request.param

    role_fixtures = {
        "guest": "guest_page",
        # "customer": "customer_page",
        # "admin": "admin_page",
    }

    try:
        fixture_name = role_fixtures[role]
    except KeyError as exc:
        supported_roles = ", ".join(role_fixtures)
        raise ValueError(
            f"Unsupported UI role '{role}'. Supported roles: {supported_roles}"
        ) from exc

    return request.getfixturevalue(fixture_name)

✅ browser_name is cheap (session-scoped string) — adding it here doesn't create extra browsers/contexts.

✅ Once this is in place, pytest_generate_tests sees browser_name normally → multi-browser parametrization works → the warning disappears on its own.

🧩 One more thing to check

📁 I checked pytest.ini and pyproject.toml — neither sets --browser in addopts.

📁 So the multiple --browser flags causing this must come from how you invoked pytest that run — CLI command, CI workflow, or a Makefile.

👉 Worth double-checking that spot too, so you know exactly which browsers you're actually meant to be covering.

"""
