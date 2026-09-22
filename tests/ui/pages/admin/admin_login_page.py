"""
Page Object for WordPress administrator authentication.

The Page Object encapsulates:
    - WordPress login locators
    - administrator authentication
    - login-page verification
"""

from urllib.parse import urljoin

from playwright.sync_api import Page, expect


class AdminLoginPage:
    """
    Represent the WordPress administrator login page.

    Authentication remains encapsulated here so tests and role fixtures do not
    contain login selectors or login mechanics.
    """

    def __init__(self, page: Page, base_url: str) -> None:
        """
        Initialize the administrator login Page Object.

        Args:
            page: Playwright Page associated with the test browser context.
            base_url: Storefront base URL.
        """
        self.page = page
        self.base_url = base_url

        # WordPress administrator login fields from the recorded UI flow.
        self.username_input = page.get_by_role(
            "textbox",
            name="Username or Email Address",
            exact=True,
        )
        self.password_input = page.get_by_role(
            "textbox",
            name="Password",
            exact=True,
        )
        self.login_button = page.get_by_role(
            "button",
            name="Log In",
            exact=True,
        )

        self.login_error = page.get_by_role("alert")

    def open(self) -> None:
        """Navigate to the WordPress administrator login page."""
        self.page.goto(
            urljoin(self.base_url.rstrip("/") + "/", "wp-login.php"),
            wait_until="domcontentloaded",
        )

    def login(self, username: str, password: str) -> None:
        """
        Authenticate as a WordPress administrator.

        Args:
            username: Administrator username.
            password: Administrator password.
        """
        self.open()

        self.username_input.fill(username)
        self.password_input.fill(password)

        # Click the login button and observe the WordPress authentication response.
        #
        # Keep the response predicate tolerant of query parameters and use
        # no_wait_after so the browser-specific navigation handling remains
        # under our control. This mirrors the robust customer-login flow and
        # avoids Firefox timing out while the native form navigation is handled.
        with self.page.expect_response(
            lambda r: (r.request.method == "POST" and "wp-login.php" in r.url)
        ) as response_info:
            self.login_button.click(no_wait_after=True)

        login_response = response_info.value

        if login_response.status not in (200, 302):
            raise AssertionError(
                f"Administrator login request failed with HTTP {login_response.status}."
            )

        # WordPress normally redirects a successful login to wp-admin.
        redirect_url = login_response.headers.get("location")

        if redirect_url:
            self.page.goto(
                urljoin(self.page.url, redirect_url),
                wait_until="domcontentloaded",
            )

        self.should_be_authenticated()

    def should_be_authenticated(self) -> None:
        """Verify that WordPress administrator authentication succeeded."""
        expect(self.page).to_have_url(f"{self.base_url.rstrip('/')}/wp-admin/")
        # expect(self.page).to_have_url(
        #     re.compile(r".*/wp-admin/.*")
        # ) # The first .* allows any text before /wp-admin/ (like https://example.com).The second .* allows any text after /wp-admin/ (like index.php or post-new.php).
