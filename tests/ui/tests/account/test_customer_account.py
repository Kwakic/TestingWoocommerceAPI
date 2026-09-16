"""
UI tests for the authenticated WooCommerce customer account area.

These tests verify that a customer can access the My Account page and navigate
to the main account sections.
"""

import pytest
from playwright.sync_api import Page

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
    customer_page: Page,
) -> None:
    """
    Verify that an authenticated customer can access the main My Account
    sections.
    """
    # Arrange: Create the Page Object for the authenticated customer account.
    account_page = CustomerAccountPage(customer_page)

    # Assert: Verify that the My Account page is loaded and authenticated.
    account_page.should_be_loaded()
    account_page.should_be_authenticated()

    # Assert: Verify that the main customer account navigation is available.
    account_page.should_have_account_navigation()


def test_customer_can_navigate_to_addresses_and_account_details(
    customer_page: Page,
    ui_base_url: str,
) -> None:
    """
    Verify that an authenticated customer can navigate to Addresses and
    Account details from the My Account page.
    """
    # Arrange: Create the Page Objects required by the navigation flow.
    account_page = CustomerAccountPage(customer_page)
    address_page = CustomerAddressPage(
        page=customer_page,
        base_url=ui_base_url,
    )

    # Assert: Verify that the My Account page is loaded and authenticated.
    account_page.should_be_loaded()
    account_page.should_be_authenticated()

    # Act: Navigate to the Addresses section.
    account_page.open_addresses()

    # Assert: Verify that the Addresses summary page is displayed.
    address_page.should_be_addresses_page_loaded()

    # Act: Navigate back to My Account and open Account details.
    customer_page.goto(
        f"{ui_base_url.rstrip('/')}/my-account/",
        wait_until="domcontentloaded",
    )
    account_page.open_account_details()

    # Assert: Verify that the Account details page is displayed.
    account_details_page = CustomerAccountDetailsPage(customer_page)
    account_details_page.should_be_loaded()
