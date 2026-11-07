"""
Customer authentication and customer-profile fixtures.

This module provides fixtures for authenticated WooCommerce customer
profiles.

The framework distinguishes between:

    Access role:
        customer

    Customer profile:
        checkout_customer
        no_address_customer
        profile_customer

A customer profile represents a dedicated test account used for a particular
testing purpose. A profile is not an access role.

Authentication credentials are supplied through environment variables and are
never hard-coded in the test suite.

Design principles:

    - Authentication implementation is centralized in one helper.
    - Customer credentials come from environment variables.
    - Tests consume authenticated Playwright pages rather than performing
      login themselves.
    - Customer profiles remain separate so one scenario can mutate its account
      state without affecting another profile.
    - Customer profile fixtures do not create or seed application data.
      Scenario-specific state should be established by the E2E test when
      appropriate.
"""

import os
from collections.abc import Callable

import pytest
from playwright.sync_api import Page

from tests.ui.pages.authentication.customer_login_page import CustomerLoginPage

from EcommerceAPI.src.test_data.builders.customers.customer_builder import (
    CustomerBuilder,
)

from tests.ui.data.models.customer_model import DynamicCustomer


def _login_customer(
    page: Page,
    ui_base_url: str,
    username_env: str,
    password_env: str,
    profile_name: str,
) -> Page:
    """
    Authenticate a seeded customer profile from environment variables.

    This internal helper is called by the profile fixtures below, such as
    ``checkout_customer_page`` and ``no_address_customer_page``. Pass the
    environment variable names for that profile's username and password.
    The helper validates those values, adds the profile name to any missing-
    credential error, and performs the shared Page Object login flow.

    Tests that already have credentials (for example, from a dynamically
    created customer) should call the public ``login_customer`` helper instead.

    Args:
        page: Fresh Playwright page belonging to an isolated Browser Context.
        ui_base_url: Storefront base URL for the active UI environment.
        username_env: Environment variable containing the profile username.
        password_env: Environment variable containing the profile password.
        profile_name: Human-readable profile name used in error messages.

    Returns:
        Page: The same page after successful customer authentication.

    Raises:
        pytest.UsageError: If one or more required credentials are missing.

    """
    username = os.getenv(username_env)
    password = os.getenv(password_env)

    missing_credentials = [
        name
        for name, value in (
            (username_env, username),
            (password_env, password),
        )
        if not value
    ]

    if missing_credentials:
        raise pytest.UsageError(
            f"Missing credentials for {profile_name}: " + ", ".join(missing_credentials)
        )

    login_page = CustomerLoginPage(
        page=page,
        base_url=ui_base_url,
    )

    login_page.login(
        username=username,
        password=password,
    )

    return page


def login_customer(
    page: Page,
    ui_base_url: str,
    username: str,
    password: str,
) -> Page:
    """Authenticate a page using credentials supplied by the test.

    Use this public helper when the test already has a customer's username
    and password, commonly from a dynamically created customer returned by
    ``dynamic_customer`` or ``dynamic_customer_factory``. It performs the
    shared ``CustomerLoginPage`` login flow and returns the authenticated
    page. Seeded profile fixtures should use the internal ``_login_customer``
    helper instead, since their credentials are read from environment variables.
    """
    assert username, "Customer username is required for UI authentication."
    assert password, "Customer password is required for UI authentication."

    login_page = CustomerLoginPage(
        page=page,
        base_url=ui_base_url,
    )
    login_page.login(
        username=username,
        password=password,
    )

    return page


@pytest.fixture(scope="function")
def dynamic_customer_factory(create_valid_customer) -> Callable[..., DynamicCustomer]:
    """Create disposable customers with optional data for a test scenario.

    Use this factory when a UI test needs a customer to start with specific
    data, such as a shipping address. The data is included in the customer
    creation request, so the test does not need a second API call to prepare
    that initial state.

    Customer creation, response validation, and cleanup registration remain
    the responsibility of ``create_valid_customer``. This factory only keeps
    the returned customer together with the password needed for UI login.

    Example:
        customer = dynamic_customer_factory(shipping={...})

    Returns:
        A callable that creates a ``DynamicCustomer`` using optional customer
        fields supported by the customer creation API.
    """

    def _create_customer(**customer_fields) -> DynamicCustomer:
        # Keep the generated password: WooCommerce does not return it in the
        # customer response, but the UI test needs it to log in.
        customer_data = CustomerBuilder().with_fields(**customer_fields).build()

        # Reuse the API fixture so validation and cleanup stay centralized.
        customer = create_valid_customer(**customer_data)

        username = customer.get("username")
        assert username, (
            "Dynamic customer creation succeeded, but WooCommerce did not "
            "return a username required for UI authentication."
        )

        return DynamicCustomer(
            customer=customer,
            username=username,
            password=customer_data["password"],
        )

    return _create_customer


