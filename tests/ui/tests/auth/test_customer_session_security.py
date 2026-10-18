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
    customer_page: Page,
    ui_base_url: str,
) -> None:
    """
    Verify that an authenticated customer can explicitly log out.

    The test starts from the standard authenticated customer fixture, performs
    the real WooCommerce logout action, and verifies that the session returns
    to the unauthenticated login state.
    """
    # Arrange: The customer fixture provides a successfully authenticated page.
    login_page = CustomerLoginPage(
        page=customer_page,
        base_url=ui_base_url,
    )
    account_page = CustomerAccountPage(customer_page)

    # Assert: Confirm the starting state is an authenticated customer session.
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
) -> None:
    """
    Verify customer session behavior after closing and reopening the browser.

    A disposable customer is provisioned through the API by the
    ``dynamic_customer`` fixture; the API ownership lifecycle handles cleanup.
    The test uses ``login_customer``'s established authentication flow for the
    customer credentials, while managing its own persistent browser contexts.

    The same persistent browser profile is deliberately reused for both phases
    of the test. This models a real browser restart while preserving the browser
    profile data that may contain WooCommerce authentication cookies.

    Expected behavior:
        - Without Remember Me: authentication is not expected to persist.
        - With Remember Me: authentication is expected to persist.

    Args:
        browser_type: Playwright browser type selected by pytest.
        ui_base_url: Base URL of the WooCommerce storefront.
        dynamic_customer: API-provisioned customer used for the login lifecycle.
        remember_me: Whether the Remember Me option is enabled before login.

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
