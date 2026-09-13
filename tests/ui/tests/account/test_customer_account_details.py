"""
Positive and validation UI tests for the WooCommerce customer Account details area.

These tests validate the authenticated customer's Account details form through
the real My Account UI. The Page Object owns reusable form interactions and
UI verification, while the test owns the business scenario.
"""

import pytest
from playwright.sync_api import Page

from tests.ui.pages.customer_account_page import CustomerAccountPage
from tests.ui.pages.customer_account_details_page import CustomerAccountDetailsPage


pytestmark = [
    pytest.mark.ui,
    pytest.mark.smoke,
]


def test_customer_can_update_account_details(
    customer_page: Page,
) -> None:
    """
    Verify that an authenticated customer can update their first and last name.

    The scenario follows the recorded Playwright Codegen flow:
        authenticated customer
            -> Account details
            -> update first and last name
            -> save changes
            -> verify success message
            -> reopen Account details
            -> verify updated values persist
    """
    # Arrange: Build the account Page Object and confirm the customer is logged in.
    account_page = CustomerAccountPage(customer_page)
    account_page.should_be_loaded()
    account_page.should_be_authenticated()

    # Act: Open the Account details section.
    account_page.open_account_details()

    # Arrange: Build the Account details Page Object.
    account_details_page = CustomerAccountDetailsPage(customer_page)
    account_details_page.should_be_loaded()

    # Act: Update the customer's first and last name.
    account_details_page.update_profile(
        first_name="John",
        last_name="Beck",
    )

    # Act: Save the Account details changes.
    account_details_page.save_changes()

    # Assert: Verify WooCommerce confirms that the Account details were updated.
    account_details_page.should_show_account_details_saved_message()

    # Act: Reopen the Account details section to verify persistence.
    account_page.open_account_details()
    account_details_page.should_be_loaded()

    # Assert: Verify the updated profile values persisted.
    account_details_page.should_show_saved_profile(
        first_name="John",
        last_name="Beck",
    )


def test_customer_cannot_save_account_details_without_required_names(
    customer_page: Page,
) -> None:
    """
    Verify that required first-name and last-name fields are enforced.

    The scenario follows the recorded WooCommerce UI flow:
        authenticated customer
            -> Account details
            -> clear required name fields
            -> save changes
            -> verify validation errors
    """
    # Arrange: Build the account Page Object and confirm the customer is logged in.
    account_page = CustomerAccountPage(customer_page)
    account_page.should_be_loaded()
    account_page.should_be_authenticated()

    # Act: Open the Account details section.
    account_page.open_account_details()

    # Arrange: Build the Account details Page Object.
    account_details_page = CustomerAccountDetailsPage(customer_page)
    account_details_page.should_be_loaded()

    # Act: Clear the required first-name and last-name fields.
    account_details_page.clear_required_name_fields()

    # Act: Submit the Account details form.
    account_details_page.save_changes()

    # Assert: Verify WooCommerce rejects the invalid update and reports both
    # required-field validation errors.
    account_details_page.should_show_required_name_validation()
