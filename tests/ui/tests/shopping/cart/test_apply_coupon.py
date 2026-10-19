"""UI test for applying a WooCommerce percentage coupon in the cart.

The test provisions a unique product and coupon through shared API fixtures,
then verifies the coupon workflow through the storefront UI. Each invocation
owns its temporary data so browser-parametrized runs remain isolated.
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
def test_apply_coupon_to_cart(
    ui_role_page: Page,
    ui_base_url: str,
    create_valid_coupon,
    create_valid_product,
) -> None:
    """
    Verify that a storefront guest can apply a valid percentage coupon.

    API fixtures provision isolated product and coupon data. Adding the product
    to the cart and applying the coupon are exercised through the storefront UI.
    """

    # Arrange: Provision a unique product priced at $15.00 and a 10% coupon.
    suffix = uuid4().hex[:10]
    product = create_valid_product(
        name=f"UI Coupon Product {suffix}",
        sku=f"ui-coupon-{suffix}",
        regular_price="15.00",
    )
    product_name = product["name"]
    product_price = "$15.00"
    discount_amount = "-$1.50"
    discounted_total = "$13.50"

    coupon = create_valid_coupon(
        discount_type="percent",
        amount="10",
    )
    coupon_code = coupon["code"]

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

    # Act: Apply the temporary coupon through the customer-facing cart UI.
    cart_page.add_coupon(coupon_code)

    # Assert: Verify the coupon, 10% discount, and recalculated cart total.
    cart_page.should_show_coupon(coupon_code)
    cart_page.should_show_discount(discount_amount)
    cart_page.should_show_total(discounted_total)