@pytest.fixture(scope="function")
def dynamic_customer(
    dynamic_customer_factory,
) -> DynamicCustomer:
    """Create a disposable customer with default valid data.

    Use this fixture when a UI test needs a fresh customer but does not need
    to provide any special fields at creation time. Tests that need initial
    customer data can use ``dynamic_customer_factory`` instead.
    """
    return dynamic_customer_factory()


@pytest.fixture
def customer_page(checkout_customer_page: Page) -> Page:
    """
    Provide the default authenticated customer access role.

    The default identity is Customer A, the dedicated checkout customer
    profile. This fixture is an alias for ``checkout_customer_page``.

    Customer A is provisioned by ``seed_test_users.sh``:
        - The account is created using WP-CLI if it does not exist.
        - Billing and shipping addresses are configured using WC_Customer.

    See:
        scripts/seed_test_users.sh

    The fixture only provides authenticated access. It does not create
    or modify the customer account or its application data.
    """
    return checkout_customer_page


@pytest.fixture
def checkout_customer_page(
    page: Page,
    ui_base_url: str,
) -> Page:
    """
    Provide the dedicated checkout customer profile (Customer A).

    Provisioning:
        The customer account and baseline addresses are provisioned by
        ``scripts/seed_test_users.sh`` during environment setup.

        The seed script:
            - Creates the WooCommerce customer using WP-CLI.
            - Configures the billing and shipping addresses using WC_Customer.
            - Uses environment-provided credentials.

    Credentials:
        UI_CUSTOMER_USERNAME
        UI_CUSTOMER_PASSWORD

    This fixture only authenticates the existing account. It does not
    create the customer or provision its addresses.

    Tests requiring different initial customer states should use the
    appropriate customer profile or dynamic customer fixtures.

    Args:
        page: Fresh page belonging to the test's isolated Browser Context.
        ui_base_url: Storefront base URL for the active UI environment.

    Returns:
        Page: Authenticated checkout-customer page.
    """
    return _login_customer(
        page=page,
        ui_base_url=ui_base_url,
        username_env="UI_CUSTOMER_USERNAME",
        password_env="UI_CUSTOMER_PASSWORD",
        profile_name="checkout customer profile",
    )


@pytest.fixture
def no_address_customer_page(
    page: Page,
    ui_base_url: str,
) -> Page:
    """
    Provide the dedicated no-address customer profile (Customer B).

    Provisioning:
        The customer account is provisioned by
        ``scripts/seed_test_users.sh`` during environment setup.

        The seed script creates the WooCommerce customer using WP-CLI if the
        account does not already exist.

    Credentials:
        UI_CUSTOMER_NO_ADDRESS_USERNAME
        UI_CUSTOMER_NO_ADDRESS_PASSWORD

    The profile is intended for scenarios that need to exercise billing or
    shipping address entry.

    Important:
        The fixture only authenticates the existing account. It does not
        create the customer or guarantee that the account has no saved
        addresses. The no-address state must be established by the seed
        script or the test environment.

    Args:
        page: Fresh page belonging to the test's isolated Browser Context.
        ui_base_url: Storefront base URL for the active UI environment.

    Returns:
        Page: Authenticated no-address-customer page.
    """
    return _login_customer(
        page=page,
        ui_base_url=ui_base_url,
        username_env="UI_CUSTOMER_NO_ADDRESS_USERNAME",
        password_env="UI_CUSTOMER_NO_ADDRESS_PASSWORD",
        profile_name="no-address customer profile",
    )


@pytest.fixture
def profile_customer_page(
    page: Page,
    ui_base_url: str,
) -> Page:
    """
    Provide the dedicated account/profile test customer (Customer C).

    Provisioning:
        The customer account is provisioned by
        ``scripts/seed_test_users.sh`` during environment setup.

        The seed script creates the WooCommerce customer using WP-CLI if the
        account does not already exist.

    Credentials:
        UI_CUSTOMER_PROFILE_USERNAME
        UI_CUSTOMER_PROFILE_PASSWORD

    This profile is intentionally isolated from Customer A (the checkout
    customer) so account modification tests can change customer information
    without affecting checkout scenarios.

    The fixture only authenticates the existing account. It does not create
    the customer or establish/restore application state automatically.

    Args:
        page: Fresh page belonging to the test's isolated Browser Context.
        ui_base_url: Storefront base URL for the active UI environment.

    Returns:
        Page: Authenticated profile-customer page.
    """
    return _login_customer(
        page=page,
        ui_base_url=ui_base_url,
        username_env="UI_CUSTOMER_PROFILE_USERNAME",
        password_env="UI_CUSTOMER_PROFILE_PASSWORD",
        profile_name="account profile customer",
    )
