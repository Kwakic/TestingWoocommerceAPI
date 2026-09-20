"""
UI tests for verifying WooCommerce cart contents.

Role selection is handled through the indirect UI role fixture so the same
test structure can later cover multiple supported storefront roles.
"""

import pytest
from playwright.sync_api import Page

from tests.ui.pages.common.home_page import HomePage
from tests.ui.pages.shopping.cart_page import CartPage


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
def test_cart_contents(
    ui_role_page: Page,
    ui_base_url: str,
) -> None:
    """
    Verify that the cart displays the expected product, quantity, price,
    and total.
    """

    product_name = "UI Seed – Album"
    product_price = "$15.00"
    cart_total = "$15.00"

    # Arrange: Add the seeded product to the cart.
    home_page = HomePage(ui_role_page, ui_base_url)
    home_page.open()
    home_page.should_be_loaded()

    shop_page = home_page.open_shop()
    product_page = shop_page.open_product(product_name)

    product_page.should_be_loaded()
    product_page.add_to_cart()

    cart_page = CartPage(ui_role_page)
    cart_page.open_from_add_to_cart_notice()

    # Assert: Verify the expected cart contents.
    cart_page.should_be_loaded()
    cart_page.should_contain_product(product_name)
    cart_page.should_show_quantity(1)
    cart_page.should_show_price(product_price)
    cart_page.should_show_total(cart_total)
