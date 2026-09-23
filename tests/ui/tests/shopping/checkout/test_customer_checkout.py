"""
End-to-end UI tests for completing a WooCommerce customer checkout.

The scenarios validate the customer purchase journey through the real
storefront and checkout UI.
"""

import pytest
from playwright.sync_api import Page

from tests.ui.pages.shopping.cart_page import CartPage
from tests.ui.pages.shopping.checkout_page import CheckoutPage
from tests.ui.pages.common.home_page import HomePage
from tests.ui.pages.shopping.order_confirmation_page import OrderConfirmationPage


pytestmark = [
    pytest.mark.ui,
    pytest.mark.smoke,
]


@pytest.mark.xfail(reason="Must be changed its profile")
def test_customer_can_complete_checkout(
    customer_page: Page,
    ui_base_url: str,
) -> None:
    """
    Verify that an authenticated customer can purchase a seeded product.

    Flow:
        customer
            -> Shop
            -> add product to cart
            -> Cart
            -> Checkout
            -> verify saved billing details
            -> select Cash on delivery
            -> add order note
            -> place order
            -> verify order confirmation
    """
    product_name = "UI Seed – Album"
    order_note = "Be smily"

    # Arrange: Customer A is the stable checkout profile with a saved
    # billing address. Open the storefront using that isolated account.
    home_page = HomePage(customer_page, ui_base_url)
    home_page.open()

    # Act: Add the seeded product to the cart.
    shop_page = home_page.open_shop()
    product_page = shop_page.open_product(product_name)
    product_page.should_be_loaded()
    product_page.add_to_cart()

    # Act: Open the cart from the add-to-cart confirmation.
    cart_page = CartPage(customer_page)
    cart_page.open_from_add_to_cart_notice()
    cart_page.should_be_loaded()
    cart_page.should_contain_product(product_name)

    # Act: Open Checkout and verify Customer A's saved billing information.
    checkout_page = CheckoutPage(customer_page, ui_base_url)
    checkout_page.open()
    checkout_page.should_be_loaded()
    checkout_page.should_have_saved_billing_address(
        first_name="John",
        last_name="Beck",
        street_address="Pl.del Pueblo,10",
        postal_code="28100",
        city="Madrid",
        province="Madrid",
        country="Spain",
        phone="753357753",
    )

    # Act: Select the available payment method and add an order note.
    checkout_page.select_cash_on_delivery()
    checkout_page.add_order_note(order_note)

    # Act: Place the order.
    checkout_page.place_order()

    # Assert: Verify WooCommerce created and displayed the order confirmation.
    confirmation_page = OrderConfirmationPage(customer_page)
    confirmation_page.should_be_loaded()
    confirmation_page.should_contain_product(product_name)
    confirmation_page.should_show_order_note(order_note)


def test_customer_can_complete_checkout_with_different_shipping_address(
    customer_page: Page,
    ui_base_url: str,
) -> None:
    """
    Verify that Customer A can complete checkout with a different shipping address.

    Flow:
        customer
            -> Shop
            -> add product to cart
            -> Checkout
            -> verify saved billing details
            -> use a separate shipping address
            -> verify shipping option
            -> select Cash on delivery
            -> place order
            -> verify order confirmation
    """
    product_name = "UI Seed – Album"

    # Arrange: Customer A is the stable checkout profile with saved
    # billing and shipping data.
    home_page = HomePage(customer_page, ui_base_url)
    home_page.open()

    # Act: Add the seeded product to the cart.
    shop_page = home_page.open_shop()
    product_page = shop_page.open_product(product_name)
    product_page.should_be_loaded()
    product_page.add_to_cart()

    # Act: Open the cart and verify the seeded product is present.
    cart_page = CartPage(customer_page)
    cart_page.open_from_add_to_cart_notice()
    cart_page.should_be_loaded()
    cart_page.should_contain_product(product_name)

    # Act: Open Checkout and verify the saved billing address.
    checkout_page = CheckoutPage(customer_page, ui_base_url)
    checkout_page.open()
    checkout_page.should_be_loaded()

    # Act: Use a separate shipping address and reveal the billing address.
    checkout_page.uncheck_use_same_address_for_billing()

    # Assert: Verify Customer A's saved billing address.
    checkout_page.should_have_saved_billing_address(
        first_name="John",
        last_name="Beck",
        street_address="Pl.del Pueblo,10",
        postal_code="28100",
        city="Madrid",
        province="Madrid",
        country="Spain",
        phone="753357753",
    )

    # Act: Open the shipping address form and enter a different address.
    checkout_page.edit_shipping_address()
    checkout_page.fill_shipping_address(
        first_name="Changan",
        last_name="Beck",
        street_address="Calle Test,25",
        postal_code="28001",
        city="Madrid",
    )
    checkout_page.should_have_shipping_option()

    # Act: Select the available payment method and place the order.
    checkout_page.select_cash_on_delivery()
    checkout_page.place_order()

    # Assert: Verify WooCommerce created and displayed the order confirmation.
    confirmation_page = OrderConfirmationPage(customer_page)
    confirmation_page.should_be_loaded()
    confirmation_page.should_contain_product(product_name)
