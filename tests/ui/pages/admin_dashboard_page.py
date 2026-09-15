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

    def should_be_loaded(self) -> None:
        """
        Verify that the authenticated WordPress administrator dashboard is open.
        """
        expect(self.page).to_have_url(f"{self.base_url.rstrip('/')}/wp-admin/")
        expect(self.dashboard_link).to_be_visible()
