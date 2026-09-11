"""
Page Object for the WooCommerce customer password-recovery flow.

The Page Object encapsulates:
    - password-recovery navigation
    - recovery form locators
    - reset-request interaction
    - password-recovery outcome verification

Recovery credentials and test data are supplied by the test or fixture layer.
"""

from playwright.sync_api import Page, expect


class CustomerPasswordRecoveryPage:
    """
    Represent the WooCommerce customer password-recovery page.

    This Page Object owns password-recovery UI implementation details so tests
    remain focused on business and security behavior.
    """

    def __init__(self, page: Page, base_url: str) -> None:
        """
        Initialize the password-recovery Page Object.

        Args:
            page: Playwright Page associated with the current test context.
            base_url: Base URL of the WooCommerce storefront.
        """
        self.page = page
        self.base_url = base_url

        # WooCommerce password-recovery form.
        self.username_or_email_input = page.get_by_label("Username or email")
        self.reset_password_button = page.get_by_role(
            "button",
            name="Reset password",
            exact=True,
        )

        # WooCommerce renders password-recovery validation failures as an accessible alert.
        self.recovery_error = page.get_by_role("alert")

        self.recovery_heading = page.get_by_role(
            "heading",
            name="Lost password",
            exact=True,
        )

    def open(self) -> None:
        """Navigate directly to the WooCommerce password-recovery page."""
        self.page.goto(
            f"{self.base_url.rstrip('/')}/my-account/lost-password/",
            wait_until="domcontentloaded",
        )

    def should_be_loaded(self) -> None:
        """
        Verify that the password-recovery page is displayed.
        """
        expect(self.recovery_heading).to_be_visible()

    def request_reset(self, username_or_email: str) -> None:
        """
        Submit a password-reset request.

        Args:
            username_or_email: Username or email supplied to WooCommerce.
        """
        self.open()

        self.username_or_email_input.fill(username_or_email)
        self.reset_password_button.click()

        self.page.wait_for_load_state("domcontentloaded")

    def should_show_invalid_identifier_error(self) -> None:
        """
        Verify that WooCommerce rejects an unknown username or email.
        """
        expect(self.recovery_error).to_contain_text("Invalid username or email.")
