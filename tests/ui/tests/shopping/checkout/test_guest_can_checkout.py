# """
# End-to-end UI test for completing a WooCommerce customer checkout.
#
# The scenario validates the complete customer purchase journey through the real
# storefront and checkout UI.
# """
#
# import pytest
# from playwright.sync_api import Page
#
# from tests.ui.pages.cart_page import CartPage
# from tests.ui.pages.checkout_page import CheckoutPage
# from tests.ui.pages.home_page import HomePage
# from tests.ui.pages.order_confirmation_page import OrderConfirmationPage
#
#
# pytestmark = [
#     pytest.mark.ui,
#     pytest.mark.smoke,
# ]
#
#
# def test_customer_can_complete_checkout(
#     customer_page: Page,
#     ui_base_url: str,
# ) -> None:
#     """
#     Verify that an authenticated customer can purchase a seeded product.
#
#     Flow:
#         customer
#             -> Shop
#             -> add product to cart
#             -> Cart
#             -> Checkout
#             -> fill billing details
#             -> select Cash on delivery
#             -> add order note
#             -> place order
#             -> verify order confirmation
#     """
#     product_name = "UI Seed – Album"
#     order_note = "Be smily"
#
#     # Arrange: Open the storefront using the authenticated customer context.
#     home_page = HomePage(customer_page, ui_base_url)
#     home_page.open()
#
#     # Act: Add the seeded product to the cart.
#     shop_page = home_page.open_shop()
#     product_page = shop_page.open_product(product_name)
#     product_page.should_be_loaded()
#     product_page.add_to_cart()
#
#     # Act: Open the cart from the add-to-cart confirmation.
#     cart_page = CartPage(customer_page)
#     cart_page.open_from_add_to_cart_notice()
#     cart_page.should_be_loaded()
#     cart_page.should_contain_product(product_name)
#
#     # Act: Open Checkout and complete the required checkout data.
#     checkout_page = CheckoutPage(customer_page, ui_base_url)
#     checkout_page.open()
#     checkout_page.should_be_loaded()
#     checkout_page.fill_billing_address(
#         email="ui.customer@test.com",
#         first_name="Ludovico",
#         last_name="Nuevo",
#         street_address="Pl.del Pueblo,10",
#         postal_code="28100",
#         city="Madrid",
#         phone="753357753",
#     )
#     checkout_page.select_cash_on_delivery()
#     checkout_page.add_order_note(order_note)
#
#     # Act: Place the order.
#     checkout_page.place_order()
#
#     # Assert: Verify WooCommerce created and displayed the order confirmation.
#     confirmation_page = OrderConfirmationPage(customer_page)
#     confirmation_page.should_be_loaded()
#     confirmation_page.should_contain_product(product_name)
#     confirmation_page.should_show_order_note(order_note)
