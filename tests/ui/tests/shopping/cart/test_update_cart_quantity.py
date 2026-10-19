"""UI test verifying quantity changes in the WooCommerce cart.

The product is created through the shared API fixture so the test is isolated
from persistent seeded catalog data. The fixture owns cleanup of the product.
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
def test_update_cart_quantity(
    ui_role_page: Page,
    ui_base_url: str,
    create_valid_product,
) -> None:
    """Verify that increasing and decreasing quantity updates the cart total."""

    # Arrange: Create a unique product priced at $15.00 and add it to the cart.
    suffix = uuid4().hex[:10]
    product = create_valid_product(
        name=f"UI Cart Quantity Product {suffix}",
        sku=f"ui-cart-quantity-{suffix}",
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

    cart_page = CartPage(ui_role_page)
    cart_page.open_from_add_to_cart_notice()
    cart_page.should_be_loaded()
    cart_page.should_contain_product(product_name)
    cart_page.should_show_quantity(1)
    cart_page.should_show_total("$15.00")

    # Act: Increase the quantity to two and verify the recalculated total.
    cart_page.increase_quantity(product_name)
    cart_page.should_show_quantity(2)
    cart_page.should_show_total("$30.00")

    # Act: Decrease the quantity back to one and verify the total again.
    cart_page.decrease_quantity(product_name)
    cart_page.should_show_quantity(1)
    cart_page.should_show_total("$15.00")
