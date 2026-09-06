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

        self.review_text = page.get_by_role(
            "textbox",
            name="Your review *",
        )

        self.reviewer_name = page.get_by_role(
            "textbox",
            name="Name *",
        )

        self.reviewer_email = page.get_by_role(
            "textbox",
            name="Email *",
        )

        self.submit_review_button = page.get_by_role(
            "button",
            name="Submit",
        )
        self.review_awaiting_approval = page.get_by_role(
            "paragraph",
        ).filter(
            has_text="Your review is awaiting approval",
        )

    def should_be_loaded(self) -> None:
        """Verify that the Product page is loaded."""
        expect(self.product_title).to_be_visible()

    def add_to_cart(self) -> None:
        """Add the product to the shopping cart."""
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

    def select_rating(self, rating: int) -> None:
        """Select a product rating from 1 to 5 stars."""
        if not 1 <= rating <= 5:
            raise ValueError("Rating must be between 1 and 5.")

        self.page.get_by_role(
            "link",
            name=f" {rating}",
        ).click()

    def enter_review(self, review: str) -> None:
        """Enter a product review."""
        self.review_text.fill(review)

    def enter_reviewer_name(self, name: str) -> None:
        """Enter the reviewer's name."""
        self.reviewer_name.fill(name)

    def enter_reviewer_email(self, email: str) -> None:
        """Enter the reviewer's email address."""
        self.reviewer_email.fill(email)

    def submit_review(self) -> None:
        """Submit the product review."""
        self.submit_review_button.click()

    def should_show_review_awaiting_approval(self) -> None:
        """Verify that the submitted review is awaiting approval."""
        expect(self.review_awaiting_approval).to_be_visible()

    def should_show_submitted_review(self, review: str) -> None:
        """Verify that the submitted review is displayed."""
        expect(self.page.get_by_text(review)).to_be_visible()
