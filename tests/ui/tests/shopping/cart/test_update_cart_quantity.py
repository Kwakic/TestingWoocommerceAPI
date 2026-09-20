"""
UI tests for updating product quantity in the WooCommerce cart.

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
def test_update_cart_quantity(
    ui_role_page: Page,
    ui_base_url: str,
) -> None:
    """
    Verify that the selected storefront role can update cart quantity.
    """

    product_name = "UI Seed – Album"

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

    cart_page.should_be_loaded()
    cart_page.should_contain_product(product_name)
    cart_page.should_show_quantity(1)

    # Act: Increase the product quantity.
    cart_page.increase_quantity()

    # Assert: Verify that the quantity and cart total are updated.
    cart_page.should_show_quantity(2)
    cart_page.should_show_total("$30.00")

    # Act: Decrease the product quantity.
    cart_page.decrease_quantity()

    # Assert: Verify that the quantity and cart total return to the original values.
    cart_page.should_show_quantity(1)
    cart_page.should_show_total("$15.00")
