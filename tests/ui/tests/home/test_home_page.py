"""UI tests for home-page access and storefront navigation.

Guest scenarios use an unauthenticated page. Customer navigation provisions a
disposable API-created customer rather than relying on a seeded customer.
"""

import pytest
from playwright.sync_api import Page

from tests.ui.data.models.customer_model import DynamicCustomer
from tests.ui.fixtures.customer_auth import login_customer
from tests.ui.pages.common.home_page import HomePage


pytestmark = [pytest.mark.ui, pytest.mark.smoke]


def test_home_page_loads(guest_page: Page, ui_base_url: str) -> None:
    """Verify that a guest can access the storefront home page."""
    home_page = HomePage(guest_page, ui_base_url)
    home_page.open()
    home_page.should_be_loaded()


def test_guest_can_navigate_to_shop(
    guest_page: Page,
    ui_base_url: str,
) -> None:
    """Verify that a guest can navigate from the home page to Shop."""
    home_page = HomePage(guest_page, ui_base_url)
    home_page.open()
    shop_page = home_page.open_shop()
    shop_page.should_be_loaded()


def test_customer_can_navigate_to_shop(
    page: Page,
    ui_base_url: str,
    dynamic_customer: DynamicCustomer,
) -> None:
    """Verify that a disposable API-provisioned customer can navigate to Shop."""
    login_customer(
        page=page,
        ui_base_url=ui_base_url,
        username=dynamic_customer.username,
        password=dynamic_customer.password,
    )
    home_page = HomePage(page, ui_base_url)
    home_page.open()
    shop_page = home_page.open_shop()
    shop_page.should_be_loaded()
