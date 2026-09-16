# """
# Page Object for the WooCommerce Checkout page.
#
# The Page Object encapsulates checkout form locators and user interactions.
# The test remains responsible for the business scenario.
# """
# import re
#
# from playwright.sync_api import Page, expect
#
#
# class CheckoutPage:
#     """Represent the WooCommerce Checkout page."""
#
#     def __init__(self, page: Page, base_url: str) -> None:
#         self.page = page
#         self.base_url = base_url
#
#         # Checkout form fields recorded with Playwright Codegen.
#         self.email_input = page.get_by_role("textbox", name="Email address")
#         self.country_combobox = page.locator("#components-form-token-input-0")
#
#         self.first_name_input = page.get_by_role("textbox", name="First name")
#         self.last_name_input = page.get_by_role("textbox", name="Last name")
#         self.address_input = page.get_by_role(
#             "textbox",
#             name="Address",
#             exact=True,
#         )
#         self.postal_code_input = page.get_by_role(
#             "textbox",
#             name="Postal code",
#         )
#         self.city_input = page.get_by_role("textbox", name="City")
#         self.province_combobox = page.get_by_role("combobox", name="Province")
#         self.phone_input = page.get_by_role("textbox", name="Phone (optional)")
#
#         # Payment method recorded during the successful checkout flow.
#         self.cash_on_delivery = page.get_by_text("Cash on delivery", exact=True)
#
#         self.add_order_note_checkbox = page.get_by_role(
#             "checkbox",
#             name="Add a note to your order",
#         )
#         self.order_note_input = page.get_by_role(
#             "textbox",
#             name="Notes about your order.",
#         )
#         self.place_order_button = page.get_by_role(
#             "button",
#             name="Place Order",
#         )
#
#     def open(self) -> None:
#         """Navigate directly to the Checkout page."""
#         self.page.goto(
#             f"{self.base_url.rstrip('/')}/checkout/",
#             wait_until="domcontentloaded",
#         )
#
#     def should_be_loaded(self) -> None:
#         """Verify that the Checkout form is displayed."""
#         expect(self.email_input).to_be_visible()
#         expect(self.first_name_input).to_be_visible()
#         expect(self.last_name_input).to_be_visible()
#         expect(self.address_input).to_be_visible()
#         expect(self.postal_code_input).to_be_visible()
#         expect(self.city_input).to_be_visible()
#         expect(self.place_order_button).to_be_visible()
#
#     def fill_billing_address(
#         self,
#         email: str,
#         first_name: str,
#         last_name: str,
#         street_address: str,
#         postal_code: str,
#         city: str,
#         phone: str | None = None,
#     ) -> None:
#         """Fill the required checkout contact and billing address fields."""
#         self.email_input.fill(email)
#
#         self.country_combobox.fill("spa")
#         self.page.get_by_role("option", name="Spain").click()
#
#         self.first_name_input.fill(first_name)
#         self.last_name_input.fill(last_name)
#         self.address_input.fill(street_address)
#         self.city_input.fill(city)
#
#         self.province_combobox.fill("ma")
#         self.page.get_by_role("option", name="Madrid").click()
#
#         self.postal_code_input.fill(postal_code)
#
#         if phone is not None:
#             self.phone_input.fill(phone)
#
#     def select_cash_on_delivery(self) -> None:
#         """Select Cash on delivery as the checkout payment method."""
#         self.cash_on_delivery.click()
#
#     def add_order_note(self, note: str) -> None:
#         """Enable the order-note field and enter the supplied note."""
#         self.add_order_note_checkbox.check()
#         self.order_note_input.fill(note)
#
#     def place_order(self) -> None:
#         """Submit the order and wait for WooCommerce order confirmation."""
#         self.place_order_button.click()
#         self.page.wait_for_url(
#             re.compile(r".*/checkout/order-received/\d+/.*"),
#             wait_until="domcontentloaded",
#         )
