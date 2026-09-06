import pytest
from playwright.sync_api import Page

from tests.ui.pages.cart_page import CartPage
from tests.ui.pages.home_page import HomePage


pytestmark = [
    pytest.mark.ui,
    # pytest.mark.smoke,
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
def test_add_product_to_cart(
    ui_role_page: Page,
    ui_base_url: str,
) -> None:
    """Verify that a storefront user can add a product to the cart."""

    product_name = "UI Seed – Album"
    product_price = "$15.00"

    home_page = HomePage(ui_role_page, ui_base_url)
    home_page.open()

    shop_page = home_page.open_shop()
    product_page = shop_page.open_product(product_name)

    product_page.should_be_loaded()
    product_page.add_to_cart()

    cart_page = CartPage(ui_role_page)
    cart_page.open_from_add_to_cart_notice()
    cart_page.should_be_loaded()
    cart_page.should_contain_product(product_name)
    cart_page.should_show_price(product_price)
