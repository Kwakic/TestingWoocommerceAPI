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
    Authenticate a customer profile using environment-provided credentials.

    This is the single authentication implementation shared by all customer
    profile fixtures. Keeping the login workflow here prevents individual
    fixtures from duplicating credential validation and login-page handling.

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
    """Authenticate a customer using explicitly supplied credentials.

    This helper is intended for dynamically provisioned test customers whose
    credentials are held by ``TestCustomer`` rather than environment variables.
    The login workflow remains centralized in this module and uses the same
    customer login Page Object as the seeded customer profiles.
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

    ``customer_page`` represents the generic ``customer`` access role used
    by the UI role router. It is not a separate customer profile.

    The default identity behind this role is the dedicated checkout customer
    profile. Tests that require a specific customer profile should request
    that profile directly.

    This fixture keeps the distinction between access roles and customer
    profiles explicit:

        Role:
            customer

        Default profile:
            checkout_customer_page

    Args:
        checkout_customer_page: Authenticated default customer profile.

    Returns:
        Page: Authenticated page representing the customer access role.

    """
    return checkout_customer_page


@pytest.fixture
def checkout_customer_page(
    page: Page,
    ui_base_url: str,
) -> Page:
    """
    Provide the dedicated checkout customer profile.

    This profile uses the credentials defined by:

        UI_CUSTOMER_USERNAME
        UI_CUSTOMER_PASSWORD

    The profile is intended for customer checkout scenarios.

    The fixture only authenticates the account. It does not create or modify
    billing addresses, products, orders, or other application state.

    Tests that require specific customer state should establish that state
    explicitly as part of their own scenario.

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
    Provide the dedicated no-address customer profile.

    This profile uses:

        UI_CUSTOMER_NO_ADDRESS_USERNAME
        UI_CUSTOMER_NO_ADDRESS_PASSWORD

    The profile is intended for scenarios that need to exercise billing or
    shipping address entry.

    The fixture does not enforce the absence of an address. That state is a
    responsibility of the test environment and/or the scenario itself.

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
    Provide the dedicated customer profile used for account/profile tests.

    This profile uses:

        UI_CUSTOMER_PROFILE_USERNAME
        UI_CUSTOMER_PROFILE_PASSWORD

    It is intentionally isolated from the checkout customer so account
    modification tests can change customer information without affecting
    checkout scenarios.

    The fixture only authenticates the account. It does not establish or
    restore application state automatically.

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
