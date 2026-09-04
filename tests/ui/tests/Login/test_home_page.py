"""
UI tests for the WooCommerce home page.
"""

import pytest

from playwright.sync_api import Page, expect

pytestmark = [
    pytest.mark.ui,
    pytest.mark.smoke,
]


def test_home_page_loads(page: Page) -> None:
    """
    Verify that the WooCommerce storefront home page loads successfully.

    The ``page`` fixture provides:
        - a session-scoped browser
        - a fresh browser context
        - a fresh page

    The test is therefore responsible only for the UI behavior being verified.

    """

    # Navigate to the WooCommerce storefront.
    page.goto("http://localhost:8888/kwakiweb")

    # Locate the Test Shop link inside the page banner.
    shop_link = page.get_by_role("banner").get_by_role(
        "link",
        name="Test Shop",
    )

    # Verify that the link is visible to the user.
    expect(shop_link).to_be_visible()

    # Click the link.
    shop_link.click()

    # Verify that the expected page loaded.
    expect(page).to_have_title("Test Shop")


# def test_navigate_to_shop(page: Page) -> None:
#     """
#     Verify that the user can navigate from the home page to the Shop page.
#     """
#
#     page.goto("http://localhost:8080/")
#
#     shop_link = page.locator("#modal-1-content").get_by_role("link",name="Shop")
#
#     expect(shop_link).to_be_visible()
#
#     shop_link.click()
#
#     expect(page).to_have_url("http://localhost:8080/shop/")
#
#
# def test_shop_page_loads(page: Page) -> None:
#     """
#     Verify that the WooCommerce Shop page loads successfully.
#     """
#
#     page.goto("http://localhost:8080/shop/")
#
#     expect(page).to_have_url("http://localhost:8080/shop/")
#     expect(page.get_by_role("heading", name="Shop")).to_be_visible()
#
#
# def test_add_product_to_cart(page: Page) -> None:
#     page.goto("http://localhost:8080/shop/")
#
#     product = page.get_by_role("link",name="ACTUAL PRODUCT NAME")
#
#     expect(product).to_be_visible()
#
#     product.click()
#
#     # Verify product details...
