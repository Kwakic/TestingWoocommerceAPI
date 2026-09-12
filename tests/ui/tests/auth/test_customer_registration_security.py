"""
Negative UI registration-security tests for WooCommerce customers.

These tests validate that an existing customer email cannot be used to create
another customer account.

The current WooCommerce registration form accepts an email address and
generates the customer username automatically. Therefore, registration
uniqueness is validated at the email level rather than through a separate
username field.

Covered scenarios:
    - existing customer email cannot be registered again
"""

import os

import pytest
from playwright.sync_api import Page

from tests.ui.pages.customer_registration_page import CustomerRegistrationPage


pytestmark = [
    pytest.mark.ui,
    pytest.mark.security,
]


def test_customer_cannot_register_with_existing_email(
    page: Page,
    ui_base_url: str,
) -> None:
    """
    Verify that an existing customer email cannot create another account.

    The dedicated UI customer's email is supplied through the execution
    environment. The test submits that existing identity through the real
    WooCommerce registration form and verifies the duplicate-account error.
    """
    # Arrange: Load the existing customer email from the execution environment.
    existing_email = os.getenv("UI_CUSTOMER_EMAIL")

    if not existing_email:
        raise pytest.UsageError("UI_CUSTOMER_EMAIL is not configured.")

    registration_page = CustomerRegistrationPage(
        page=page,
        base_url=ui_base_url,
    )

    # Arrange: Open the My Account page containing the registration form.
    registration_page.open()

    # Assert: Confirm that the registration form is available in this
    # environment before attempting the duplicate-account scenario.
    registration_page.should_be_loaded()

    # Act: Attempt to register a second customer using the existing email.
    registration_page.register(email=existing_email)

    # Assert: WooCommerce must reject the duplicate customer identity.
    registration_page.should_show_existing_email_error()
