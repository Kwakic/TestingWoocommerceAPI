"""
Page Object for WooCommerce customer address management.
"""

from playwright.sync_api import Page, expect


class CustomerAddressPage:
    """
    Represent the customer Addresses section in WooCommerce My Account.

    This Page Object encapsulates address navigation, shipping address
    form interactions, and UI-level verification of the saved address.
    """

    def __init__(self, page: Page, base_url: str) -> None:
        """
        Initialize the customer address Page Object.

        Args:
            page: Playwright Page associated with the current test context.
            base_url: Base URL of the WooCommerce storefront.
        """
        self.page = page
        self.base_url = base_url

        # Shipping address page.
        self.shipping_address_heading = page.get_by_role(
            "heading",
            name="Shipping address",
            exact=True,
        )

        # Shipping address form fields.
        self.first_name_input = page.get_by_role(
            "textbox",
            name="First name *",
            exact=True,
        )
        self.last_name_input = page.get_by_role(
            "textbox",
            name="Last name *",
            exact=True,
        )
        self.company_input = page.get_by_role(
            "textbox",
            name="Company name (optional)",
            exact=True,
        )
        self.street_address_input = page.get_by_role(
            "textbox",
            name="Street address *",
            exact=True,
        )
        self.apartment_input = page.get_by_role(
            "textbox",
            name="Apartment, suite, unit, etc. (optional)",
            exact=True,
        )
        self.city_input = page.get_by_role(
            "textbox",
            name="Town / City *",
            exact=True,
        )
        self.zip_code_input = page.get_by_role(
            "textbox",
            name="Postcode / ZIP *",
            exact=True,
        )

        self.save_address_button = page.get_by_role(
            "button",
            name="Save address",
            exact=True,
        )

    def open(self) -> None:
        """Navigate directly to the customer shipping address page."""
        self.page.goto(
            f"{self.base_url.rstrip('/')}/my-account/edit-address/shipping/",
            wait_until="domcontentloaded",
        )

    def open_addresses(self) -> None:
        """Navigate to the customer Addresses summary page."""
        self.page.goto(
            f"{self.base_url.rstrip('/')}/my-account/edit-address/",
            wait_until="domcontentloaded",
        )

    def should_be_loaded(self) -> None:
        """Verify that the shipping address form is available."""
        expect(self.shipping_address_heading).to_be_visible()
        expect(self.first_name_input).to_be_visible()
        expect(self.last_name_input).to_be_visible()
        expect(self.street_address_input).to_be_visible()
        expect(self.city_input).to_be_visible()
        expect(self.zip_code_input).to_be_visible()
        expect(self.save_address_button).to_be_visible()

    def fill_shipping_address(
        self,
        first_name: str,
        last_name: str,
        street_address: str,
        city: str,
        zip_code: str,
        company: str | None = None,
    ) -> None:
        """
        Fill the customer shipping address form.

        Args:
            first_name: Shipping recipient first name.
            last_name: Shipping recipient last name.
            street_address: Shipping street address.
            city: Shipping city.
            zip_code: Shipping postal code.
            company: Optional company name.
        """
        self.first_name_input.fill(first_name)
        self.last_name_input.fill(last_name)

        if company is not None:
            self.company_input.fill(company)

        self.street_address_input.fill(street_address)
        self.city_input.fill(city)
        self.zip_code_input.fill(zip_code)

    def save_address(self) -> None:
        """
        Submit the shipping address form and wait for the WooCommerce save
        request to complete.

        WooCommerce submits this form with a POST request and then redirects
        back to the account area. Waiting for the POST response prevents the
        test from navigating away before the address update has been processed.
        """
        with self.page.expect_response(
            lambda response: (
                response.request.method == "POST"
                and "/my-account/edit-address/shipping/" in response.url
                and response.status in (200, 302, 303)
            )
        ):
            self.save_address_button.click()

        self.page.wait_for_load_state("domcontentloaded")

    def should_show_shipping_address(
        self,
        first_name: str,
        last_name: str,
        company: str,
        street_address: str,
        apartment: str,
        zip_code: str,
        city: str,
        state: str,
        country: str,
    ) -> None:
        """
        Verify that the saved shipping address is displayed on the Addresses page.

        The WooCommerce Addresses page renders the shipping address inside an
        HTML <address> element. The assertion is intentionally scoped to that
        element rather than relying on the exact text-node structure, which can
        vary between browsers.
        """
        # Locate the container that owns the "Shipping address" heading and
        # then find the address element inside that same container.
        shipping_address_container = self.page.get_by_role(
            "heading",
            name="Shipping address",
            exact=True,
        ).locator("xpath=ancestor::*[.//address][1]")

        shipping_address = shipping_address_container.locator("address")

        # Verify that the shipping address block is displayed.
        expect(shipping_address).to_be_visible()

        # Verify every expected address component independently. This avoids
        # brittle full-string matching across browser-specific whitespace and
        # line-break rendering.
        expected_parts = [
            first_name,
            last_name,
            company,
            street_address,
            apartment,
            zip_code,
            city,
            state,
            country,
        ]

        for part in expected_parts:
            if part:
                expect(shipping_address).to_contain_text(part)

    def update_shipping_address(
        self,
        company: str | None = None,
        street_address: str | None = None,
        apartment: str | None = None,
    ) -> None:
        """
        Update selected fields in the customer shipping address form.

        Args:
            company: Optional company name.
            street_address: Optional shipping street address.
            apartment: Optional apartment, suite, or unit.
        """
        # Update the company field when a new value is supplied.
        if company is not None:
            self.company_input.fill(company)

        # Update the street address when a new value is supplied.
        if street_address is not None:
            self.street_address_input.fill(street_address)

        # Update the apartment field when a new value is supplied.
        if apartment is not None:
            self.apartment_input.fill(apartment)
