"""
UI test for applying a WooCommerce coupon in the shopping cart.

The coupon is created as test-specific data through the existing Coupons API
fixture. The browser then exercises the customer-facing coupon workflow.

This keeps the persistent UI baseline limited to users and products while
allowing each test to own and clean up its temporary coupon.
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
    ],
    indirect=True,
)
def test_apply_coupon_to_cart(
    ui_role_page: Page,
    ui_base_url: str,
    create_valid_coupon,
) -> None:
    """
    Verify that a storefront user can apply a valid percentage coupon.

    The test uses the API only to prepare isolated coupon test data.
    The behavior under test is performed and verified entirely through the UI.
    """

    product_name = "UI Seed – Album"
    product_price = "$15.00"
    discount_amount = "-$1.50"
    discounted_total = "$13.50"

    # Arrange: Create a temporary 10% coupon and add the seeded product
    # to the shopping cart.
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

    # Assert: Verify that WooCommerce displays the applied coupon,
    # the expected 10% discount, and the recalculated cart total.
    cart_page.should_show_coupon(coupon_code)
    cart_page.should_show_discount(discount_amount)
    cart_page.should_show_total(discounted_total)
