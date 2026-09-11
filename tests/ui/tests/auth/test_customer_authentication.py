"""
UI authentication tests for WooCommerce customer accounts.

These tests validate the positive customer authentication contract at the
business level.

The ``customer_page`` fixture owns the standard customer authentication flow.
Authentication-specific tests may deliberately bypass that fixture when they
need to validate a particular authentication mechanism, such as email-based
login.

Covered scenarios:
- authenticated customer can access My Account
- existing customer can authenticate using their email address

Covered scenarios:
- login with username
- login with email
"""

import os
import pytest
from playwright.sync_api import Page

from tests.ui.pages.customer_login_page import CustomerLoginPage
from tests.ui.pages.customer_account_page import CustomerAccountPage


pytestmark = [
    pytest.mark.ui,
    pytest.mark.smoke,
]


def test_customer_can_access_my_account(
    customer_page: Page,
) -> None:
    """
    Verify that the dedicated UI customer can access My Account after login.

    The ``customer_page`` fixture owns credential handling and authentication.
    This test therefore validates the resulting business capability rather
    than duplicating the login implementation.
    """

    # Arrange: Build the Page Object for the authenticated customer account.
    account_page = CustomerAccountPage(customer_page)

    # Assert: Verify that the customer reached the authenticated My Account area.
    account_page.should_be_loaded()
    account_page.should_be_authenticated()


def test_customer_can_authenticate_with_email(
    page: Page,
    ui_base_url: str,
) -> None:
    """
    Verify that an existing customer can authenticate using their email address.

    WooCommerce supports authentication using either the customer's username
    or email address. This test explicitly validates the email-based login path
    independently of the ``customer_page`` fixture.

    The fixture is intentionally not used here because the purpose of this
    test is to exercise the authentication mechanism itself.
    """

    # Arrange: Load the existing customer's email and password.
    email = os.getenv("UI_CUSTOMER_EMAIL")
    password = os.getenv("UI_CUSTOMER_PASSWORD")

    if not email or not password:
        raise pytest.UsageError(
            "UI_CUSTOMER_EMAIL and UI_CUSTOMER_PASSWORD are required."
        )

    login_page = CustomerLoginPage(
        page=page,
        base_url=ui_base_url,
    )

    # Act: Authenticate using the customer's email address.
    login_page.login(
        username=email,
        password=password,
    )

    # Assert: Verify that email-based authentication established a session.
    login_page.should_be_authenticated()

    account_page = CustomerAccountPage(page)

    # Assert: Verify the authenticated customer can access My Account.
    account_page.should_be_loaded()
    account_page.should_be_authenticated()
