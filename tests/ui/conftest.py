"""
Shared pytest fixtures for Playwright UI tests.

This module owns the browser lifecycle and provides role-oriented fixtures
for the UI test suite.

Architecture:

    Playwright
        |
        v
    Browser  --------------- session-scoped
        |
        +-- Browser Context ---- function-scoped
                 |
                 +-- Page -------- function-scoped
                         |
                         +-- guest_page
                         +-- customer_page

Design principles:
    - One browser process is reused during the pytest session.
    - Every test receives a fresh Browser Context.
    - Every test receives a fresh Page.
    - Browser Context provides session/cookie/storage isolation.
    - Role-specific fixtures build on the generic page fixture.
    - Authentication details belong in role fixtures, not individual tests.
    - Tests should not manage browser lifecycle themselves.
    - The role router keeps role selection separate from authentication
      implementation.
"""

import os
from collections.abc import Generator

import pytest
from playwright.sync_api import Browser, BrowserContext, Page

from tests.ui.config.config_ui import UI_HOSTS
from tests.ui.pages.customer_login_page import CustomerLoginPage


# ---------------------------------------------------------------------------
# UI role registry
# ---------------------------------------------------------------------------
#
# The role router intentionally contains only implemented roles.
# A role must have a real fixture before it is exposed to parametrized tests.
#
# Keeping the mapping explicit prevents tests from coupling themselves to
# authentication fixture names and gives the framework one controlled place
# to define supported UI roles.
# ---------------------------------------------------------------------------

UI_ROLE_FIXTURES = {
    "guest": "guest_page",
    "customer": "customer_page",
}


@pytest.fixture
def context(browser: Browser) -> Generator[BrowserContext, None, None]:
    """
    Create an isolated Browser Context for a single test.

    A Browser Context behaves like an independent browser profile.
    Cookies, local storage, session storage, and authentication state are
    isolated from other contexts.

    The context is the primary isolation boundary between tests and user
    roles. Authentication performed inside one context must never leak into
    another test.

    Args:
        browser: Browser instance provided by pytest-playwright.

    Yields:
        BrowserContext: Isolated browser context available to the test.
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

    This is the generic low-level page fixture. Role-specific fixtures such
    as ``guest_page`` and ``customer_page`` build on top of this fixture
    rather than creating their own browser or context lifecycle.

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

    The active environment is selected using the same ``API_ENV`` convention
    used by the API framework.

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

    Guest tests intentionally use the fresh page and isolated browser context
    supplied by the generic fixtures. No authentication state is applied.

    Args:
        page: Fresh page provided by the generic ``page`` fixture.

    Returns:
        Page: Page representing a guest storefront session.
    """
    return page


@pytest.fixture
def customer_page(page: Page, ui_base_url: str) -> Page:
    """
    Provide a page authenticated as the dedicated WooCommerce UI customer.

    Authentication is performed during fixture setup for each test that
    requests the customer role. Credentials are read from the process
    environment and are never hard-coded in the repository.

    This fixture deliberately owns the authentication workflow. Tests should
    consume ``customer_page`` and focus on customer behavior rather than
    auth selectors, URLs, or credential handling.

    Required environment variables:
        UI_CUSTOMER_USERNAME:
            Username of the dedicated UI customer used for authentication.

        UI_CUSTOMER_PASSWORD:
            Password of the dedicated UI customer used for authentication.

    Optional customer identity:
        UI_CUSTOMER_EMAIL:
            Email address of the dedicated UI customer. This is not required
            by the authentication fixture because WooCommerce accepts either
            username or email in the login field. It may be used by individual
            customer scenarios that need to verify the authenticated identity.

    Args:
        page: Fresh page belonging to the test's isolated browser context.
        ui_base_url: Storefront base URL for the active environment.

    Returns:
        Page: Page representing an authenticated customer session.

    Raises:
        pytest.UsageError: If required customer credentials are missing.
    """
    username = os.getenv("UI_CUSTOMER_USERNAME")
    password = os.getenv("UI_CUSTOMER_PASSWORD")

    missing_credentials = [
        name
        for name, value in (
            ("UI_CUSTOMER_USERNAME", username),
            ("UI_CUSTOMER_PASSWORD", password),
        )
        if not value
    ]

    if missing_credentials:
        raise pytest.UsageError(
            "Missing required UI customer credentials: "
            + ", ".join(missing_credentials)
        )

    login_page = CustomerLoginPage(page=page, base_url=ui_base_url)
    login_page.login(username=username, password=password)

    return page


@pytest.fixture
def ui_role_page(
    request: pytest.FixtureRequest,
    browser_name: str,
) -> Page:
    """
    Provide the Playwright page associated with the requested UI role.

    Role selection is performed through indirect pytest parametrization.

    ``browser_name`` is intentionally declared even though this fixture does
    not use its value. pytest-playwright inspects declared fixture
    dependencies during collection to determine whether tests require browser
    parametrization. Keeping the browser fixture visible here ensures that
    tests using the dynamic role router participate correctly in multi-browser
    execution.

    Supported roles:
        - guest
        - customer

    Args:
        request: Pytest fixture request containing the parametrized role.
        browser_name: Browser name supplied by pytest-playwright. Declared
            explicitly so browser parametrization remains visible at
            collection time.

    Returns:
        Page: Playwright page configured for the requested role.

    Raises:
        ValueError: If the requested role is not supported.
    """

    # The fixture dependency is intentionally declared for pytest-playwright's
    # collection-time browser parametrization.The value itself is not needed
    # by the role router.
    _ = browser_name

    role = request.param

    try:
        fixture_name = UI_ROLE_FIXTURES[role]
    except KeyError as exc:
        supported_roles = ", ".join(sorted(UI_ROLE_FIXTURES))
        raise ValueError(
            f"Unsupported UI role '{role}'. Supported roles: {supported_roles}"
        ) from exc

    return request.getfixturevalue(fixture_name)
