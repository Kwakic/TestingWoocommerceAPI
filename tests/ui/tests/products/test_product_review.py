"""
UI tests for storefront product reviews.

These scenarios currently validate the guest review workflow. Role selection is
handled consistently through the indirect UI role fixture.
"""

import pytest
from playwright.sync_api import Page

from EcommerceAPI.src.utils.generic_utilities import generate_random_string
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
def test_guest_can_submit_product_review(
    ui_role_page: Page,
    ui_base_url: str,
) -> None:
    """
    Verify that the selected storefront role can submit a product review.

    The current enabled role is guest. The review itself is generated with a
    unique value so repeated test runs do not rely on static review content.
    """

    product_name = "UI Seed – Album"

    # Arrange: Navigate to the seeded product.
    home_page = HomePage(ui_role_page, ui_base_url)
    home_page.open()
    shop_page = home_page.open_shop()
    product_page = shop_page.open_product(product_name)

    product_page.should_be_loaded()

    review = generate_random_string(
        length=10,
        prefix="UI automation test review – ",
    )

    # Act: Enter and submit the review as the selected storefront role.
    product_page.select_rating(5)
    product_page.enter_review(review)
    product_page.enter_reviewer_name("UI Test User")
    product_page.enter_reviewer_email("ui-test@example.com")
    product_page.submit_review()

    # Assert: Verify that WordPress accepted the review for moderation and
    # that the submitted review content is displayed.
    product_page.should_show_review_awaiting_approval()
    product_page.should_show_submitted_review(review)
