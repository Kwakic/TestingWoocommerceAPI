from playwright.sync_api import Page, expect


class ProductPage:
    def __init__(self, page: Page) -> None:

        self.page = page
        self.product_title = page.get_by_role("heading", name="UI Seed – Album")
        self.add_to_cart_button = page.get_by_role(
            "button",
            name="Add to cart",
            exact=True,
        )
        self.price = page.get_by_text("$15.00")
        self.sku = page.get_by_text("SKU: ui-seed-album")
        self.category = page.get_by_label("Breadcrumb").get_by_role(
            "link", name="Uncategorized"
        )
        self.related_products_heading = page.get_by_role(
            "heading",
            name="Related products",
        )

    def should_be_loaded(self) -> None:
        """Verify that the Product page is loaded."""
        expect(self.product_title).to_be_visible()

    def add_to_cart(self) -> None:
        """Add the product to the cart."""
        self.add_to_cart_button.click()

    def should_show_price(self, expected_price: str) -> None:
        """Verify that the product displays the expected price."""
        expect(self.price).to_have_text(expected_price)

    def should_show_sku(self, expected_sku: str) -> None:
        """Verify that the product displays the expected SKU."""
        expect(self.sku).to_have_text(f"SKU: {expected_sku}")

    def should_show_category(self, expected_category: str) -> None:
        """Verify that the product displays the expected category."""
        expect(self.category).to_have_text(expected_category)

    def should_show_related_products(self) -> None:
        """Verify that the Related products section is displayed."""
        expect(self.related_products_heading).to_be_visible()
