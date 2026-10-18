"""Page Object for the WooCommerce single-product page."""

import re

from playwright.sync_api import Page, expect


class ProductPage:
    """Encapsulate locators and actions for a WooCommerce product page."""

    def __init__(self, page: Page, product_name: str) -> None:
        self.page = page
        self.product_title = page.get_by_role(
            "heading", name=product_name, exact=True, level=1
        )
        self.add_to_cart_button = page.get_by_role(
            "button", name="Add to cart", exact=True
        )
        self.related_products_heading = page.get_by_role(
            "heading", name="Related products"
        )
        self.review_text = page.get_by_role("textbox", name="Your review *")
        self.reviewer_name = page.get_by_role("textbox", name="Name *")
        self.reviewer_email = page.get_by_role("textbox", name="Email *")
        self.submit_review_button = page.get_by_role("button", name="Submit")

    def should_be_loaded(self) -> None:
        """Verify that the requested product heading is visible."""
        expect(self.product_title).to_be_visible()

    def add_to_cart(self) -> None:
        """Add the current product to the shopping cart."""
        self.add_to_cart_button.click()

    def should_show_price(self, expected_price: str) -> None:
        """Verify the main product price, not a related-product card's price."""

        price = (
            self.page.get_by_role("main").get_by_text(expected_price, exact=True).first
        )
        expect(price).to_be_visible()

    def should_show_sku(self, expected_sku: str) -> None:
        """Verify that the product SKU is displayed."""
        expect(self.page.get_by_text(expected_sku, exact=True)).to_be_visible()

    def should_show_category(self, expected_category: str) -> None:
        """Verify the product category in the breadcrumb."""
        category = self.page.get_by_label("Breadcrumb").get_by_role(
            "link", name=expected_category, exact=True
        )
        expect(category).to_have_text(expected_category)

    def should_show_related_products(self) -> None:
        """Verify that the related-products section is displayed."""
        expect(self.related_products_heading).to_be_visible()

    def open_reviews(self) -> None:
        """Open the Reviews tab and wait for its content to be available."""
        reviews_tab = self.page.get_by_role(
            "link",
            name=re.compile(r"^Reviews(?: \(\d+\))?$"),
        )
        expect(reviews_tab).to_be_visible()
        reviews_tab.click()
        expect(self.page.locator("#review_form")).to_be_visible()

    def select_rating(self, rating: int) -> None:
        """Select a product rating from 1 to 5 stars."""
        if not 1 <= rating <= 5:
            raise ValueError("Rating must be between 1 and 5.")

        rating_link = self.page.locator(f"#review_form p.stars a.star-{rating}")
        expect(rating_link).to_be_visible()
        rating_link.click()

    def enter_review(self, review: str) -> None:
        """Enter the review text."""
        self.review_text.fill(review)

    def enter_reviewer_name(self, name: str) -> None:
        """Enter the reviewer's name for a guest review."""
        self.reviewer_name.fill(name)

    def enter_reviewer_email(self, email: str) -> None:
        """Enter the reviewer's email address for a guest review."""
        self.reviewer_email.fill(email)

    def complete_review_form(
        self,
        rating: int,
        review: str,
        reviewer_name: str | None = None,
        reviewer_email: str | None = None,
    ) -> None:
        """Fill and submit a review, including guest identity fields when supplied."""
        self.open_reviews()
        self.select_rating(rating)
        self.enter_review(review)

        if reviewer_name is not None:
            self.enter_reviewer_name(reviewer_name)
        if reviewer_email is not None:
            self.enter_reviewer_email(reviewer_email)

        self.submit_review()

    def submit_review(self) -> None:
        """Submit the review and explicitly follow WordPress's 302 redirect."""
        with self.page.expect_request("**/wp-comments-post.php") as request_info:
            self.submit_review_button.click(no_wait_after=True)

        request = request_info.value
        if request.method != "POST":
            raise AssertionError(f"Expected POST request, got {request.method}.")

        response = request.response()
        if response is None:
            raise AssertionError("Review submission response was not received.")
        if response.status != 302:
            raise AssertionError(
                f"Expected 302 response from review submission, got {response.status}."
            )

        redirect_url = response.headers.get("location")
        if not redirect_url:
            raise AssertionError(
                "Review submission response did not contain a redirect URL."
            )

        self.page.goto(redirect_url, wait_until="domcontentloaded")

    def should_show_submitted_review(self, review: str) -> None:
        """Verify that the submitted review is visible on the page."""
        expect(self.page.get_by_text(review, exact=True)).to_be_visible()
