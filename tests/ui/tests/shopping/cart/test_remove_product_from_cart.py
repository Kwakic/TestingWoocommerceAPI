"""UI test verifying that a product can be removed from the WooCommerce cart.

The product is provisioned through the shared API fixture, avoiding reliance on
persistent seeded catalog data. The fixture owns cleanup of the temporary product.
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
        pytest.param("guest", id="guest"),
    ],
    indirect=True,
)
def test_remove_product_from_cart(
    ui_role_page: Page,
    ui_base_url: str,
    create_valid_product,
) -> None:
    """Verify that a guest can remove a product and leave the cart empty."""

    # Arrange: Create a unique product and add it to the cart.
    suffix = uuid4().hex[:10]
    product = create_valid_product(
        name=f"UI Remove Cart Product {suffix}",
        sku=f"ui-remove-cart-{suffix}",
        regular_price="15.00",
    )
    product_name = product["name"]

    home_page = HomePage(ui_role_page, ui_base_url)
    home_page.open()
    home_page.should_be_loaded()

    shop_page = home_page.open_shop()
    product_page = shop_page.open_product(product_name)
    product_page.should_be_loaded()
    product_page.add_to_cart()

    # Act: Open the cart and confirm the product was added.
    cart_page = CartPage(ui_role_page)
    cart_page.open_from_add_to_cart_notice()
    cart_page.should_be_loaded()
    cart_page.should_contain_product(product_name)

    # Act: Remove the product from the cart.
    cart_page.remove_product(product_name)

    # Assert: The cart is empty after removal.
    cart_page.should_be_empty()
