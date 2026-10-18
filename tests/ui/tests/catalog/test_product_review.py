"""UI tests for guest and authenticated product review submission.

Each test provisions its own product through the shared API fixture, which
also handles API cleanup. Storefront navigation is explicit in the test, while
ProductPage encapsulates product-page interactions and review-form locators.
"""

from collections.abc import Callable
from uuid import uuid4

import pytest
from playwright.sync_api import Page

from EcommerceAPI.src.utils.generic_utilities import generate_random_string
from tests.ui.data.models.customer_model import DynamicCustomer
from tests.ui.fixtures.customer_auth import login_customer
from tests.ui.pages.common.home_page import HomePage


pytestmark = [pytest.mark.ui, pytest.mark.smoke]


def test_guest_can_submit_product_review(
    guest_page: Page,
    ui_base_url: str,
    create_valid_product: Callable[..., dict],
) -> None:
    """Verify that a guest can submit a review for a product."""
    suffix = uuid4().hex[:10]
    product = create_valid_product(
        name=f"UI Review Product {suffix}",
        sku=f"ui-review-{suffix}",
        regular_price="15.00",
    )

    # Arrange: Navigate to the API-created product through the storefront.
    home_page = HomePage(guest_page, ui_base_url)
    home_page.open()

    shop_page = home_page.open_shop()
    shop_page.should_be_loaded()

    product_page = shop_page.open_product(product["name"])
    product_page.should_be_loaded()

    # Act: Submit a review as a guest.
    review = generate_random_string(
        length=10,
        prefix="UI automation test review – ",
    )
    product_page.complete_review_form(
        rating=5,
        review=review,
        reviewer_name=f"UI Test User {uuid4().hex[:8]}",
        reviewer_email=f"ui-review-{uuid4().hex}@example.com",
    )

    # Assert: Verify that the submitted review is visible.
    product_page.should_show_submitted_review(review)


def test_customer_can_submit_product_review(
    page: Page,
    ui_base_url: str,
    dynamic_customer: DynamicCustomer,
    create_valid_product: Callable[..., dict],
) -> None:
    """Verify that an authenticated customer can submit a product review."""
    login_customer(
        page=page,
        ui_base_url=ui_base_url,
        username=dynamic_customer.username,
        password=dynamic_customer.password,
    )

    suffix = uuid4().hex[:10]
    product = create_valid_product(
        name=f"UI Review Product {suffix}",
        sku=f"ui-review-{suffix}",
        regular_price="15.00",
        # skip_cleanup= True
    )

    # Arrange: Navigate to the API-created product through the storefront.
    home_page = HomePage(page, ui_base_url)
    home_page.open()

    shop_page = home_page.open_shop()
    shop_page.should_be_loaded()

    product_page = shop_page.open_product(product["name"])
    product_page.should_be_loaded()

    # Act: Submit a review as the authenticated customer.
    review = generate_random_string(
        length=10,
        prefix="UI automation test review – ",
    )
    product_page.complete_review_form(rating=5, review=review)

    # Assert: Verify that the submitted review is visible.
    product_page.should_show_submitted_review(review)
