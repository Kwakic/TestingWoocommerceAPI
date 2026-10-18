"""Positive and negative UI tests for WooCommerce customer Account details.

Each test uses its own disposable API-provisioned customer so profile changes
are isolated and the tests can run safely in parallel with pytest-xdist.
"""

import pytest
from playwright.sync_api import Page

from tests.ui.data.models.customer_model import DynamicCustomer
from tests.ui.fixtures.customer_auth import login_customer
from tests.ui.pages.account.customer_account_details_page import (
    CustomerAccountDetailsPage,
)
from tests.ui.pages.account.customer_account_page import CustomerAccountPage


pytestmark = [
    pytest.mark.ui,
    pytest.mark.smoke,
]


def test_customer_can_update_account_details(
    page: Page,
    ui_base_url: str,
    dynamic_customer: DynamicCustomer,
) -> None:
    """
    Verify that a disposable customer can update their first and last name.

    The customer is provisioned through the API specifically for this test.
    The UI updates the profile, and API ownership handles customer cleanup.
    """
    # Arrange: Build the Page Objects.
    account_page = CustomerAccountPage(page)
    account_details_page = CustomerAccountDetailsPage(page)

    # Arrange: Authenticate the disposable customer.
    login_customer(
        page=page,
        ui_base_url=ui_base_url,
        username=dynamic_customer.username,
        password=dynamic_customer.password,
    )
    account_page.should_be_loaded()
    account_page.should_be_authenticated()

    # Act: Open the Account details section.
    account_page.open_account_details()
    account_details_page.should_be_loaded()

    # Arrange: Read the current values so the test always changes the profile.
    current_first_name = account_details_page.first_name_input.input_value()
    current_last_name = account_details_page.last_name_input.input_value()

    # Toggle between valid values to ensure a state transition.
    new_first_name = "John" if current_first_name != "John" else "Jane"
    new_last_name = "Beck" if current_last_name != "Beck" else "Doe"

    # Act: Update and save the customer's profile.
    account_details_page.update_profile(
        first_name=new_first_name,
        last_name=new_last_name,
    )
    account_details_page.save_changes()

    # Assert: Verify WooCommerce confirms that the details were updated.
    account_details_page.should_show_account_details_saved_message()

    # Act: Reopen Account details to verify persistence.
    account_page.open_account_details()
    account_details_page.should_be_loaded()

    # Assert: Verify the updated profile values persisted.
    account_details_page.should_show_saved_profile(
        first_name=new_first_name,
        last_name=new_last_name,
    )


@pytest.mark.negative
def test_customer_cannot_save_account_details_without_required_names(
    page: Page,
    ui_base_url: str,
    dynamic_customer: DynamicCustomer,
) -> None:
    """
    Verify that a disposable customer cannot save Account details without
    the required first and last names.
    """
    # Arrange: Build the Page Objects.
    account_page = CustomerAccountPage(page)
    account_details_page = CustomerAccountDetailsPage(page)

    # Arrange: Authenticate the disposable customer.
    login_customer(
        page=page,
        ui_base_url=ui_base_url,
        username=dynamic_customer.username,
        password=dynamic_customer.password,
    )
    account_page.should_be_loaded()
    account_page.should_be_authenticated()

    # Act: Open the Account details section.
    account_page.open_account_details()
    account_details_page.should_be_loaded()

    # Act: Clear the required first-name and last-name fields.
    account_details_page.clear_required_name_fields()

    # Act: Submit the Account details form.
    account_details_page.save_changes()

    # Assert: Verify WooCommerce rejects the update and reports both
    # required-field validation errors.
    account_details_page.should_show_required_name_validation()
