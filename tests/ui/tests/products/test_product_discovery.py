import pytest

from playwright.sync_api import Page

from tests.ui.pages.home_page import HomePage

pytestmark = [
    pytest.mark.ui,
    # pytest.mark.smoke,
]


def test_guest_can_open_product(
    guest_page: Page,
    ui_base_url: str,
) -> None:
    """Verify that a guest can open a product from the Shop page."""

    home_page = HomePage(guest_page, ui_base_url)

    home_page.open()
    shop_page = home_page.open_shop()

    shop_page.should_be_loaded()

    product_page = shop_page.open_product("UI Seed – Album")
    product_page.should_be_loaded()
    product_page.add_to_cart()
    product_page.should_show_price("$15.00")
    product_page.should_show_sku("ui-seed-album")
    product_page.should_show_category("Uncategorized")
    product_page.should_show_related_products()
