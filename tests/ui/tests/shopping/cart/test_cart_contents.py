"""UI test verifying the contents of the WooCommerce shopping cart.

The product is created through the shared API fixture so the test does not
depend on persistent seeded catalog data. The fixture owns product cleanup.
"""

from uuid import uuid4

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
        # This test exercises guest cart behavior, so route to the unauthenticated
        # guest_page fixture. No customer account is created or logged in.
        pytest.param("guest", id="guest"),
    ],
    indirect=True,
)
def test_cart_contents(
    ui_role_page: Page,
    ui_base_url: str,
    create_valid_product,
) -> None:
    """Verify the cart's product, quantity, unit price, and total."""

    # Arrange: Create an isolated product priced at $15.00 for this test run.
    suffix = uuid4().hex[:10]
    product = create_valid_product(
        name=f"UI Cart Contents Product {suffix}",
        sku=f"ui-cart-contents-{suffix}",
        regular_price="15.00",
    )
    product_name = product["name"]
    product_price = "$15.00"
    cart_total = "$15.00"

    home_page = HomePage(ui_role_page, ui_base_url)
    home_page.open()
    home_page.should_be_loaded()

    shop_page = home_page.open_shop()
    product_page = shop_page.open_product(product_name)
    product_page.should_be_loaded()
    product_page.add_to_cart()

    cart_page = CartPage(ui_role_page)
    cart_page.open_from_add_to_cart_notice()

    # Assert: Verify the product, quantity, unit price, and cart total.
    cart_page.should_be_loaded()
    cart_page.should_contain_product(product_name)
    cart_page.should_show_quantity(1)
    cart_page.should_show_price(product_price)
    cart_page.should_show_total(cart_total)
