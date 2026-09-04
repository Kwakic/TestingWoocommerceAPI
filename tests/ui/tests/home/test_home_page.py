"""
UI smoke tests for the WooCommerce storefront home page.
"""

import pytest
from playwright.sync_api import Page

from tests.ui.pages.home_page import HomePage

pytestmark = [
    pytest.mark.ui,
    pytest.mark.smoke,
]


def test_home_page_loads(
    guest_page: Page,
    ui_base_url: str,
) -> None:
    """
    Verify that a guest can access the WooCommerce storefront home page.

    The test uses the explicit ``guest_page`` role fixture so that the
    business role is visible at the test boundary while browser lifecycle
    and session isolation remain managed by the fixture layer.
    """

    # Arrange: Navigate to the WooCommerce storefront as an unauthenticated user.
    home_page = HomePage(guest_page, ui_base_url)

    # Act: Locate the Test Shop link exposed in the page banner.
    home_page.open()

    # Assert: Verify that the storefront exposes the expected navigation entry.
    home_page.should_be_loaded()


def test_guest_can_navigate_to_shop(
    guest_page: Page,
    ui_base_url: str,
) -> None:
    """
    Verify that a guest can navigate from the storefront home page
    to the Shop page.
    """

    # Arrange: Navigate to the WooCommerce storefront as an unauthenticated user.
    home_page = HomePage(guest_page, ui_base_url)

    # Act: Locate the Test Shop link exposed in the page banner
    home_page.open()
    # Act: Navigate from the home page to the Shop page
    shop_page = home_page.open_shop()

    # Assert: Verify that the storefront exposes the expected navigation entry.
    shop_page.should_be_loaded()
