"""
Page Object for the WooCommerce customer registration flow.

The Page Object encapsulates:
    - customer registration navigation
    - registration form locators
    - registration interaction
    - registration outcome verification

Registration data is supplied by the test or fixture layer.
"""

from playwright.sync_api import Page, expect


class CustomerRegistrationPage:
    """
    Represent the WooCommerce customer registration section on My Account.

    This Page Object owns registration UI implementation details so tests can
    focus on the registration and security contract.
    """

    def __init__(self, page: Page, base_url: str) -> None:
        """
        Initialize the customer registration Page Object.

        Args:
            page: Playwright Page associated with the current test context.
            base_url: Base URL of the WooCommerce storefront.
        """
        self.page = page
        self.base_url = base_url

        # WooCommerce exposes customer registration on the My Account page
        # when the corresponding account-creation setting is enabled.
        self.email_input = page.get_by_role(
            "textbox",
            name="Email address *",
            exact=True,
        )
        self.register_button = page.get_by_role(
            "button",
            name="Register",
            exact=True,
        )

        # Registration failures are rendered as an accessible alert.
        self.registration_error = page.get_by_role("alert")

        self.register_heading = page.get_by_role(
            "heading",
            name="Register",
            exact=True,
        )

    def open(self) -> None:
        """Navigate to the WooCommerce My Account page."""
        self.page.goto(
            f"{self.base_url.rstrip('/')}/my-account/",
            wait_until="domcontentloaded",
        )

    def should_be_loaded(self) -> None:
        """
        Verify that the customer registration section is available.
        """
        expect(self.register_heading).to_be_visible()
        expect(self.email_input).to_be_visible()
        expect(self.register_button).to_be_visible()

    def register(self, email: str) -> None:
        """
        Submit the customer registration form.

        WooCommerce generates the customer username and sends the password
        setup link separately, so this registration contract requires only
        an email address in the current environment.

        Args:
            email: Email address submitted for customer registration.

        Note:
             We have to capture the POST response explicitly and manually
             follow the redirect when WooCommerce returns one.
        """
        self.email_input.fill(email)

        with self.page.expect_response(
            lambda candidate_response: candidate_response.request.method == "POST"
        ) as response_info:
            self.register_button.click(no_wait_after=True)

        response = response_info.value

        if response.status not in (200, 302):
            raise AssertionError(
                f"Customer registration failed with unexpected HTTP status "
                f"{response.status}."
            )

        redirect_url = response.headers.get("location")

        if redirect_url:
            from urllib.parse import urljoin

            self.page.goto(
                urljoin(self.page.url, redirect_url),
                wait_until="domcontentloaded",
            )
        else:
            self.page.wait_for_load_state("domcontentloaded")

    def should_show_existing_email_error(self) -> None:
        """
        Verify that WooCommerce rejects an email already associated with
        an existing customer account.
        """
        expect(self.registration_error).to_contain_text(
            "An account is already registered with your email address."
        )
