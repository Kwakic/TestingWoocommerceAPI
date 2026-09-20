from playwright.sync_api import Page, expect


class CartPage:
    """Page Object for the WooCommerce shopping cart."""

    def __init__(self, page: Page) -> None:
        """
        Initialize the Cart Page Object.

        Args:
            page: Playwright Page associated with the current test context.
        """
        self.page = page

        self.cart_heading = page.get_by_role(
            "heading",
            name="Cart",
        )
        self.empty_cart_heading = page.get_by_role(
            "heading",
            name="Your cart is currently empty!",
        )
        self.view_cart_link = page.get_by_role(
            "alert",
        ).get_by_role(
            "link",
            name="View cart",
        )
        self.product_price = page.get_by_text("$").first
        self.quantity_input = page.get_by_role("spinbutton").first

    def should_be_loaded(self) -> None:
        """Verify that the shopping cart page is displayed."""
        expect(self.cart_heading).to_be_visible()

    def open_from_add_to_cart_notice(self) -> None:
        """Open the shopping cart from the product-added confirmation."""
        expect(self.view_cart_link).to_be_visible()
        self.view_cart_link.click()

    def should_contain_product(self, product_name: str) -> None:
        """Verify that the cart contains the specified product."""
        expect(self.page.get_by_text(product_name)).to_be_visible()

    def should_show_price(self, expected_price: str) -> None:
        """Verify that the product price is displayed in the cart."""
        expect(self.product_price).to_have_text(expected_price)

    def increase_quantity(self) -> None:
        """Increase the quantity of the seeded cart product."""
        self.page.get_by_role(
            "button",
            name="Increase quantity of UI Seed",
        ).click()

    def decrease_quantity(self) -> None:
        """Decrease the quantity of the seeded cart product."""
        self.page.get_by_role(
            "button",
            name="Reduce quantity of UI Seed",
        ).click()

    def should_show_quantity(self, expected_quantity: int) -> None:
        """Verify the current cart quantity."""
        expect(self.quantity_input).to_have_value(str(expected_quantity))

    def should_show_total(self, expected_total: str) -> None:
        """Verify that the cart displays the expected total."""
        expect(self.page.get_by_text(expected_total, exact=True).last).to_be_visible()

    def remove_product(self, product_name: str) -> None:
        """Remove the specified product and wait for its cart row to disappear."""
        remove_button_name = f"Remove {product_name}".replace("–", "&#8211;")

        remove_button = self.page.get_by_role(
            "button",
            name=remove_button_name,
        )

        remove_button.click()

    def should_be_empty(self) -> None:
        """Verify that the shopping cart is empty."""
        expect(self.empty_cart_heading).to_be_visible()
