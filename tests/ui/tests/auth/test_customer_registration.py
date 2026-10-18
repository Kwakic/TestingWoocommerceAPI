"""
Positive UI registration tests for WooCommerce customers.

These tests validate the customer self-registration happy path. Registration
UI mechanics remain encapsulated in CustomerRegistrationPage, while the test
verifies the resulting authenticated customer capability.
"""

import pytest
from playwright.sync_api import Page

from EcommerceAPI.src.test_data.builders.customers.customer_builder import (
    CustomerBuilder,
)
from tests.ui.pages.account.customer_account_page import CustomerAccountPage
from tests.ui.pages.authentication.customer_registration_page import (
    CustomerRegistrationPage,
)


pytestmark = [
    pytest.mark.ui,
    pytest.mark.smoke,
]


def test_customer_can_register_with_new_email(
    page: Page,
    ui_base_url: str,
    customer_resource_helper,
    ui_resources,
) -> None:
    """
    Verify that a new customer can successfully register through the UI.

    The customer is intentionally created by the UI because customer
    registration is the behavior under test.

    The generated email guarantees test isolation. After registration, the
    created customer is resolved through the API and registered with the UI
    resource owner so the customer is removed during UI test cleanup.
    """

    # Arrange: Generate unique registration data required by the UI contract.
    registration_data = CustomerBuilder().build()
    unique_email = registration_data["email"]

    # Arrange: Build the registration Page Object.
    registration_page = CustomerRegistrationPage(
        page=page,
        base_url=ui_base_url,
    )

    # Arrange: Open My Account and verify that registration is available.
    registration_page.open()
    registration_page.should_be_loaded()

    # Act: Create the customer through the real WooCommerce UI.
    registration_page.register(email=unique_email)

    # Arrange: Resolve the application resource created by the UI.
    created_customer = customer_resource_helper.get_customer_by_email(unique_email)

    # Ownership: The UI test created this customer, so the UI resource registry
    # owns its cleanup.
    ui_resources("customers", str(created_customer["id"]))

    # Assert: Registration should establish an authenticated customer session.
    account_page = CustomerAccountPage(page)
    account_page.should_be_loaded()
    account_page.should_be_authenticated()
