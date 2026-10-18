"""
UI authentication and authorization tests for WordPress administrator access.

These tests validate administrator authentication and role-based access to
the WordPress Dashboard at the business level.

Authentication mechanics remain in the role fixtures and Page Objects.
"""

import pytest
from playwright.sync_api import Page

from tests.ui.data.models.customer_model import DynamicCustomer
from tests.ui.fixtures.customer_auth import login_customer
from tests.ui.pages.account.customer_account_page import CustomerAccountPage
from tests.ui.pages.admin.admin_dashboard_page import AdminDashboardPage


@pytest.mark.ui
@pytest.mark.smoke
def test_admin_can_access_wordpress_dashboard(
    admin_page: Page,
    ui_base_url: str,
) -> None:
    """
    Verify that the dedicated UI administrator can access WordPress Dashboard.

    The ``admin_page`` fixture owns administrator authentication. This test
    therefore validates the resulting authenticated capability rather than
    duplicating login selectors or credential handling.
    """
    # Arrange: Build the Page Object for the authenticated administrator dashboard.
    dashboard_page = AdminDashboardPage(
        page=admin_page,
        base_url=ui_base_url,
    )

    # Assert: Verify that WordPress administrator access was established.
    dashboard_page.should_have_admin_access()


@pytest.mark.ui
@pytest.mark.smoke
@pytest.mark.security
def test_customer_cannot_access_wordpress_dashboard(
    page: Page,
    dynamic_customer: DynamicCustomer,
    ui_base_url: str,
) -> None:
    """
    Verify that an authenticated WooCommerce customer cannot access
    the WordPress administrator dashboard.

    Flow:
        authenticated customer
            -> /wp-admin/
            -> administrator access denied
            -> remains outside WordPress admin
    """
    # Arrange: Authenticate a per-test customer created through the REST API.
    login_customer(
        page=page,
        ui_base_url=ui_base_url,
        username=dynamic_customer.username,
        password=dynamic_customer.password,
    )
    account_page = CustomerAccountPage(page)
    account_page.should_be_authenticated()

    dashboard_page = AdminDashboardPage(
        page=page,
        base_url=ui_base_url,
    )

    # Act: Attempt to access the WordPress administrator dashboard.
    dashboard_page.open()

    # Assert: The customer is redirected away from the WordPress admin area.
    assert "/wp-admin/" not in page.url

    # Assert: Denied admin access does not log the customer out.
    account_page.should_be_authenticated()
