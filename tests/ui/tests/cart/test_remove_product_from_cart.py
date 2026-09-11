"""
UI tests for removing products from the WooCommerce cart.

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
def test_remove_product_from_cart(
    ui_role_page: Page,
    ui_base_url: str,
) -> None:
    """
    Verify that the selected storefront role can remove a product from the cart.
    """

    product_name = "UI Seed – Album"

    # Arrange: Add the seeded product to the cart.
    home_page = HomePage(ui_role_page, ui_base_url)
    home_page.open()
    shop_page = home_page.open_shop()
    product_page = shop_page.open_product(product_name)

    product_page.should_be_loaded()
    product_page.add_to_cart()

    # Act: Open the cart using the same isolated role-specific page.
    cart_page = CartPage(ui_role_page)
    cart_page.open_from_add_to_cart_notice()

    # Assert: Confirm the product is initially present.
    cart_page.should_be_loaded()
    cart_page.should_contain_product(product_name)

    # Act: Remove the product from the cart.
    cart_page.remove_product(product_name)

    # Assert: Confirm that the cart is empty.
    cart_page.should_be_empty()
