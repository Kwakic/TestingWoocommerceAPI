"""
UI tests for the authenticated WooCommerce customer account area.

Each test authenticates a disposable API-provisioned customer so account
navigation tests do not depend on a shared seeded customer profile.
"""

import pytest
from playwright.sync_api import Page

from tests.ui.data.models.customer_model import DynamicCustomer
from tests.ui.fixtures.customer_auth import login_customer
from tests.ui.pages.account.customer_account_details_page import (
    CustomerAccountDetailsPage,
)
from tests.ui.pages.account.customer_account_page import CustomerAccountPage
from tests.ui.pages.account.customer_address_page import CustomerAddressPage


# These are critical authenticated customer flows suitable for smoke testing.
pytestmark = [
    pytest.mark.ui,
    pytest.mark.smoke,
]


def test_customer_account_contains_main_sections(
    page: Page,
    ui_base_url: str,
    dynamic_customer: DynamicCustomer,
) -> None:
    """
    Verify that a disposable API-provisioned customer can access the main My Account
    sections. API ownership handles customer cleanup.
    """
    # Arrange: Build the Page Object and authenticate this test's customer.
    account_page = CustomerAccountPage(page)
    login_customer(
        page=page,
        ui_base_url=ui_base_url,
        username=dynamic_customer.username,
        password=dynamic_customer.password,
    )

    # Assert: Verify that the My Account page is loaded and authenticated.
    account_page.should_be_loaded()
    account_page.should_be_authenticated()

    # Assert: Verify that the main customer account navigation is available.
    account_page.should_have_account_navigation()


def test_customer_can_navigate_to_addresses_and_account_details(
    page: Page,
    ui_base_url: str,
    dynamic_customer: DynamicCustomer,
) -> None:
    """
    Verify that a disposable API-provisioned customer can navigate to Addresses and
    Account details. API ownership handles customer cleanup.
    """
    # Arrange: Create the Page Objects required by the navigation flow.
    account_page = CustomerAccountPage(page)
    address_page = CustomerAddressPage(
        page=page,
        base_url=ui_base_url,
    )
    account_details_page = CustomerAccountDetailsPage(page)

    # Arrange: Authenticate the disposable customer.
    login_customer(
        page=page,
        ui_base_url=ui_base_url,
        username=dynamic_customer.username,
        password=dynamic_customer.password,
    )

    # Assert: Verify that the My Account page is loaded and authenticated.
    account_page.should_be_loaded()
    account_page.should_be_authenticated()

    # Act: Navigate to the Addresses section.
    account_page.open_addresses()

    # Assert: Verify that the Addresses summary page is displayed.
    address_page.should_be_addresses_page_loaded()

    # Act: Navigate back to My Account and open Account details.
    page.goto(
        f"{ui_base_url.rstrip('/')}/my-account/",
        wait_until="domcontentloaded",
    )
    account_page.open_account_details()

    # Assert: Verify that the Account details page is displayed.
    account_details_page.should_be_loaded()
