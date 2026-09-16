"""
Positive UI tests for WooCommerce customer shipping address management.

These tests use the dedicated no-address customer profile so that shipping
address scenarios are isolated from the stable checkout customer.

Each test establishes the state it requires through the UI rather than relying
on data created by another test or by a previous automated run.

The scenarios cover:

    Registered customer
            ↓
    Shipping address state
            ↓
    Create or modify shipping address
            ↓
    Verify saved values
            ↓
    Verify persistence
"""

import re

import pytest
from playwright.sync_api import Page, expect

from tests.ui.pages.account.customer_account_page import CustomerAccountPage
from tests.ui.pages.account.customer_address_page import CustomerAddressPage


pytestmark = [
    pytest.mark.ui,
    pytest.mark.smoke,
]


def test_customer_can_save_shipping_address(
    no_address_customer_page: Page,
    ui_base_url: str,
) -> None:
    """
    Verify that a customer without a saved shipping address can create one.

    The test uses the dedicated no-address customer profile and performs the
    complete address setup through the real My Account UI.
    """
    # Arrange: Confirm the dedicated no-address customer is authenticated.
    account_page = CustomerAccountPage(no_address_customer_page)
    account_page.should_be_loaded()
    account_page.should_be_authenticated()

    # Act: Open the customer Addresses section.
    account_page.open_addresses()

    # Arrange: Build the Page Object for the shipping address flow.
    address_page = CustomerAddressPage(
        page=no_address_customer_page,
        base_url=ui_base_url,
    )

    # Act: Open the shipping address form.
    address_page.open()
    address_page.should_be_loaded()

    # Act: Set the customer's shipping address.
    address_page.fill_shipping_address(
        first_name="Mark",
        last_name="Twain",
        company="QA SDET Ltd",
        street_address="Calle Alguna",
        city="Alcobendas",
        zip_code="28109",
    )

    # Act: Select Spain from the WooCommerce Select2 country control.
    no_address_customer_page.locator("#select2-shipping_country-container").click()
    no_address_customer_page.get_by_role("combobox").filter(
        has_text=re.compile(r"^$")
    ).fill("spa")
    no_address_customer_page.get_by_role("option", name="Spain").click()

    # Act: Select Madrid from the WooCommerce Select2 state control.
    no_address_customer_page.locator("#select2-shipping_state-container").click()
    no_address_customer_page.get_by_role("combobox").filter(
        has_text=re.compile(r"^$")
    ).fill("madr")
    no_address_customer_page.get_by_role("option", name="Madrid").click()

    # Act: Save the shipping address.
    address_page.save_address()

    # Act: Open the customer Addresses summary page.
    address_page.open_addresses()

    # Assert: Verify that the saved shipping address is displayed.
    address_page.should_show_shipping_address(
        first_name="Mark",
        last_name="Twain",
        company="QA SDET Ltd",
        street_address="Calle Alguna",
        apartment="",
        zip_code="28109",
        city="Alcobendas",
        state="Madrid",
        country="Spain",
    )


def test_customer_can_modify_shipping_address(
    no_address_customer_page: Page,
    ui_base_url: str,
) -> None:
    """
    Verify that a customer can modify an existing shipping address and that
    the updated values persist after reloading the form.

    The test first creates the required shipping address itself, ensuring
    that it does not depend on another test having run previously.
    """
    # Arrange: Confirm the dedicated no-address customer is authenticated.
    account_page = CustomerAccountPage(no_address_customer_page)
    account_page.should_be_loaded()
    account_page.should_be_authenticated()

    # Act: Open the customer Addresses section.
    account_page.open_addresses()

    # Arrange: Build the Page Object for the shipping address flow.
    address_page = CustomerAddressPage(
        page=no_address_customer_page,
        base_url=ui_base_url,
    )

    # -----------------------------------------------------------------------
    # Establish the initial state required by this test.
    # -----------------------------------------------------------------------

    # Act: Open the shipping address form.
    address_page.open()
    address_page.should_be_loaded()

    # Act: Create the initial shipping address used by the modification flow.
    address_page.fill_shipping_address(
        first_name="Mark",
        last_name="Twain",
        company="QA SDET Ltd",
        street_address="Calle Alguna",
        city="Alcobendas",
        zip_code="28109",
    )

    # Act: Select Spain from the WooCommerce Select2 country control.
    no_address_customer_page.locator("#select2-shipping_country-container").click()
    no_address_customer_page.get_by_role("combobox").filter(
        has_text=re.compile(r"^$")
    ).fill("spa")
    no_address_customer_page.get_by_role("option", name="Spain").click()

    # Act: Select Madrid from the WooCommerce Select2 state control.
    no_address_customer_page.locator("#select2-shipping_state-container").click()
    no_address_customer_page.get_by_role("combobox").filter(
        has_text=re.compile(r"^$")
    ).fill("madr")
    no_address_customer_page.get_by_role("option", name="Madrid").click()

    # Act: Save the initial shipping address.
    address_page.save_address()

    # -----------------------------------------------------------------------
    # Modify the address established above.
    # -----------------------------------------------------------------------

    # Act: Open the existing shipping address for editing.
    # The Page Object selects the shipping Edit link specifically because the
    # Addresses page also contains a separate Billing Edit link.
    address_page.open_shipping_address()
    address_page.should_be_loaded()

    # Act: Update selected shipping address fields.
    address_page.update_shipping_address(
        company="New company Ltd",
        street_address="C/Arriba",
        apartment="23",
    )

    # Act: Save the modified shipping address.
    address_page.save_address()

    # Act: Open the customer Addresses summary page.
    address_page.open_addresses()

    # Assert: Verify that the updated shipping address is displayed.
    address_page.should_show_shipping_address(
        first_name="Mark",
        last_name="Twain",
        company="New company Ltd",
        street_address="C/Arriba",
        apartment="23",
        zip_code="28109",
        city="Alcobendas",
        state="Madrid",
        country="Spain",
    )

    # Act: Reload the shipping address form to verify persistence.
    address_page.open()

    # Assert: Verify that the updated values persisted after reload.
    expect(address_page.company_input).to_have_value("New company Ltd")
    expect(address_page.street_address_input).to_have_value("C/Arriba")
    expect(address_page.apartment_input).to_have_value("23")
