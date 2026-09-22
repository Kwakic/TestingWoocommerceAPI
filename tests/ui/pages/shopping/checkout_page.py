"""
Page Object for the WooCommerce Checkout page.

The Page Object encapsulates checkout locators, UI interactions, and page-level
state verification. The test remains responsible for the business scenario.
"""

import re

from playwright.sync_api import Page, expect


class CheckoutPage:
    """Represent the WooCommerce Checkout page."""

    def __init__(self, page: Page, base_url: str) -> None:
        self.page = page
        self.base_url = base_url

        # Customer contact information.
        self.email_input = page.get_by_role(
            "textbox",
            name="Email address",
        )

        # Billing address section rendered by the WooCommerce Checkout Block.
        # Scope the address fields to this section so the selectors remain
        # independent of the currently selected country/state values.
        self.billing_address_section = page.get_by_role(
            "group",
            name="Billing address",
            exact=True,
        )

        # WooCommerce renders country and state as the two comboboxes in the
        # billing address group. Their accessible names include the current
        # selected value, so the stable selector is their position within the
        # billing address section rather than a value-dependent name.
        self.country_combobox = self.billing_address_section.get_by_role(
            "combobox"
        ).first  # Inside the Billing address section, find all elements with role combobox, and give me the first one.
        self.first_name_input = self.billing_address_section.get_by_role(
            "textbox",
            name="First name",
        )
        self.last_name_input = self.billing_address_section.get_by_role(
            "textbox",
            name="Last name",
        )
        self.address_input = self.billing_address_section.get_by_role(
            "textbox",
            name="Address",
            exact=True,
        )
        self.city_input = self.billing_address_section.get_by_role(
            "textbox",
            name="City",
        )
        # The second combobox is the state/province field. Its accessible
        # name changes with the selected country (for Spain it is "Province").
        self.state_combobox = self.billing_address_section.get_by_role("combobox").nth(
            1
        )  # Give me the second combobox which is State.
        # The field label is localized by the selected country. For Spain,
        # WooCommerce renders this field as "Postal code" rather than "ZIP Code".
        self.postal_code_input = self.billing_address_section.get_by_role(
            "textbox",
            name=re.compile(r"^(ZIP Code|Postal code)$"),
        )
        self.phone_input = self.billing_address_section.get_by_role(
            "textbox",
            name="Phone (optional)",
        )

        # Payment method.
        self.cash_on_delivery = page.get_by_text(
            "Cash on delivery",
            exact=True,
        )

        # Optional order note.
        self.add_order_note_checkbox = page.get_by_role(
            "checkbox",
            name="Add a note to your order",
        )
        self.order_note_input = page.get_by_role(
            "textbox",
            name="Notes about your order.",
        )

        # Checkout submission.
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
        """Verify that the checkout page is displayed and ready for input."""
        expect(self.email_input).to_be_visible()
        expect(self.first_name_input).to_be_visible()
        expect(self.last_name_input).to_be_visible()
        expect(self.address_input).to_be_visible()
        expect(self.city_input).to_be_visible()
        expect(self.postal_code_input).to_be_visible()
        expect(self.place_order_button).to_be_visible()

    def fill_billing_address(
        self,
        first_name: str,
        last_name: str,
        street_address: str,
        postal_code: str,
        city: str,
        province: str,
        country: str,
        phone: str | None = None,
    ) -> None:
        """Fill the billing address fields required for checkout.

        The authenticated customer's email is already supplied by WooCommerce,
        so the method only fills the billing information required by this
        scenario.
        """
        self.first_name_input.fill(first_name)
        self.last_name_input.fill(last_name)
        self.address_input.fill(street_address)
        self.city_input.fill(city)

        # WooCommerce uses searchable comboboxes for country and state.
        self.country_combobox.click()
        self.country_combobox.fill(country)
        self.page.get_by_role(
            "option",
            name=country,
            exact=True,
        ).click()

        self.state_combobox.click()
        self.state_combobox.fill(province)
        self.page.get_by_role(
            "option",
            name=province,
            exact=True,
        ).click()

        self.postal_code_input.fill(postal_code)

        if phone is not None:
            self.phone_input.fill(phone)

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
