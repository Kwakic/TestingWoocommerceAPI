"""
Administrator authentication fixtures for Playwright UI tests.

This module provides the authenticated page representing the WordPress
administrator access role.

Administrator credentials are supplied through environment variables and are
never hard-coded in the test suite.

Design principles:

    - Authentication is performed by the fixture, not individual tests.
    - Credentials remain outside the source code.
    - The fixture builds on the generic page and UI environment fixtures.
    - Administrator browser state remains isolated through the generic
      Browser Context fixture.
"""

import os

import pytest
from playwright.sync_api import Page

from tests.ui.pages.admin.admin_login_page import AdminLoginPage


@pytest.fixture
def admin_page(
    page: Page,
    ui_base_url: str,
) -> Page:
    """
    Provide a page authenticated as the WordPress administrator role.

    Credentials are read from:

        UI_ADMIN_USERNAME
        UI_ADMIN_PASSWORD

    The fixture owns the authentication workflow so administrator tests can
    focus on administrator behavior rather than login selectors, URLs, or
    credential management.

    Args:
        page: Fresh page belonging to the test's isolated Browser Context.
        ui_base_url: Storefront base URL for the active UI environment.

    Returns:
        Page: Authenticated WordPress administrator page.

    Raises:
        pytest.UsageError: If required administrator credentials are missing.

    """
    username = os.getenv("UI_ADMIN_USERNAME")
    password = os.getenv("UI_ADMIN_PASSWORD")

    missing_credentials = [
        name
        for name, value in (
            ("UI_ADMIN_USERNAME", username),
            ("UI_ADMIN_PASSWORD", password),
        )
        if not value
    ]

    if missing_credentials:
        raise pytest.UsageError(
            "Missing required UI admin credentials: " + ", ".join(missing_credentials)
        )

    login_page = AdminLoginPage(
        page=page,
        base_url=ui_base_url,
    )
    login_page.login(
        username=username,
        password=password,
    )

    return page
