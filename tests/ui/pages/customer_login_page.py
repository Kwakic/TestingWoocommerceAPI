"""
Page Object for the WooCommerce customer auth flow.

The Page Object encapsulates:
    - the customer auth URL
    - auth form locators
    - auth interaction
    - page-level authentication verification
    - negative authentication outcome verification
    - logout interaction and logged-out state verification

Authentication credentials are intentionally not stored in this Page Object.
The fixture or test layer supplies credentials from the execution environment.
"""

from urllib.parse import urljoin

from playwright.sync_api import Page, expect


class CustomerLoginPage:
    """
    Represent the WooCommerce My Account auth page.

    This Page Object owns UI implementation details for customer auth.
    Tests and fixtures should not contain auth selectors or navigation
    mechanics directly.
    """

    def __init__(self, page: Page, base_url: str) -> None:
        """
        Initialize the Customer Login Page Object.

        Args:
            page: Playwright Page associated with the current test context.
            base_url: Base URL of the WooCommerce storefront.
        """
        self.page = page
        self.base_url = base_url

        # WooCommerce customer auth form.
        self.username_input = page.get_by_label("Username or email address")
        self.password_input = page.get_by_label("Password")
        self.login_button = page.get_by_role(
            "button",
            name="Log in",
            exact=True,
        )
        self.remember_me_checkbox = page.get_by_role(
            "checkbox",
            name="Remember me",
            exact=True,
        )

        # WooCommerce renders authentication failures as an accessible alert.
        self.login_error = page.get_by_role("alert")

        # The WooCommerce "Account pages" navigation contains the authenticated
        # customer logout control. Scoping the locator to this navigation
        # avoids the duplicate logout link rendered elsewhere on the page.
        self.logout_link = page.get_by_label("Account pages").get_by_role(
            "link",
            name="Log out",
            exact=True,
        )

    def open(self) -> None:
        """Navigate to the WooCommerce My Account page."""
        self.page.goto(
            f"{self.base_url.rstrip('/')}/my-account/",
            wait_until="domcontentloaded",
        )

    def login(self, username: str, password: str) -> None:
        """
        Authenticate the current browser context as a WooCommerce customer.

        WooCommerce performs a native form POST and normally redirects the
        customer back to the My Account page. The request/response is observed
        explicitly so browser-specific navigation timing does not weaken the
        authentication contract.

        Args:
            username: Customer username or email address.
            password: Customer password.

        Raises:
            AssertionError: If the login endpoint does not return a successful
                HTTP response.
        """
        response = self._submit_login(username=username, password=password)

        if response.status not in (200, 302):
            raise AssertionError(
                "Customer login request failed with HTTP " f"{response.status}."
            )

        self._follow_login_redirect(response)

        # Authentication must be established before the role fixture exposes
        # the page to customer tests.
        self.should_be_authenticated()

    def login_with_remember_me(self, username: str, password: str) -> None:
        """
        Authenticate the customer with Remember Me enabled.

        This method uses the real WooCommerce login form and explicitly enables
        the Remember Me option before submitting the credentials.

        Args:
            username: Customer username or email address.
            password: Password supplied for the login attempt.

        Raises:
            AssertionError: If the login request does not return a successful
                HTTP response.
        """
        self.open()

        self.username_input.fill(username)
        self.password_input.fill(password)
        self.remember_me_checkbox.check()

        with self.page.expect_response(
            lambda candidate_response: candidate_response.request.method == "POST"
        ) as response_info:
            self.login_button.click(no_wait_after=True)

        response = response_info.value

        if response.status not in (200, 302):
            raise AssertionError(
                "Customer login request failed with HTTP " f"{response.status}."
            )

        self._follow_login_redirect(response)
        self.should_be_authenticated()

    def attempt_login(self, username: str, password: str) -> None:
        """
        Submit customer credentials without assuming authentication succeeds.

        This method is intended for negative authentication tests where the
        response may legitimately represent a rejected login attempt.

        Args:
            username: Customer username or email address.
            password: Password supplied for the login attempt.
        """
        response = self._submit_login(username=username, password=password)

        # A rejected login is expected to remain on the login page. Follow a
        # redirect only when WooCommerce explicitly returns one so that this
        # method remains useful for both successful and unsuccessful attempts.
        self._follow_login_redirect(response)

    def should_be_authenticated(self) -> None:
        """
        Verify that the current browser context is authenticated.

        The logout control is used as the page-level authentication contract.
        This keeps the assertion independent from customer-specific profile
        data and avoids exposing credentials in test code.
        """
        expect(self.logout_link).to_be_visible()

    def should_not_be_authenticated(self) -> None:
        """
        Verify that the current browser context is not authenticated.

        The authenticated-only logout control must not be visible after a
        rejected login attempt.
        """
        expect(self.logout_link).not_to_be_visible()

    def should_show_login_error(self) -> None:
        """
        Verify that WooCommerce displays an authentication error notice.

        The assertion intentionally checks the WooCommerce error container
        rather than matching the complete message text because the exact
        message can vary by credential scenario.
        """
        expect(self.login_error).to_be_visible()

    def logout(self) -> None:
        """
        Log out the currently authenticated WooCommerce customer.

        The logout control is scoped to the WooCommerce account navigation,
        ensuring that the authenticated customer session is explicitly
        terminated through the real UI.

        Raises:
            AssertionError: If the authenticated logout control is unavailable.
        """
        self.logout_link.click()
        self.page.wait_for_load_state("domcontentloaded")

    def should_be_logged_out(self) -> None:
        """
        Verify that the current browser session is no longer authenticated.

        The customer login form must be visible and the authenticated-only
        logout control must no longer be visible.
        """
        expect(self.login_button).to_be_visible()
        expect(self.logout_link).not_to_be_visible()

    def _submit_login(self, username: str, password: str):
        """
        Submit the login form and return the native POST response.

        Args:
            username: Customer username or email address.
            password: Password supplied for the login attempt.

        Returns:
            Response: Native WooCommerce login POST response.
        """
        self.open()

        self.username_input.fill(username)
        self.password_input.fill(password)

        with self.page.expect_response(
            lambda candidate_response: candidate_response.request.method == "POST"
        ) as response_info:
            self.login_button.click(no_wait_after=True)

        return response_info.value

    def _follow_login_redirect(self, response) -> None:
        """
        Follow a WooCommerce redirect when the login response provides one.

        Args:
            response: Native WooCommerce login POST response.
        """
        redirect_url = response.headers.get("location")

        if redirect_url:
            absolute_redirect_url = urljoin(self.page.url, redirect_url)
            self.page.goto(
                absolute_redirect_url,
                wait_until="domcontentloaded",
            )
        else:
            self.page.wait_for_load_state("domcontentloaded")

    def should_show_username_required_error(self) -> None:
        """Verify that WooCommerce requires a username or email."""
        expect(self.login_error).to_contain_text("Error: Username is required.")

    def should_show_password_required_error(self) -> None:
        """Verify that WooCommerce requires a password."""
        expect(self.login_error).to_contain_text("Error: The password field is")

    def should_show_invalid_username_error(self) -> None:
        """Verify that WooCommerce rejects an unknown username."""
        expect(self.login_error).to_contain_text("Error: The username")
