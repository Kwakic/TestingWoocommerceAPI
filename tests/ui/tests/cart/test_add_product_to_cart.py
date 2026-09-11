"""
UI tests for adding products to the WooCommerce cart.

Role selection is handled through the indirect UI role fixture so the same
test structure can later cover multiple supported storefront roles.
"""

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
    """
    Verify that the selected storefront role can add a product to the cart.

    The Playwright Page is role-specific and is passed between Page Objects.
    Page Objects therefore continue to operate on the same isolated browser
    context throughout the scenario.
    """

    product_name = "UI Seed – Album"
    product_price = "$15.00"

    # Arrange: Navigate to the seeded product.
    home_page = HomePage(ui_role_page, ui_base_url)
    home_page.open()
    shop_page = home_page.open_shop()
    product_page = shop_page.open_product(product_name)

    product_page.should_be_loaded()

    # Act: Add the product to the cart.
    product_page.add_to_cart()

    # Act: Continue using the same role-specific Page Object context to open
    # the cart from the storefront confirmation.
    cart_page = CartPage(ui_role_page)
    cart_page.open_from_add_to_cart_notice()

    # Assert: Verify that the expected product and price are present in the cart.
    cart_page.should_be_loaded()
    cart_page.should_contain_product(product_name)
    cart_page.should_show_price(product_price)
