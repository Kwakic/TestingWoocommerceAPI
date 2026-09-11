"""
UI tests for the WooCommerce storefront home page.

These scenarios currently validate guest access. The indirect role fixture is
used consistently so additional supported roles can be enabled at the test
boundary without changing the test implementation.
"""

import pytest
from playwright.sync_api import Page

from tests.ui.pages.home_page import HomePage


pytestmark = [
    pytest.mark.ui,
    pytest.mark.smoke,
]


@pytest.mark.parametrize(
    "ui_role_page",
    [
        pytest.param("guest", id="guest"),
        # pytest.param("customer", id="customer"),
        # pytest.param("admin", id="admin"),
    ],
    indirect=True,
)
def test_home_page_loads(
    ui_role_page: Page,
    ui_base_url: str,
) -> None:
    """
    Verify that the selected storefront role can access the home page.

    The role is supplied through the indirect ``ui_role_page`` fixture so
    browser/session lifecycle and authentication remain outside the test.
    """

    # Arrange: Build the Home Page Object using the role-specific Playwright page.
    home_page = HomePage(ui_role_page, ui_base_url)

    # Act: Navigate to the storefront home page.
    home_page.open()

    # Assert: Verify that the storefront home page is displayed.
    home_page.should_be_loaded()


@pytest.mark.parametrize(
    "ui_role_page",
    [
        pytest.param("guest", id="guest"),
        # pytest.param("customer", id="customer"),
        # pytest.param("admin", id="admin"),
    ],
    indirect=True,
)
def test_guest_can_navigate_to_shop(
    ui_role_page: Page,
    ui_base_url: str,
) -> None:
    """
    Verify that the selected storefront role can navigate to the Shop page.

    The current scenario is named for the guest use case because guest access
    is the only enabled role in this test matrix at present.
    """

    # Arrange: Start from the storefront home page.
    home_page = HomePage(ui_role_page, ui_base_url)

    # Act: Open the home page and navigate to the Shop page.
    home_page.open()
    shop_page = home_page.open_shop()

    # Assert: Verify that the Shop page is displayed.
    shop_page.should_be_loaded()
