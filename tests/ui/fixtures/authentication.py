"""
Authentication-role fixtures for Playwright UI tests.

This module defines the UI access roles supported by the framework:

    guest
    customer
    admin

The role router provides a controlled way for parametrized tests to request
an access role without knowing the implementation or fixture name behind it.

Use ``ui_role_page`` when a test should select an access role (guest, customer,
or admin), especially when the same behavior is intentionally parametrized
across roles. The router only resolves a role to a page fixture; it does not
create test data.

For most customer tests that need a fresh customer as a prerequisite, request
the ``dynamic_customer`` fixture separately and authenticate it with
``login_customer``. ``dynamic_customer`` is a test-data provisioning fixture,
not an access role, so it must not be added to ``UI_ROLE_FIXTURES``.

Important architectural distinction:

    Role
        Describes the access level being exercised.

    Customer profile
        Describes the specific customer account used by a scenario.

For example:

    customer role
        -> checkout_customer_page
           or another explicitly requested customer profile

Customer profiles and data-provisioning fixtures (including
``dynamic_customer``) therefore must not be added to ``UI_ROLE_FIXTURES``.
"""

import pytest
from playwright.sync_api import Page


# ---------------------------------------------------------------------------
# UI access-role registry
# ---------------------------------------------------------------------------
#
# This registry contains ACCESS ROLES ONLY.
#
# The keys are the values a test passes indirectly to ``ui_role_page``; the
# values are the pytest fixture names that provide the matching browser page.
# Use it when selecting an access role, for example:
#
#     @pytest.mark.parametrize(
#         "ui_role_page",
#         ["guest"],
#         indirect=True,
#     )
#
# ``customer`` currently resolves to ``customer_page``, which authenticates
# the configured checkout-customer profile. It does NOT create a new customer.
#
# Do not add customer profiles (checkout_customer, no_address_customer,
# profile_customer) or test-data fixtures such as ``dynamic_customer`` here.
# For a fresh customer prerequisite, request ``dynamic_customer`` directly in
# the test and use ``login_customer`` with its credentials.
#
# Add a registry entry only when introducing a new access role and its role
# fixture. Keeping this mapping explicit prevents tests from depending on
# implementation fixture names.
# ---------------------------------------------------------------------------

UI_ROLE_FIXTURES = {
    "guest": "guest_page",
    "customer": "customer_page",
    "admin": "admin_page",
}


@pytest.fixture
def guest_page(page: Page) -> Page:
    """
    Provide a page representing an unauthenticated guest user.

    The fixture intentionally performs no authentication. The page inherits
    the isolated Browser Context created by the generic browser fixtures.

    Args:
        page: Fresh Playwright page belonging to the current test.

    Returns:
        Page: Unauthenticated storefront page.

    """
    return page


@pytest.fixture
def ui_role_page(
    request: pytest.FixtureRequest,
    browser_name: str,
) -> Page:
    """
    Provide a Playwright page for the requested UI access role.

    Tests can use indirect parametrization to request an access role without
    directly referencing the implementation fixture.

    Use this router when role selection is part of the test design. It only
    selects the page fixture; it does not create customers or other test data.
    For a fresh API-created customer, request ``dynamic_customer`` separately
    and authenticate with ``login_customer``.

    Example:

        @pytest.mark.parametrize(
            "ui_role_page",
            ["guest", "customer", "admin"],
            indirect=True,
        )

    Supported roles:

        guest
        customer
        admin

    ``browser_name`` is intentionally declared even though its value is not
    used. pytest-playwright uses declared browser dependencies during
    collection to determine browser parametrization. Keeping the dependency
    visible ensures role-routed tests participate correctly in multi-browser
    execution.

    Args:
        request: Pytest fixture request containing the indirect role value.
        browser_name: Browser name supplied by pytest-playwright.

    Returns:
        Page: Page configured for the requested access role.

    Raises:
        ValueError: If the requested role is not supported.

    """
    # The value is intentionally unused. The fixture dependency itself is
    # required so pytest-playwright can detect browser parametrization during
    # test collection.
    _ = browser_name

    role = request.param

    try:
        fixture_name = UI_ROLE_FIXTURES[role]
    except KeyError as exc:
        supported_roles = ", ".join(sorted(UI_ROLE_FIXTURES))
        raise ValueError(
            f"Unsupported UI role '{role}'. " f"Supported roles: {supported_roles}"
        ) from exc

    return request.getfixturevalue(fixture_name)
