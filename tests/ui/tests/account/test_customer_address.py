"""
Positive UI tests for WooCommerce customer shipping address management.

These tests use disposable customers provisioned through the API when a
customer is only a prerequisite for the UI behavior under test.

The shipping address itself is established through the UI because creating or
modifying the address is the behavior being verified.

The scenarios cover:

    Dynamic customer prerequisite
            ↓
    UI authentication
            ↓
    Shipping address state
            ↓
    Create or modify shipping address
            ↓
    Verify saved values
            ↓
    Verify persistence
"""

import pytest
from playwright.sync_api import Page, expect

from EcommerceAPI.src.test_data.builders.customers.customer_state_builder import (
    CustomerStateBuilder,
)
from EcommerceAPI.src.test_data.provisioning.customers.customer_state_provisioner import (
    CustomerStateProvisioner,
)
from tests.ui.data.models.customer_model import DynamicCustomer
from tests.ui.fixtures.customer_auth import login_customer
from tests.ui.pages.account.customer_account_page import CustomerAccountPage
from tests.ui.pages.account.customer_address_page import CustomerAddressPage


pytestmark = [
    pytest.mark.ui,
    pytest.mark.smoke,
]


def test_customer_can_save_shipping_address(
    page: Page,
    ui_base_url: str,
    dynamic_customer: DynamicCustomer,
) -> None:
    """
    Verify that a dynamically provisioned customer can create a shipping
    address through the My Account UI.

    The customer is created through the API as a disposable prerequisite.
    The shipping address itself is created through the UI because creating
    the address is the behavior under test.

    The customer's API ownership registration remains responsible for cleanup
    after the test finishes.
    """
    # Arrange: Build the Page Objects.
    account_page = CustomerAccountPage(page)
    address_page = CustomerAddressPage(
        page=page,
        base_url=ui_base_url,
    )

    # Arrange: Authenticate the dynamically provisioned customer.
    login_customer(
        page=page,
        ui_base_url=ui_base_url,
        username=dynamic_customer.username,
        password=dynamic_customer.password,
    )

    account_page.should_be_loaded()
    account_page.should_be_authenticated()

    # Act: Open the customer Addresses section.
    account_page.open_addresses()

    # Act: Open the shipping address form.
    address_page.open()
    address_page.should_be_loaded()

    # Act: Fill the customer's shipping address.
    address_page.fill_shipping_address(
        first_name="Mark",
        last_name="Twain",
        company="QA SDET Ltd",
        street_address="Calle Alguna",
        city="Alcobendas",
        zip_code="28109",
    )

    # Act: Select Spain from the WooCommerce country control.
    address_page.select_shipping_country("spa", "Spain")

    # Act: Select Madrid from the WooCommerce state control.
    address_page.select_shipping_state("madr", "Madrid")

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
    page: Page,
    ui_base_url: str,
    dynamic_customer: DynamicCustomer,
    customer_state_provisioner: CustomerStateProvisioner,
) -> None:
    """
    Verify that a customer can modify an existing shipping address and that
    the updated values persist after reloading the form.

    The customer is provisioned through the API as a disposable prerequisite.
    The initial shipping address is established through the API state-provisioning
    layer because address creation is not the behavior under test.

    The UI is responsible only for:
        - opening the existing shipping address;
        - modifying the selected fields;
        - saving the modification;
        - verifying the updated address;
        - verifying persistence after reload.

    The customer's API ownership registration remains responsible for cleanup.
    """

    # -----------------------------------------------------------------------
    # Arrange: Build the Page Objects required by the test.
    # -----------------------------------------------------------------------
    account_page = CustomerAccountPage(page)
    address_page = CustomerAddressPage(
        page=page,
        base_url=ui_base_url,
    )

    # -----------------------------------------------------------------------
    # Arrange: Authenticate the dynamically provisioned customer.
    # -----------------------------------------------------------------------
    login_customer(
        page=page,
        ui_base_url=ui_base_url,
        username=dynamic_customer.username,
        password=dynamic_customer.password,
    )

    account_page.should_be_loaded()
    account_page.should_be_authenticated()

    # -----------------------------------------------------------------------
    # Arrange: Build the initial shipping-address state required by the test.
    #
    # This is prerequisite state, not the behavior under test. Therefore it
    # belongs in the API test-data/state-provisioning layer rather than in the
    # UI flow.
    # -----------------------------------------------------------------------
    initial_shipping_state = (
        CustomerStateBuilder()
        .with_shipping(
            {
                "first_name": "Mark",
                "last_name": "Twain",
                "company": "QA SDET Ltd",
                "address_1": "Calle Alguna",
                "address_2": "",
                "city": "Alcobendas",
                "state": "M",
                "postcode": "28109",
                "country": "ES",
            }
        )
        .build()
    )

    # -----------------------------------------------------------------------
    # Arrange: Provision the initial shipping address through the API.
    #
    # The customer was already created by the dynamic_customer fixture.
    # CustomerStateProvisioner changes only the required shipping state.
    # API ownership remains responsible for customer cleanup.
    # -----------------------------------------------------------------------
    response = customer_state_provisioner.provision(
        customer_id=dynamic_customer.customer["id"],
        state=initial_shipping_state,
    )

    # The prerequisite must be successfully established before the UI test
    # begins exercising the behavior under test.
    assert response.status_code == 200, (
        "Initial shipping-address state provisioning failed. "
        f"Expected: 200, got {response.status_code}. "
        f"Response: {response.text}"
    )

    # -----------------------------------------------------------------------
    # Act: Open the customer Addresses section.
    # -----------------------------------------------------------------------
    account_page.open_addresses()

    # -----------------------------------------------------------------------
    # Act: Open the existing shipping address for editing.
    #
    # At this point the address already exists because it was provisioned
    # through the API. The UI test therefore starts directly at the behavior
    # under test.
    # -----------------------------------------------------------------------
    address_page.open_shipping_address()
    address_page.should_be_loaded()

    # -----------------------------------------------------------------------
    # Act: Modify the selected shipping-address fields.
    # -----------------------------------------------------------------------
    address_page.update_shipping_address(
        company="New company Ltd",
        street_address="C/Arriba",
        apartment="23",
    )

    # Diagnostic: verify that the UI fields contain the values we intend to save.
    expect(address_page.company_input).to_have_value("New company Ltd")
    expect(address_page.street_address_input).to_have_value("C/Arriba")
    expect(address_page.apartment_input).to_have_value("23")

    # -----------------------------------------------------------------------
    # Act: Save the modified shipping address.
    # -----------------------------------------------------------------------
    address_page.save_address()

    # -----------------------------------------------------------------------
    # Act: Open the customer Addresses summary page.
    # -----------------------------------------------------------------------
    address_page.open_addresses()

    # -----------------------------------------------------------------------
    # Assert: Verify that the modified shipping address is displayed.
    # -----------------------------------------------------------------------
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

    # -----------------------------------------------------------------------
    # Act: Reload the shipping address form to verify persistence.
    # -----------------------------------------------------------------------
    address_page.open()

    # -----------------------------------------------------------------------
    # Assert: Verify that the modified values persisted after reload.
    # -----------------------------------------------------------------------
    expect(address_page.company_input).to_have_value("New company Ltd")
    expect(address_page.street_address_input).to_have_value("C/Arriba")
    expect(address_page.apartment_input).to_have_value("23")
