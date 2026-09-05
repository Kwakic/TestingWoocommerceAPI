"""
Page Object for the WooCommerce storefront home page.

The Page Object encapsulates:
    - page-specific navigation
    - locators
    - user interactions
    - page-level verification

Tests should use this class to interact with the home page instead of
containing Playwright selectors and navigation details directly.
"""

from playwright.sync_api import Page, expect

from tests.ui.pages.shop_page import ShopPage


class HomePage:
    """
    Represent the WooCommerce storefront home page.

    This class follows the Page Object Model (POM) by keeping UI
    implementation details separate from test behavior.
    """

    def __init__(self, page: Page, base_url: str) -> None:
        """
        Initialize the Home Page Object.

        Args:
            page: Playwright Page associated with the current test context.
            base_url: Base URL of the WooCommerce storefront.
        """
        self.page = page
        self.base_url = base_url

        # Main heading used to verify that the home page is loaded.
        self.home_heading = page.get_by_role(
            "heading",
            name="A commitment to innovation and sustainability",
        )

        # Storefront navigation link used to open the Shop page.
        self.shop_link = page.get_by_role("banner").get_by_role(
            "link",
            name="Shop",
            exact=True,
        )

    def open(self) -> None:
        """Navigate to the WooCommerce storefront home page."""
        self.page.goto(self.base_url)

    def should_be_loaded(self) -> None:
        """
        Verify that the WooCommerce storefront home page is loaded.

        The verification is kept inside the Page Object so tests do not
        depend on Playwright selectors or page implementation details.
        """
        expect(self.home_heading).to_be_visible()

    def open_shop(self) -> ShopPage:
        """
        Navigate from the home page to the Shop page.

        Returns:
            ShopPage: Page Object representing the Shop page.
        """
        self.shop_link.click()

        return ShopPage(self.page)
