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
        self.billing_address_section = page.get_by_role(
            "group",
            name="Billing address",
        )

        # The Checkout Block exposes shipping and billing as separate groups
        # once "Use same address for billing" is unchecked.
        self.shipping_address_section = page.get_by_role(
            "group",
            name="Shipping address",
        )
        self.use_same_address_for_billing = page.get_by_role(
            "checkbox",
            name="Use same address for billing",
        )

        self.add_order_note_checkbox = page.get_by_role(
            "checkbox",
            name="Add a note to your order",
        )
        self.order_note_input = page.get_by_role(
            "textbox",
            name="Notes about your order, e.g.",
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
        expect(self.shipping_address_section).to_be_visible()
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

    def check_use_same_address_for_billing(self) -> None:
        """Use the shipping address as the billing address."""
        self.use_same_address_for_billing.check()

    def uncheck_use_same_address_for_billing(self) -> None:
        """Show separate billing and shipping address forms."""
        self.use_same_address_for_billing.uncheck()

    def edit_shipping_address(self) -> None:
        """Open the shipping address form from the saved address summary."""
        self.shipping_address_section.get_by_label("Edit address").click()

    def fill_shipping_address(
        self,
        first_name: str,
        last_name: str,
        street_address: str,
        postal_code: str,
        city: str,
    ) -> None:
        """
        Fill the shipping address shown in the Checkout Block.

        WooCommerce may display a saved shipping address as a summary
        instead of showing the editable fields. When that happens, open
        the shipping address form before entering the supplied address.
        """
        first_name_input = self.shipping_address_section.get_by_label("First name")

        if not first_name_input.is_visible():
            self.edit_shipping_address()

        first_name_input.fill(first_name)
        self.shipping_address_section.get_by_label("Last name").fill(last_name)
        self.shipping_address_section.get_by_label("Address", exact=True).fill(
            street_address
        )
        self.shipping_address_section.get_by_label("Postal code", exact=True).fill(
            postal_code
        )
        self.shipping_address_section.get_by_label("City").fill(city)

    def should_have_shipping_option(self) -> None:
        """Verify that the configured flat-rate shipping option is available."""
        expect(
            self.page.get_by_role("radio", name=re.compile(r"Flat rate", re.I))
        ).to_be_visible()

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
