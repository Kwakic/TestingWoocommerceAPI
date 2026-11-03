# test_customer_can_logout
# test_customer_session_persistence

"""
UI session-security tests for WooCommerce customer accounts.

These tests validate customer session lifecycle behavior after authentication.

Covered scenarios:
    - an authenticated customer can explicitly log out
    - an authentication session without Remember Me does not persist after
      the browser profile is closed and reopened
    - an authentication session with Remember Me persists after the browser
      profile is closed and reopened
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from playwright.sync_api import BrowserType, Page

from tests.ui.pages.account.customer_account_page import CustomerAccountPage
from tests.ui.data.models.customer_model import DynamicCustomer
from tests.ui.fixtures.customer_auth import login_customer
from tests.ui.pages.authentication.customer_login_page import CustomerLoginPage


pytestmark = [
    pytest.mark.ui,
    pytest.mark.security,
]


def test_customer_can_logout(
    page: Page,
    ui_base_url: str,
    dynamic_customer: DynamicCustomer,
) -> None:
    """
    Verify that a disposable API-provisioned customer can explicitly log out.

    The test logs in with generated credentials, performs the real logout
    action, and verifies that the session ends.
    """
    # Arrange: Build the Page Objects and authenticate this test's customer.
    login_page = CustomerLoginPage(page=page, base_url=ui_base_url)
    account_page = CustomerAccountPage(page)
    login_customer(
        page=page,
        ui_base_url=ui_base_url,
        username=dynamic_customer.username,
        password=dynamic_customer.password,
    )

    # Assert: Confirm the starting state is an authenticated customer session.
    account_page.should_be_loaded()
    account_page.should_be_authenticated()

    # Act: Log out through the real WooCommerce account navigation.
    login_page.logout()

    # Assert: Verify that the authenticated session has ended.
    login_page.should_be_logged_out()


@pytest.mark.parametrize(
    "remember_me",
    [
        pytest.param(False, id="without-remember-me"),
        pytest.param(True, id="with-remember-me"),
    ],
)
def test_customer_session_persistence(
    browser_type: BrowserType,
    ui_base_url: str,
    dynamic_customer: DynamicCustomer,
    remember_me: bool,
    trace_custom_context,
) -> None:
    """
    Check whether “Remember Me” keeps a customer logged in after a browser restart.

    The test first creates a temporary customer through the API and logs in.
    It then closes the browser and opens it again with the same saved browser
    profile. Reusing that profile lets the test check whether WooCommerce saved
    the login information, as it would in a real browser.

    A regular ``page`` fixture gives each test a fresh, temporary browser
    session. This test needs to close and reopen the same saved profile, so it
    creates persistent browser sessions directly. ``trace_custom_context``
    records a Playwright trace for those sessions when tracing is enabled.

    Expected result:
        - If Remember Me is off, the customer is logged out after restart.
        - If Remember Me is on, the customer stays logged in after restart.

    Args:
        browser_type: Browser engine selected for this test (Chromium, Firefox,
            or WebKit).
        ui_base_url: Address of the storefront being tested.
        dynamic_customer: Temporary customer account created for this test.
            The API fixture also arranges cleanup after the test.
        remember_me: Whether this run checks the Remember Me option.
        trace_custom_context: Helper that saves traces for failed custom
            browser sessions when ``--tracing retain-on-failure`` is enabled.

    """
    # Arrange: Use the disposable API-provisioned customer. Its ownership
    # lifecycle handles cleanup after the test completes.
    username = dynamic_customer.username
    password = dynamic_customer.password

    # Arrange: Use one persistent browser profile for the full restart cycle.
    with TemporaryDirectory(prefix="playwright-session-security-") as user_data_dir:
        user_data_path = Path(user_data_dir)

        # Act: Start browser session A using the persistent profile and log in.
        context = browser_type.launch_persistent_context(
            user_data_dir=user_data_path,
            headless=True,
        )

        try:
            with trace_custom_context(context, "initial-login"):
                page: Page = context.pages[0] if context.pages else context.new_page()

                if remember_me:
                    # Use the Page Object's explicit Remember Me login action.
                    login_page = CustomerLoginPage(
                        page=page,
                        base_url=ui_base_url,
                    )
                    login_page.login_with_remember_me(
                        username=username,
                        password=password,
                    )
                else:
                    # Reuse the shared UI authentication helper for standard login.
                    login_customer(
                        page=page,
                        ui_base_url=ui_base_url,
                        username=username,
                        password=password,
                    )

                account_page = CustomerAccountPage(page)

                # Assert: Confirm authentication was established before restart.
                account_page.should_be_loaded()
                account_page.should_be_authenticated()
        finally:
            # Act: Close the entire persistent browser context. This represents
            # closing the browser application while retaining the same profile.
            context.close()

        # Act: Reopen browser session B using the exact same persistent profile.
        context = browser_type.launch_persistent_context(
            user_data_dir=user_data_path,
            headless=True,
        )

        try:
            with trace_custom_context(context, "reopened-session"):
                page = context.pages[0] if context.pages else context.new_page()

                # Act: Open My Account without performing another login.
                page.goto(
                    f"{ui_base_url.rstrip('/')}/my-account/",
                    wait_until="domcontentloaded",
                )

                account_page = CustomerAccountPage(page)

                if remember_me:
                    # Assert: Remember Me must preserve the authenticated session.
                    account_page.should_be_loaded()
                    account_page.should_be_authenticated()
                else:
                    # Assert: Without Remember Me, the customer must return to the
                    # unauthenticated login state after the browser restart.
                    login_page = CustomerLoginPage(
                        page=page,
                        base_url=ui_base_url,
                    )
                    login_page.should_be_logged_out()
        finally:
            context.close()
