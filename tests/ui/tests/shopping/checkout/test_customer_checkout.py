"""
End-to-end UI tests for completing a WooCommerce customer checkout.

The scenarios validate the customer purchase journey through the real
storefront and checkout UI. Products are created dynamically through the
shared API fixture so each test owns an independent product, while customer
fixtures provide the saved-address profiles required by each scenario.
"""

from uuid import uuid4

import pytest

from playwright.sync_api import Page

from tests.ui.data.checkout_address import MADRID_ADDRESS
from tests.ui.fixtures.customer_auth import login_customer
from tests.ui.pages.common.home_page import HomePage
from tests.ui.pages.shopping.cart_page import CartPage
from tests.ui.pages.shopping.checkout_page import CheckoutPage
from tests.ui.pages.shopping.order_confirmation_page import OrderConfirmationPage


pytestmark = [
    pytest.mark.ui,
    pytest.mark.smoke,
    pytest.mark.pr,
]


def test_customer_can_complete_checkout(
    page: Page,
    ui_base_url: str,
    dynamic_customer_factory,
    create_valid_product,
) -> None:
    """
    Verify that an authenticated customer can purchase a dynamically created product.

    Flow:
        isolated customer with saved billing and shipping addresses
            -> Shop
            -> add dynamically created product to cart
            -> Cart
            -> Checkout
            -> verify saved billing details
            -> add order note
            -> place order
            -> verify order confirmation
    """
    # Create a dedicated account because WooCommerce stores a logged-in
    # customer's cart on the server. MADRID_ADDRESS is a frozen preset, and
    # its methods return new API payloads for this customer's initial state.
    customer = dynamic_customer_factory(
        billing=MADRID_ADDRESS.as_billing(),
        shipping=MADRID_ADDRESS.as_shipping(),
    )

    # Authenticate with the disposable customer so this test owns its
    # account, cart, checkout state, and order.
    customer_page = login_customer(
        page=page,
        ui_base_url=ui_base_url,
        username=customer.username,
        password=customer.password,
    )

    # Provision a product unique to this test run.
    product_suffix = uuid4().hex[:8]
    product = create_valid_product(
        name=f"UI Checkout Product {product_suffix}",
        sku=f"ui-checkout-{product_suffix}",
        regular_price="15.00",
    )
    product_name = product["name"]
    order_note = "Be smily"

    # Act: Open the storefront as the isolated customer.
    home_page = HomePage(customer_page, ui_base_url)
    home_page.open()

    # Act: Navigate to the Shop and add the dynamically created product to the cart.
    shop_page = home_page.open_shop()
    product_page = shop_page.open_product(product_name)
    product_page.should_be_loaded()
    product_page.add_to_cart()

    # Act: Open the cart from the add-to-cart confirmation and verify the product.
    cart_page = CartPage(customer_page)
    cart_page.open_from_add_to_cart_notice()
    cart_page.should_be_loaded()
    cart_page.should_contain_product(product_name)

    # Act: Open Checkout and verify the customer's saved billing information.
    checkout_page = CheckoutPage(customer_page, ui_base_url)
    checkout_page.open()
    checkout_page.should_be_loaded()
    checkout_page.should_have_saved_billing_address(
        first_name=MADRID_ADDRESS.first_name,
        last_name=MADRID_ADDRESS.last_name,
        street_address=MADRID_ADDRESS.street_address,
        postal_code=MADRID_ADDRESS.postal_code,
        city=MADRID_ADDRESS.city,
        province=MADRID_ADDRESS.province,
        country=MADRID_ADDRESS.country,
        phone=MADRID_ADDRESS.phone,
    )

    # Act: Add an order note before placing the order.
    checkout_page.add_order_note(order_note)

    checkout_page.place_order()

    # Assert: Verify WooCommerce created and displayed the order confirmation.
    confirmation_page = OrderConfirmationPage(customer_page)
    confirmation_page.should_be_loaded()
    confirmation_page.should_contain_product(product_name)
    confirmation_page.should_show_order_note(order_note)


