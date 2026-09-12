"""
Positive UI tests for WooCommerce customer account management.

These tests validate the authenticated My Account area and navigation to the
main customer account sections. Detailed address and account-details flows are
covered separately.
"""

import pytest
from playwright.sync_api import Page, expect

from tests.ui.pages.customer_account_page import CustomerAccountPage


pytestmark = [
    pytest.mark.ui,
    pytest.mark.smoke,
]


def test_customer_account_contains_main_sections(
    customer_page: Page,
) -> None:
    """
    Verify that an authenticated customer can see the main My Account sections.
    """
    # Arrange: Build the Page Object for the authenticated My Account area.
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
    Verify that an authenticated customer can access Addresses and
    Account details from the My Account navigation.
    """
    # Arrange: Build the Page Object for the authenticated My Account area.
    account_page = CustomerAccountPage(customer_page)

    # Assert: Confirm that the authenticated My Account page is available.
    account_page.should_be_loaded()
    account_page.should_be_authenticated()

    # Act: Navigate to the customer Addresses section.
    account_page.open_addresses()

    # Assert: Verify the Addresses page is displayed.
    addresses_heading = customer_page.get_by_role(
        "heading",
        name="Addresses",
        exact=True,
    )
    expect(addresses_heading).to_be_visible()

    # Act: Return to My Account and navigate to Account details.
    customer_page.goto(
        f"{ui_base_url.rstrip('/')}/my-account/",
        wait_until="domcontentloaded",
    )
    account_page.open_account_details()

    # Assert: Verify the Account details page is displayed.
    account_details_heading = customer_page.get_by_role(
        "heading",
        name="Account details",
        exact=True,
    )
    expect(account_details_heading).to_be_visible()
