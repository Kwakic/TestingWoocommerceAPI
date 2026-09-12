"""
Positive UI registration tests for WooCommerce customers.

These tests validate the customer self-registration happy path. Registration
UI mechanics remain encapsulated in CustomerRegistrationPage, while the test
verifies the resulting authenticated customer capability.
"""

import pytest
from playwright.sync_api import Page

from EcommerceAPI.src.utils.generic_utilities import generate_random_email_and_password

from tests.ui.pages.customer_account_page import CustomerAccountPage
from tests.ui.pages.customer_registration_page import CustomerRegistrationPage


pytestmark = [
    pytest.mark.ui,
    pytest.mark.smoke,
]


def test_customer_can_register_with_new_email(
    page: Page,
    ui_base_url: str,
) -> None:
    """
    Verify that a new customer can successfully register from My Account.

    A unique email address is generated using the framework's shared utility
    so the happy-path test does not depend on a pre-existing account or
    conflict with a customer created by a previous local run.

    The current WooCommerce configuration generates the customer username
    automatically and sends a password setup link after registration.
    """
    # Arrange: Build the registration and authenticated account Page Objects.
    registration_page = CustomerRegistrationPage(
        page=page,
        base_url=ui_base_url,
    )

    # Arrange: Generate a unique email using the framework's shared utility.
    credentials = generate_random_email_and_password(
        email_prefix="ui-registration",
    )
    unique_email = credentials["email"]

    # Arrange: Open My Account and confirm that registration is available.
    registration_page.open()
    registration_page.should_be_loaded()

    # Act: Submit a new customer registration through the real UI.
    registration_page.register(email=unique_email)

    # Assert: Verify that registration resulted in an authenticated customer
    # session with access to the My Account area.
    account_page = CustomerAccountPage(page)
    account_page.should_be_loaded()
    account_page.should_be_authenticated()
