"""
Authentication-role fixtures for Playwright UI tests.

This module defines the UI access roles supported by the framework:

    guest
    customer
    admin

The role router provides a controlled way for parametrized tests to request
an access role without knowing the implementation or fixture name behind it.

Important architectural distinction:

    Role
        Describes the access level being exercised.

    Customer profile
        Describes the specific customer account used by a scenario.

For example:

    customer role
        -> checkout_customer_page
           or another explicitly requested customer profile

Customer profiles therefore must not be added to ``UI_ROLE_FIXTURES``.
"""

import pytest
from playwright.sync_api import Page


# ---------------------------------------------------------------------------
# UI access-role registry
# ---------------------------------------------------------------------------
#
# This registry contains ACCESS ROLES ONLY.
#
# It deliberately does not contain customer profiles such as:
#
#     checkout_customer
#     no_address_customer
#     profile_customer
#
# Those are test-data/profile concerns, not authorization roles.
#
# Keeping this mapping explicit gives the framework one controlled definition
# of the supported UI access roles and prevents parametrized tests from being
# coupled directly to implementation fixture names.
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

    Tests can use indirect parametrization to request a role without directly
    referencing the implementation fixture.

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
