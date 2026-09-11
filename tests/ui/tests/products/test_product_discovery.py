"""
UI tests for storefront product discovery.

These scenarios currently validate guest product discovery. Role selection is
handled consistently through the indirect UI role fixture.
"""

import pytest
from playwright.sync_api import Page

from tests.ui.pages.home_page import HomePage


pytestmark = [
    pytest.mark.ui,
    # pytest.mark.smoke,
]


@pytest.mark.parametrize(
    "ui_role_page",
    [
        pytest.param("guest", id="guest"),
        # pytest.param("customer", id="customer"),
        # pytest.param("admin", id="admin"),
    ],
    indirect=True,
)
def test_guest_can_open_product(
    ui_role_page: Page,
    ui_base_url: str,
) -> None:
    """
    Verify that the selected storefront role can open a product.

    The current enabled role is guest. Customer and admin coverage can be
    added to the parameter set when those business scenarios are required.
    """

    product_name = "UI Seed – Album"
    product_price = "$15.00"

    # Arrange: Navigate to the Shop page.
    home_page = HomePage(ui_role_page, ui_base_url)
    home_page.open()
    shop_page = home_page.open_shop()

    # Assert: Confirm that the Shop page is available before opening a product.
    shop_page.should_be_loaded()

    # Act: Open the target seeded product.
    product_page = shop_page.open_product(product_name)

    # Assert: Verify the product details exposed by the storefront.
    product_page.should_be_loaded()
    product_page.should_show_price(product_price)
    product_page.should_show_sku("ui-seed-album")
    product_page.should_show_category("Uncategorized")
    product_page.should_show_related_products()
