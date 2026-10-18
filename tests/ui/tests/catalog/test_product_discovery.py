"""UI tests for storefront product discovery.

Products are created through the shared API fixture so each test owns its
product data and the fixture handles API cleanup. Customer coverage uses a
disposable API-provisioned customer instead of a seeded account.
"""

from collections.abc import Callable
from uuid import uuid4

import pytest
from playwright.sync_api import Page

from tests.ui.data.models.customer_model import DynamicCustomer
from tests.ui.fixtures.customer_auth import login_customer
from tests.ui.pages.common.home_page import HomePage


pytestmark = [pytest.mark.ui, pytest.mark.smoke]


def test_guest_can_open_product(
    guest_page: Page,
    ui_base_url: str,
    create_valid_product: Callable[..., dict],
) -> None:
    """Verify that a guest can view an API-created product and its details."""
    product = _create_catalog_products(create_valid_product)

    # Keep navigation and UI assertions in the Page Objects; the test describes
    # the behavior being checked rather than hiding it in another helper.
    home_page = HomePage(guest_page, ui_base_url)
    home_page.open()

    shop_page = home_page.open_shop()
    shop_page.should_be_loaded()

    product_page = shop_page.open_product(product["name"])
    product_page.should_be_loaded()
    product_page.should_show_price("$15.00")
    product_page.should_show_sku(product["sku"])
    product_page.should_show_related_products()


def test_customer_can_open_product(
    page: Page,
    ui_base_url: str,
    dynamic_customer: DynamicCustomer,
    create_valid_product: Callable[..., dict],
) -> None:
    """Verify that an API-provisioned customer can view a product's details."""
    login_customer(
        page=page,
        ui_base_url=ui_base_url,
        username=dynamic_customer.username,
        password=dynamic_customer.password,
    )
    product = _create_catalog_products(create_valid_product)

    home_page = HomePage(page, ui_base_url)
    home_page.open()

    shop_page = home_page.open_shop()
    shop_page.should_be_loaded()

    product_page = shop_page.open_product(product["name"])
    product_page.should_be_loaded()
    product_page.should_show_price("$15.00")
    product_page.should_show_sku(product["sku"])
    product_page.should_show_related_products()


def _create_catalog_products(
    create_valid_product: Callable[..., dict],
) -> dict:
    """Create isolated products needed by the catalog scenario.

    The target product is returned for assertions. A companion product is
    created so the storefront has another product available for its related
    products section. Both products are registered for cleanup by the shared
    ``create_valid_product`` fixture; this helper does not own cleanup.
    """
    # A shared suffix makes the products from one scenario easy to correlate
    # in logs, while their complete names and SKUs remain distinct.
    suffix = uuid4().hex[:10]

    target_product = create_valid_product(
        name=f"UI Discovery Product {suffix}",
        sku=f"ui-discovery-{suffix}",
        regular_price="15.00",
    )
    create_valid_product(
        name=f"UI Related Product {suffix}",
        sku=f"ui-related-{suffix}",
        regular_price="12.00",
    )
    return target_product