def test_customer_can_complete_checkout_with_different_shipping_address(
    page: Page,
    ui_base_url: str,
    dynamic_customer_factory,
    create_valid_product,
) -> None:
    """
    Verify that a dynamically provisioned customer can complete checkout
    with a different shipping address.

    The customer is created for this test execution with its own saved billing
    and shipping addresses, avoiding reuse of a shared seeded checkout account.

    Flow:
        dynamically created customer with saved billing and shipping data
            -> Shop
            -> add dynamically created product to cart
            -> Cart
            -> Checkout
            -> verify saved billing details
            -> use a separate shipping address
            -> verify shipping option
            -> place order
            -> verify order confirmation
    """
    # Arrange: Create a dedicated customer for this test execution. The
    # shared address preset avoids duplicating the API address payload.
    customer = dynamic_customer_factory(
        billing=MADRID_ADDRESS.as_billing(),
        shipping=MADRID_ADDRESS.as_shipping(),
    )
    customer_page = login_customer(
        page=page,
        ui_base_url=ui_base_url,
        username=customer.username,
        password=customer.password,
    )

    product_suffix = uuid4().hex[:8]
    product = create_valid_product(
        name=f"UI Checkout Shipping Product {product_suffix}",
        sku=f"ui-checkout-shipping-{product_suffix}",
        regular_price="15.00",
    )
    product_name = product["name"]

    home_page = HomePage(customer_page, ui_base_url)
    home_page.open()

    # Act: Navigate to the Shop and add the dynamically created product to the cart.
    shop_page = home_page.open_shop()
    product_page = shop_page.open_product(product_name)
    product_page.should_be_loaded()
    product_page.add_to_cart()

    # Act: Open the cart and verify the dynamically created product is present.
    cart_page = CartPage(customer_page)
    cart_page.open_from_add_to_cart_notice()
    cart_page.should_be_loaded()
    cart_page.should_contain_product(product_name)

    # Act: Open Checkout and verify the dynamically created customer's saved billing address.
    checkout_page = CheckoutPage(customer_page, ui_base_url)
    checkout_page.open()
    checkout_page.should_be_loaded()

    # Act: Use a separate shipping address and reveal the billing address.
    checkout_page.uncheck_use_same_address_for_billing()

    # Assert: Verify the dynamically created customer's saved billing address.
    checkout_page.should_have_saved_billing_address(
        first_name=MADRID_ADDRESS.first_name,
        last_name=MADRID_ADDRESS.last_name,
        street_address=MADRID_ADDRESS.street_address,
        postal_code=MADRID_ADDRESS.postal_code,
        city=MADRID_ADDRESS.city,
        province=MADRID_ADDRESS.province,
        country=MADRID_ADDRESS.country,
        phone=MADRID_ADDRESS.phone,
    )

    # Act: Open the shipping address form and enter a different address.
    # fill_shipping_address opens the editor when the saved address is collapsed.
    checkout_page.fill_shipping_address(
        first_name="Changan",
        last_name="Beck",
        street_address="Calle Test,25",
        postal_code="28001",
        city="Madrid",
        country="Spain",
        province="Madrid",
    )

    # Assert: Verify that WooCommerce offers a shipping option for the entered address.
    checkout_page.should_have_shipping_option()

    # Act: Place the order.

    checkout_page.place_order()

    # Assert: Verify WooCommerce created and displayed the order confirmation.
    confirmation_page = OrderConfirmationPage(customer_page)
    confirmation_page.should_be_loaded()
    confirmation_page.should_contain_product(product_name)


def test_customer_without_saved_address_can_complete_checkout(
    page: Page,
    ui_base_url: str,
    dynamic_customer_factory,
    create_valid_product,
) -> None:
    """
    Verify that a newly created customer can complete checkout
    by entering an address when no saved addresses exist.

    The customer is provisioned without billing or shipping address data.
    This ensures the test starts with a clean, independent customer account.

    Flow:
        dynamically created customer without saved addresses
            -> Shop
            -> add dynamically created product to cart
            -> Cart
            -> Checkout
            -> use shipping address for billing
            -> enter shipping address
            -> verify shipping option
            -> place order
            -> verify order confirmation
    """
    # Arrange: Create a dedicated customer without saved billing or shipping
    # addresses. The customer is registered for cleanup by the API fixture.
    customer = dynamic_customer_factory()

    # Authenticate using the credentials generated for this customer.
    customer_page = login_customer(
        page=page,
        ui_base_url=ui_base_url,
        username=customer.username,
        password=customer.password,
    )

    # Arrange: Provision a unique product through the API for this UI scenario.
    product_suffix = uuid4().hex[:8]
    product = create_valid_product(
        name=f"UI Checkout No Address Product {product_suffix}",
        sku=f"ui-checkout-no-address-{product_suffix}",
        regular_price="15.00",
    )
    product_name = product["name"]

    # Act: Open the storefront and add the dynamically created product to the cart.
    home_page = HomePage(customer_page, ui_base_url)
    home_page.open()

    shop_page = home_page.open_shop()
    product_page = shop_page.open_product(product_name)
    product_page.should_be_loaded()
    product_page.add_to_cart()

    # Act: Open the cart and verify the product is present.
    cart_page = CartPage(customer_page)
    cart_page.open_from_add_to_cart_notice()
    cart_page.should_be_loaded()
    cart_page.should_contain_product(product_name)

    # Act: Open Checkout and use the shipping address for billing.
    checkout_page = CheckoutPage(customer_page, ui_base_url)
    checkout_page.open()
    checkout_page.should_be_loaded()
    checkout_page.check_use_same_address_for_billing()

    # Act: Enter the customer's address for the first time.
    # WooCommerce uses this address for both billing and shipping.
    checkout_page.fill_shipping_address(
        first_name="John",
        last_name="Beck",
        street_address="Pl.del Pueblo,10",
        postal_code="28100",
        city="Madrid",
        country="Spain",
        province="Madrid",
    )

    # Assert: Wait until WooCommerce has calculated the available shipping option.
    checkout_page.should_have_shipping_option()

    # Act: Place the order.
    checkout_page.place_order()

    # Assert: Verify WooCommerce created and displayed the order confirmation.
    confirmation_page = OrderConfirmationPage(customer_page)
    confirmation_page.should_be_loaded()
    confirmation_page.should_contain_product(product_name)
