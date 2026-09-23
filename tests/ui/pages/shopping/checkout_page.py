"""
Page Object for the WooCommerce Checkout page.

The Page Object encapsulates checkout form locators and user interactions.
The test remains responsible for the business scenario.
"""

import re

from playwright.sync_api import Page, expect


class CheckoutPage:
    """Represent the WooCommerce Checkout page."""

    def __init__(self, page: Page, base_url: str) -> None:
        self.page = page
        self.base_url = base_url

        # Checkout fields that remain visible for an authenticated customer.
        self.email_input = page.get_by_role("textbox", name="Email address")

        # Saved billing details are displayed as a summary until the customer
        # explicitly chooses to edit the address.
        # WooCommerce displays saved billing information as a summary inside
        # the Billing address section until the customer chooses "Edit address".
        self.billing_address_section = page.get_by_role(
            "group",
            name="Billing address",
        )

        # Shipping-address section used when checkout requires a destination
        # different from the customer's saved billing address.
        self.shipping_address_section = page.get_by_role(
            "group",
            name="Shipping address",
        )

        # Payment method recorded during the successful checkout flow.
        self.cash_on_delivery = page.get_by_text(
            "Cash on delivery",
            exact=True,
        )

        self.add_order_note_checkbox = page.get_by_role(
            "checkbox",
            name="Add a note to your order",
        )
        self.order_note_input = page.get_by_role(
            "textbox",
            name="Notes about your order.",
        )
        self.place_order_button = page.get_by_role(
            "button",
            name="Place Order",
        )

    def open(self) -> None:
        """Navigate directly to the Checkout page."""
        self.page.goto(
            f"{self.base_url.rstrip('/')}/checkout/",
            wait_until="domcontentloaded",
        )

    def should_be_loaded(self) -> None:
        """Verify that the authenticated checkout page is displayed."""
        expect(self.email_input).to_be_visible()
        expect(self.billing_address_section).to_be_visible()
        expect(self.place_order_button).to_be_visible()

    def should_have_saved_billing_address(
        self,
        first_name: str,
        last_name: str,
        street_address: str,
        postal_code: str,
        city: str,
        province: str,
        country: str,
        phone: str,
    ) -> None:
        """Verify the customer's saved billing details are displayed."""
        expect(self.billing_address_section).to_contain_text(
            f"{first_name} {last_name}"
        )
        expect(self.billing_address_section).to_contain_text(street_address)
        expect(self.billing_address_section).to_contain_text(postal_code)
        expect(self.billing_address_section).to_contain_text(city)
        expect(self.billing_address_section).to_contain_text(province)
        expect(self.billing_address_section).to_contain_text(country)
        expect(self.billing_address_section).to_contain_text(phone)

    def fill_shipping_address(
        self,
        first_name: str,
        last_name: str,
        street_address: str,
        city: str,
        postal_code: str,
    ) -> None:
        """Fill the checkout shipping address with a destination different from billing."""
        self.shipping_address_section.get_by_role(
            "textbox",
            name="First name *",
        ).fill(first_name)
        self.shipping_address_section.get_by_role(
            "textbox",
            name="Last name *",
        ).fill(last_name)
        self.shipping_address_section.get_by_role(
            "textbox",
            name="Street address *",
        ).fill(street_address)
        self.shipping_address_section.get_by_role(
            "textbox",
            name="Town / City *",
        ).fill(city)
        self.shipping_address_section.locator("#shipping_postcode").fill(postal_code)

    def should_have_shipping_address(
        self,
        first_name: str,
        last_name: str,
        street_address: str,
        city: str,
        postal_code: str,
    ) -> None:
        """Verify that the requested shipping address is displayed at checkout."""
        expect(self.shipping_address_section).to_contain_text(
            f"{first_name} {last_name}"
        )
        expect(self.shipping_address_section).to_contain_text(street_address)
        expect(self.shipping_address_section).to_contain_text(city)
        expect(self.shipping_address_section).to_contain_text(postal_code)

    def select_cash_on_delivery(self) -> None:
        """Select Cash on delivery as the checkout payment method."""
        self.cash_on_delivery.click()

    def add_order_note(self, note: str) -> None:
        """Enable the order-note field and enter the supplied note."""
        self.add_order_note_checkbox.check()
        self.order_note_input.fill(note)

    def place_order(self) -> None:
        """Submit the order and wait for WooCommerce order confirmation."""
        self.place_order_button.click()
        self.page.wait_for_url(
            re.compile(r".*/checkout/order-received/\d+/.*"),
            wait_until="domcontentloaded",
        )
