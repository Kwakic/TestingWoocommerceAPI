"""
UI tests for storefront product reviews.

These scenarios validate product review submission for guest and customer
storefront roles.
"""

import pytest
from playwright.sync_api import Page

from EcommerceAPI.src.utils.generic_utilities import generate_random_string
from tests.ui.pages.common.home_page import HomePage


pytestmark = [
    pytest.mark.ui,
    pytest.mark.smoke,
]


def test_guest_can_submit_product_review(
    guest_page: Page,
    ui_base_url: str,
) -> None:
    """
    Verify that a guest can submit a product review.

    Guests must provide their name and email when submitting a review.
    """

    product_name = "UI Seed – Album"

    # Arrange: Navigate to the seeded product.
    home_page = HomePage(guest_page, ui_base_url)
    home_page.open()
    shop_page = home_page.open_shop()
    product_page = shop_page.open_product(product_name)

    product_page.should_be_loaded()

    review = generate_random_string(
        length=10,
        prefix="UI automation test review – ",
    )

    # Act: Submit a review as a guest.
    product_page.select_rating(5)
    product_page.enter_review(review)
    product_page.enter_reviewer_name("UI Test User")
    product_page.enter_reviewer_email("ui-test@example.com")
    product_page.submit_review()

    # Assert: Verify that the submitted review is displayed.
    product_page.should_show_submitted_review(review)


def test_customer_can_submit_product_review(
    customer_page: Page,
    ui_base_url: str,
) -> None:
    """
    Verify that a logged-in customer can submit a product review.

    Customer identity is provided by the authenticated account, so name and
    email are not entered in the review form.
    """

    product_name = "UI Seed – Album"

    # Arrange: Navigate to the seeded product.
    home_page = HomePage(customer_page, ui_base_url)
    home_page.open()
    shop_page = home_page.open_shop()
    product_page = shop_page.open_product(product_name)

    product_page.should_be_loaded()

    review = generate_random_string(
        length=10,
        prefix="UI automation test review – ",
    )

    # Act: Submit a review as a logged-in customer.
    product_page.select_rating(5)
    product_page.enter_review(review)
    product_page.submit_review()

    # Assert: Verify that the submitted review is displayed.
    product_page.should_show_submitted_review(review)
