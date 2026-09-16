"""
Page Object for the WordPress administrator dashboard.
"""

from playwright.sync_api import Page, expect


class AdminDashboardPage:
    """
    Represent the authenticated WordPress administrator dashboard.

    The Page Object encapsulates dashboard-level verification without exposing
    Playwright selectors directly to the test layer.
    """

    def __init__(self, page: Page, base_url: str) -> None:
        """
        Initialize the administrator dashboard Page Object.

        Args:
            page: Playwright Page associated with the authenticated admin
                browser context.
            base_url: Storefront base URL.
        """
        self.page = page
        self.base_url = base_url

        # The recorded admin flow exposes "Dashboard" as the primary
        # administrator navigation entry.
        self.dashboard_link = page.get_by_role(
            "link",
            name="Dashboard",
            exact=True,
        )

    def open(self) -> None:
        """Navigate directly to the WordPress administrator dashboard."""
        self.page.goto(
            f"{self.base_url.rstrip('/')}/wp-admin/",
            wait_until="domcontentloaded",
        )

    def should_have_admin_access(self) -> None:
        """
        Verify that the current user has access to the WordPress administrator
        dashboard.

        This assertion verifies both the administrator URL and the presence
        of the Dashboard navigation entry. Keeping these checks in the Page
        Object prevents tests from exposing Playwright selectors directly.
        """
        expect(self.page).to_have_url(f"{self.base_url.rstrip('/')}/wp-admin/")
        expect(self.dashboard_link).to_be_visible()

    def should_not_have_admin_access(self) -> None:
        """
        Verify that the current user does not have access to the WordPress
        administrator dashboard.

        This assertion intentionally verifies the access boundary rather than
        a specific redirect destination. The application may redirect a
        non-administrator to different pages depending on its configuration,
        but the user must not remain on the WordPress administrator dashboard.
        """
        expect(self.page).not_to_have_url(f"{self.base_url.rstrip('/')}/wp-admin/")
        expect(self.dashboard_link).not_to_be_visible()
