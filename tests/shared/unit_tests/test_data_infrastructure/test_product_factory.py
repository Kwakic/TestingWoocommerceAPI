"""Unit tests for Product test-data factories.

These tests exercise ProductFactory in isolation.

The unit-test layer intentionally does not:
    - call WooCommerce;
    - use pytest integration fixtures;
    - provision Products;
    - access the database;
    - register resources for cleanup.

The purpose is to verify that the ProductFactory generates valid, predictable
test-data values and rejects invalid generation parameters.

Product API integration tests live separately under the Product API test suite.
"""

import pytest

from EcommerceAPI.src.test_data.factories.products.product_factory import (
    ProductFactory,
)


class TestProductFactorySalePrice:
    """Verify ProductFactory sale-price generation in isolation."""

    def test_generate_sale_price_uses_requested_discount(
        self,
        monkeypatch,
    ):
        """
        Verify that the generated sale price is derived from the supplied
        regular price and generated discount.

        ``random.uniform`` is patched so the unit test is deterministic while
        still exercising ProductFactory's calculation logic.
        """

        monkeypatch.setattr(
            "EcommerceAPI.src.test_data.factories.products.product_factory.random.uniform",
            lambda min_discount, max_discount: 20.0,
        )

        sale_price, discount_percentage = ProductFactory.generate_sale_price(
            regular_price=100.00,
        )

        assert sale_price == "80.0"
        assert discount_percentage == 20.0
        assert float(sale_price) < 100.00

    @pytest.mark.parametrize(
        "regular_price,min_discount,max_discount",
        [
            (0.0, 5.0, 50.0),
            (-10.0, 5.0, 50.0),
        ],
    )
    def test_generate_sale_price_rejects_invalid_regular_price(
        self,
        regular_price,
        min_discount,
        max_discount,
    ):
        """Verify that the regular price must be greater than zero."""

        with pytest.raises(ValueError, match="regular_price must be greater than zero"):
            ProductFactory.generate_sale_price(
                regular_price,
                min_discount,
                max_discount,
            )

    def test_generate_sale_price_rejects_negative_discount(self):
        """Verify that a negative discount cannot be configured."""

        with pytest.raises(ValueError, match="min_discount cannot be negative"):
            ProductFactory.generate_sale_price(
                regular_price=100.00,
                min_discount=-1.0,
                max_discount=50.0,
            )

    def test_generate_sale_price_rejects_reversed_discount_range(self):
        """Verify that the maximum discount cannot be below the minimum."""

        with pytest.raises(
            ValueError,
            match="max_discount must be greater than or equal to min_discount",
        ):
            ProductFactory.generate_sale_price(
                regular_price=100.00,
                min_discount=50.0,
                max_discount=20.0,
            )

    def test_generate_sale_price_rejects_full_discount(self):
        """
        Verify that a 100% or greater discount is rejected because it would
        produce a zero or negative sale price.
        """

        with pytest.raises(
            ValueError,
            match="max_discount must be less than 100",
        ):
            ProductFactory.generate_sale_price(
                regular_price=100.00,
                min_discount=5.0,
                max_discount=100.0,
            )
