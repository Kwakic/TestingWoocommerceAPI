"""
Page Object for the authenticated WooCommerce customer account area.

The Page Object encapsulates:
    - account-page locators
    - authenticated customer navigation
    - page-level verification of customer access

Authentication itself is intentionally owned by the customer role fixture and
CustomerLoginPage. This Page Object verifies the authenticated capability that
the customer is expected to have after login.
"""

from playwright.sync_api import Page, expect


class CustomerAccountPage:
    """
    Represent the authenticated WooCommerce customer account page.

    This class follows the Page Object Model by keeping account-page locators
    and verification details outside of the test layer.
    """

    def __init__(self, page: Page) -> None:
        """
        Initialize the Customer Account Page Object.

        Args:
            page: Playwright Page associated with the authenticated customer
                browser context.
        """
        self.page = page

        # Primary account-page heading used as the authenticated access
        # contract. This confirms that the customer reached the My Account area.
        self.account_heading = page.get_by_role(
            "heading",
            name="My account",
            exact=True,
        )

        # The authenticated customer logout control is rendered inside the
        # WooCommerce "Account pages" navigation. Scoping to that navigation avoids
        # ambiguity when the theme renders another logout link in the page header.
        self.logout_link = page.get_by_label("Account pages").get_by_role(
            "link",
            name="Log out",
            exact=True,
        )

    def should_be_loaded(self) -> None:
        """
        Verify that the authenticated customer account page is displayed.

        The assertion is intentionally kept inside the Page Object so tests
        do not depend directly on Playwright selectors.
        """
        expect(self.account_heading).to_be_visible()

    def should_be_authenticated(self) -> None:
        """
        Verify that the current browser session is authenticated.

        This complements account-page verification with the authenticated-only
        logout control exposed by WooCommerce.
        """
        expect(self.logout_link).to_be_visible()
