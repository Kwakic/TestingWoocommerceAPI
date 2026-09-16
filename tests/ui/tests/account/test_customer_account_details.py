"""
Positive and negative UI tests for the WooCommerce customer Account details
area.

These tests use Customer C, a dedicated mutable profile, so profile changes
cannot affect Customer A's stable checkout state.
"""

import pytest
from playwright.sync_api import Page

from tests.ui.pages.account.customer_account_details_page import (
    CustomerAccountDetailsPage,
)
from tests.ui.pages.account.customer_account_page import CustomerAccountPage


pytestmark = [
    pytest.mark.ui,
    pytest.mark.smoke,
]


def test_customer_can_update_account_details(
    profile_customer_page: Page,
) -> None:
    """
    Verify that Customer C can update their first and last name.

    The profile is intentionally separate from the stable checkout customer,
    so this test may mutate persisted account data safely.
    """
    # Arrange: Customer C is the mutable profile used by account-edit tests.
    account_page = CustomerAccountPage(profile_customer_page)
    account_page.should_be_loaded()
    account_page.should_be_authenticated()

    # Act: Open the Account details section.
    account_page.open_account_details()

    # Arrange: Build the Account details Page Object.
    account_details_page = CustomerAccountDetailsPage(profile_customer_page)
    account_details_page.should_be_loaded()

    # Arrange: Read Customer C's current persisted values so this test always
    # performs a real state transition, even when the test has run before.
    current_first_name = account_details_page.first_name_input.input_value()
    current_last_name = account_details_page.last_name_input.input_value()

    # Toggle between two valid values so the test can be repeated safely.
    new_first_name = "John" if current_first_name != "John" else "Jane"
    new_last_name = "Beck" if current_last_name != "Beck" else "Doe"

    # Act: Update Customer C's profile.
    account_details_page.update_profile(
        first_name=new_first_name,
        last_name=new_last_name,
    )

    # Act: Save the Account details changes.
    account_details_page.save_changes()

    # Assert: Verify WooCommerce confirms that the Account details were updated.
    account_details_page.should_show_account_details_saved_message()

    # Act: Reopen Account details to verify persistence.
    account_page.open_account_details()
    account_details_page.should_be_loaded()

    # Assert: Verify Customer C's updated profile values persisted.
    account_details_page.should_show_saved_profile(
        first_name=new_first_name,
        last_name=new_last_name,
    )


@pytest.mark.negative
def test_customer_cannot_save_account_details_without_required_names(
    profile_customer_page: Page,
) -> None:
    """
    Verify that Customer C cannot save Account details without required names.
    """
    # Arrange: Customer C is the dedicated mutable profile.
    account_page = CustomerAccountPage(profile_customer_page)
    account_page.should_be_loaded()
    account_page.should_be_authenticated()

    # Act: Open the Account details section.
    account_page.open_account_details()

    # Arrange: Build the Account details Page Object.
    account_details_page = CustomerAccountDetailsPage(profile_customer_page)
    account_details_page.should_be_loaded()

    # Act: Clear the required first-name and last-name fields.
    account_details_page.clear_required_name_fields()

    # Act: Submit the Account details form.
    account_details_page.save_changes()

    # Assert: Verify WooCommerce rejects the invalid update and reports both
    # required-field validation errors.
    account_details_page.should_show_required_name_validation()
