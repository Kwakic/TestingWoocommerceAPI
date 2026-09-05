"""
Page Object for the WooCommerce Shop page.

The Page Object encapsulates:
    - page-specific locators
    - page-specific interactions
    - page-specific verification concepts

Tests should use this class to interact with the Shop page instead of
containing Playwright selectors and implementation details directly.
"""

from playwright.sync_api import Page, expect
from tests.ui.pages.product_page import ProductPage


class ShopPage:
    """
    Represent the WooCommerce Shop page.

    This class owns the UI implementation details associated with
    the Shop page.
    """

    def __init__(self, page: Page) -> None:
        """
        Initialize the Shop Page Object.

        Args:
            page: Playwright Page associated with the current test context.
        """
        self.page = page
        self.shop_heading = page.get_by_role(
            "heading",
            name="Shop",
        )

    def should_be_loaded(self) -> None:
        """
        Verify that the Shop page is loaded.

        The exact page-level verification is intentionally kept inside
        the Page Object so tests do not depend on implementation details
        such as the browser title.
        """
        expect(self.shop_heading).to_be_visible()

    def open_product(self, product_name: str) -> ProductPage:
        """Open a product from the Shop page."""
        self.page.get_by_role("link", name=product_name).click()
        return ProductPage(self.page)


# def test_seeded_products_are_visible(page):
#     shop_page = ShopPage(page)
#
#     shop_page.open()
#
#     assert shop_page.is_product_visible("UI Seed - Album")
#     assert shop_page.is_product_visible("UI Seed - Beanie")
#     assert shop_page.is_product_visible("UI Seed - Hoodie")
