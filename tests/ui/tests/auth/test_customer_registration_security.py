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

import pytest
from playwright.sync_api import Page

from tests.ui.data.models.customer_model import DynamicCustomer
from tests.ui.pages.authentication.customer_registration_page import (
    CustomerRegistrationPage,
)


pytestmark = [
    pytest.mark.ui,
    pytest.mark.security,
]


def test_customer_cannot_register_with_existing_email(
    page: Page,
    ui_base_url: str,
    dynamic_customer: DynamicCustomer,
) -> None:
    """
    Verify that an existing customer email cannot create another account.

    The customer is provisioned through the API as a disposable prerequisite.
    The test submits that existing email through the real WooCommerce
    registration form and verifies the duplicate-account error.
    """
    # -----------------------------------------------------------------------
    # Arrange: Use a dynamically provisioned customer as the existing identity.
    #
    # The customer is created through the API because customer creation is not
    # the behavior under test. API ownership remains responsible for cleanup.
    # -----------------------------------------------------------------------
    existing_email = dynamic_customer.customer["email"]

    # -----------------------------------------------------------------------
    # Arrange: Build the registration Page Object.
    # -----------------------------------------------------------------------
    registration_page = CustomerRegistrationPage(
        page=page,
        base_url=ui_base_url,
    )

    # -----------------------------------------------------------------------
    # Arrange: Open My Account and verify that registration is available.
    # -----------------------------------------------------------------------
    registration_page.open()
    registration_page.should_be_loaded()

    # -----------------------------------------------------------------------
    # Act: Attempt to register a second customer using the existing email.
    #
    # This is the behavior under test: the UI attempts to create another
    # account using an email that already belongs to an existing customer.
    # -----------------------------------------------------------------------
    registration_page.register(email=existing_email)

    # -----------------------------------------------------------------------
    # Assert: WooCommerce must reject the duplicate customer identity.
    # -----------------------------------------------------------------------
    registration_page.should_show_existing_email_error()
