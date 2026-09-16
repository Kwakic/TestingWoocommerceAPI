"""
Page Object for the WooCommerce order-confirmation page.

The Page Object encapsulates confirmation-page verification only.
"""

import re

from playwright.sync_api import Page, expect


class OrderConfirmationPage:
    """Represent the WooCommerce order-received page."""

    def __init__(self, page: Page) -> None:
        self.page = page

        self.thank_you_message = page.get_by_text(
            re.compile(r"Thank you\. Your order has"),
        )
        self.order_number_text = page.get_by_text(
            re.compile(r"Order number:"),
        )
        self.order_details_heading = page.get_by_role(
            "heading",
            name="Order details",
            exact=True,
        )
        self.order_note_text = page.get_by_text("Be smily", exact=True)
        self.product_link = page.get_by_role(
            "link",
            name="UI Seed – Album",
            exact=True,
        )

    def should_be_loaded(self) -> None:
        """Verify that WooCommerce displayed the order confirmation page."""
        expect(self.thank_you_message).to_be_visible()
        expect(self.order_number_text).to_be_visible()
        expect(self.order_details_heading).to_be_visible()

    def should_contain_product(self, product_name: str) -> None:
        """Verify that the confirmation contains the purchased product."""
        expect(
            self.page.get_by_role("link", name=product_name, exact=True)
        ).to_be_visible()

    def should_show_order_note(self, note: str) -> None:
        """Verify that the submitted order note is displayed."""
        expect(self.page.get_by_text(note, exact=True)).to_be_visible()
