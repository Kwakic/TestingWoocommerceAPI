"""UI tests for adding a product to the WooCommerce cart.

Each test invocation provisions its own product through the shared API fixture,
so browser-parametrized runs do not depend on or mutate a shared seeded product.
"""

from collections.abc import Callable
from uuid import uuid4

import pytest
from playwright.sync_api import Page

from tests.ui.pages.common.home_page import HomePage
from tests.ui.pages.shopping.cart_page import CartPage


pytestmark = [pytest.mark.ui, pytest.mark.smoke]


@pytest.mark.parametrize(
    "ui_role_page",
    [pytest.param("guest", id="guest")],
    indirect=True,
)
def test_add_product_to_cart(
    ui_role_page: Page,
    ui_base_url: str,
    create_valid_product: Callable[..., dict],
) -> None:
    """Verify that a guest can add a newly provisioned product to the cart."""
    # Arrange: Create an isolated product for this test invocation.
    suffix = uuid4().hex[:10]
    product = create_valid_product(
        name=f"UI Cart Product {suffix}",
        sku=f"ui-cart-{suffix}",
        regular_price="15.00",
    )
    product_name = product["name"]
    product_price = "$15.00"

    # Arrange: Navigate to the newly created product through the storefront.
    home_page = HomePage(ui_role_page, ui_base_url)
    home_page.open()
    home_page.should_be_loaded()

    shop_page = home_page.open_shop()
    product_page = shop_page.open_product(product_name)
    product_page.should_be_loaded()

    # Act: Add the product to the cart and open the cart page.
    product_page.add_to_cart()
    cart_page = CartPage(ui_role_page)
    cart_page.open_from_add_to_cart_notice()

    # Assert: The cart displays the created product and its expected price.
    cart_page.should_be_loaded()
    cart_page.should_contain_product(product_name)
    cart_page.should_show_price(product_price)
