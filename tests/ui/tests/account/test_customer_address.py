"""
Positive UI tests for WooCommerce customer shipping address management.

These tests validate that an authenticated customer can save and modify a
shipping address through the real My Account UI. The Page Object owns the
reusable address form interactions, while the test owns the business scenario.

The flow is:

    Registered customer
            ↓
    No shipping address
            ↓
    Create shipping address
            ↓
    Verify address exists
            ↓
    Modify shipping address
            ↓
    Verify modification
"""

import re

import pytest
from playwright.sync_api import Page, expect

from tests.ui.pages.customer_account_page import CustomerAccountPage
from tests.ui.pages.customer_address_page import CustomerAddressPage


pytestmark = [
    pytest.mark.ui,
    pytest.mark.smoke,
]


def test_customer_can_save_shipping_address(
    customer_page: Page,
    ui_base_url: str,
) -> None:
    """
    Verify that an authenticated customer can save a shipping address.

    The scenario uses a realistic Spanish address and verifies that the saved
    address is displayed in the customer's Addresses summary.
    """
    # Arrange: Build the account Page Object and confirm the customer is logged in.
    account_page = CustomerAccountPage(customer_page)
    account_page.should_be_loaded()
    account_page.should_be_authenticated()

    # Act: Open the customer Addresses section.
    account_page.open_addresses()

    # Arrange: Build the address Page Object for the shipping address flow.
    address_page = CustomerAddressPage(
        page=customer_page,
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
    customer_page.locator("#select2-shipping_country-container").click()
    customer_page.get_by_role("combobox").filter(has_text=re.compile(r"^$")).fill("spa")
    customer_page.get_by_role("option", name="Spain").click()

    # Act: Select Madrid from the WooCommerce Select2 state control.
    customer_page.locator("#select2-shipping_state-container").click()
    customer_page.get_by_role("combobox").filter(has_text=re.compile(r"^$")).fill(
        "madr"
    )
    customer_page.get_by_role("option", name="Madrid").click()

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
    customer_page: Page,
    ui_base_url: str,
) -> None:
    """
    Verify that an authenticated customer can modify an existing shipping
    address and that the updated values persist after reloading the form.
    """
    # Arrange: Build the account Page Object and confirm the customer is logged in.
    account_page = CustomerAccountPage(customer_page)
    account_page.should_be_loaded()
    account_page.should_be_authenticated()

    # Act: Open the customer Addresses section.
    account_page.open_addresses()

    # Act: Open the existing shipping address for editing.
    edit_link = customer_page.get_by_role(
        "link",
        name="Edit",
        exact=True,
    )
    edit_link.click()
    customer_page.wait_for_load_state("domcontentloaded")

    # Arrange: Build the address Page Object for the shipping address flow.
    address_page = CustomerAddressPage(
        page=customer_page,
        base_url=ui_base_url,
    )
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
