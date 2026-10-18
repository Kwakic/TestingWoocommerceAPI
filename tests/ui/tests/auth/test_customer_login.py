"""
UI authentication tests for WooCommerce customer accounts.

These tests validate the positive customer authentication contract at the
business level.

Authenticated scenarios provision a disposable customer through the API.
The shared login helper handles standard authentication, while the email
scenario exercises email-based login directly through the Page Object.

Covered scenarios:
- authenticated customer can access My Account
- existing customer can authenticate using their email address
"""

import pytest
from playwright.sync_api import Page

from tests.ui.data.models.customer_model import DynamicCustomer
from tests.ui.fixtures.customer_auth import login_customer
from tests.ui.pages.account.customer_account_page import CustomerAccountPage
from tests.ui.pages.authentication.customer_login_page import CustomerLoginPage


pytestmark = [
    pytest.mark.ui,
    pytest.mark.smoke,
]


def test_customer_can_access_my_account(
    page: Page,
    ui_base_url: str,
    dynamic_customer: DynamicCustomer,
) -> None:
    """
    Verify that a disposable API-provisioned customer can access My Account.

    The shared login helper performs authentication; API ownership handles
    cleanup of the customer created for this test.
    """

    # Arrange: Build the account Page Object and authenticate this test's customer.
    account_page = CustomerAccountPage(page)
    login_customer(
        page=page,
        ui_base_url=ui_base_url,
        username=dynamic_customer.username,
        password=dynamic_customer.password,
    )

    # Assert: Verify that the customer reached the authenticated My Account area.
    account_page.should_be_loaded()
    account_page.should_be_authenticated()


def test_customer_can_authenticate_with_email(
    page: Page,
    ui_base_url: str,
    dynamic_customer: DynamicCustomer,
) -> None:
    """
    Verify that a customer can authenticate using their email address.

    A disposable customer is provisioned through the API because the test
    needs a valid account as a prerequisite, not a predefined customer persona.
    The test exercises email-based login through the real UI; the dynamic
    customer fixture owns API cleanup.
    """

    # Arrange: Use the disposable customer's email and password.
    email = dynamic_customer.customer["email"]
    password = dynamic_customer.password

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
