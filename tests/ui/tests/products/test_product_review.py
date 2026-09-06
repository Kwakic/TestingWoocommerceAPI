import pytest
from playwright.sync_api import Page

from tests.ui.pages.home_page import HomePage
from EcommerceAPI.src.utils.generic_utilities import generate_random_string

pytestmark = [
    pytest.mark.ui,
    # pytest.mark.smoke,
]


def test_guest_can_submit_product_review(
    guest_page: Page,
    ui_base_url: str,
) -> None:
    """Verify that a guest can submit a product review."""

    home_page = HomePage(guest_page, ui_base_url)

    home_page.open()
    shop_page = home_page.open_shop()

    product_page = shop_page.open_product("UI Seed – Album")

    product_page.should_be_loaded()

    review = generate_random_string(
        length=10,
        prefix="UI automation test review – ",
    )

    product_page.select_rating(5)
    product_page.enter_review(review)
    product_page.enter_reviewer_name("UI Test User")
    product_page.enter_reviewer_email("ui-test@example.com")
    product_page.submit_review()

    product_page.should_show_review_awaiting_approval()
    product_page.should_show_submitted_review(review)
