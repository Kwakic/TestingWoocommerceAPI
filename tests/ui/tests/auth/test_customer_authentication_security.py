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

import os

import pytest
from playwright.sync_api import Page

from tests.ui.pages.customer_login_page import CustomerLoginPage

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
    scenario: str,
) -> None:
    """
    Verify that invalid customer credentials cannot establish authentication.

    The valid customer credentials are read from the environment so the test
    can exercise realistic negative combinations without hard-coding secrets
    or exposing passwords in parametrized test IDs.
    """
    # Arrange: Load the configured dedicated customer credentials.
    valid_username = os.getenv("UI_CUSTOMER_USERNAME")
    valid_email = os.getenv("UI_CUSTOMER_EMAIL")
    valid_password = os.getenv("UI_CUSTOMER_PASSWORD")

    missing_credentials = [
        name
        for name, value in (
            ("UI_CUSTOMER_USERNAME", valid_username),
            ("UI_CUSTOMER_EMAIL", valid_email),
            ("UI_CUSTOMER_PASSWORD", valid_password),
        )
        if not value
    ]

    if missing_credentials:
        raise pytest.UsageError(
            "Missing required UI customer credentials: "
            + ", ".join(missing_credentials)
        )

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
