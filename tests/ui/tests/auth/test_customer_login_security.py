"""
Negative UI authentication and security tests for WooCommerce customers.

These tests validate that invalid customer credentials cannot establish an
authenticated session. Authentication mechanics remain in the
CustomerLoginPage Page Object, while the tests validate the security contract
at the business level.

Covered scenarios:
- invalid username
- invalid email
- invalid password + username
- invalid password + email
- invalid username + password
- empty username
- empty password

The test also validates the expected WooCommerce error for scenarios where
Codegen confirmed the user-facing validation contract.
"""

import pytest
from playwright.sync_api import Page

from tests.ui.pages.authentication.customer_login_page import CustomerLoginPage
from tests.ui.data.models.customer_model import DynamicCustomer

pytestmark = [
    pytest.mark.ui,
    pytest.mark.security,
]


@pytest.mark.parametrize(
    "scenario",
    [
        pytest.param("invalid_password_username", id="invalid-password-username"),
        pytest.param("invalid_password_email", id="invalid-password-email"),
        pytest.param("invalid_username", id="invalid-username"),
        pytest.param("unknown_email", id="unknown-email"),
        pytest.param("invalid_credentials", id="invalid-credentials"),
        pytest.param("empty_username", id="empty-username"),
        pytest.param("empty_password", id="empty-password"),
    ],
)
def test_customer_cannot_authenticate_with_invalid_credentials(
    page: Page,
    ui_base_url: str,
    dynamic_customer: DynamicCustomer,
    scenario: str,
) -> None:
    """
    Verify that invalid customer credentials cannot establish authentication.

    A disposable customer is provisioned through the API because the test needs
    valid credentials to construct negative combinations, not a predefined
    customer persona. The dynamic customer fixture owns API cleanup.
    """

    # Arrange: Use credentials from the disposable API-provisioned customer.
    valid_username = dynamic_customer.username
    valid_email = dynamic_customer.customer["email"]
    valid_password = dynamic_customer.password

    login_page = CustomerLoginPage(
        page=page,
        base_url=ui_base_url,
    )

    # Arrange: Build the credential combination for the selected security case.
    if scenario == "invalid_password_username":
        username = valid_username
        password = "invalid-password"

    elif scenario == "invalid_password_email":
        username = valid_email
        password = "invalid-password"

    elif scenario == "invalid_username":
        username = f"invalid-{valid_username}"
        password = valid_password

    elif scenario == "unknown_email":
        username = f"unknown-{valid_email}"
        password = valid_password

    elif scenario == "invalid_credentials":
        username = f"invalid-{valid_username}"
        password = "invalid-password"

    elif scenario == "empty_username":
        username = ""
        password = valid_password

    else:  # empty_password
        username = valid_username
        password = ""

    # Act: Attempt authentication with the invalid credential combination.
    login_page.attempt_login(
        username=username,
        password=password,
    )

    # Assert: Authentication must not be established after a rejected login.
    login_page.should_not_be_authenticated()

    # Assert: Validate the specific WooCommerce validation message where the
    # user-facing contract has been confirmed by Playwright Codegen.
    if scenario == "empty_username":
        login_page.should_show_username_required_error()

    elif scenario == "empty_password":
        login_page.should_show_password_required_error()

    elif scenario == "invalid_username":
        login_page.should_show_invalid_username_error()

    else:
        # Invalid credential combinations must still render an authentication
        # error, even where the precise message is intentionally not asserted.
        login_page.should_show_login_error()
