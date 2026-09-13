"""
Page Object for the WooCommerce customer account details area.

The Page Object encapsulates:
    - account-details form locators
    - account-details navigation
    - page-level verification
    - reusable account-details interactions and validation
"""

from playwright.sync_api import Page, expect


class CustomerAccountDetailsPage:
    """
    Represent the authenticated customer's Account details page.

    This Page Object keeps form locators and UI interaction details outside
    the test layer while the test remains responsible for the business scenario.
    """

    def __init__(self, page: Page) -> None:
        """
        Initialize the customer Account details Page Object.

        Args:
            page: Playwright Page associated with the authenticated customer
                browser context.
        """
        self.page = page

        # Account details page heading.
        self.account_details_heading = page.get_by_role(
            "heading",
            name="Account details",
            exact=True,
        )

        # Required customer profile fields.
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

        # Customer display name.
        self.display_name_input = page.get_by_role(
            "textbox",
            name="Display name *",
            exact=True,
        )

        # Customer email.
        self.email_input = page.get_by_role(
            "textbox",
            name="Email address *",
            exact=True,
        )

        # Password-management fields.
        self.current_password_input = page.get_by_role(
            "textbox",
            name="Current password (leave blank to leave unchanged)",
            exact=True,
        )
        self.new_password_input = page.get_by_role(
            "textbox",
            name="New password (leave blank to leave unchanged)",
            exact=True,
        )
        self.confirm_new_password_input = page.get_by_role(
            "textbox",
            name="Confirm new password",
            exact=True,
        )

        # Account-details form submission.
        self.save_changes_button = page.get_by_role(
            "button",
            name="Save changes",
            exact=True,
        )

        # WooCommerce validation / confirmation message.
        self.alert = page.get_by_role("alert")

        # Validation messages for the required profile fields.
        self.first_name_required_error = page.get_by_text(
            "First name is a required field.",
            exact=True,
        )
        self.last_name_required_error = page.get_by_text(
            "Last name is a required field.",
            exact=True,
        )

    def should_be_loaded(self) -> None:
        """Verify that the customer Account details form is displayed."""
        expect(self.account_details_heading).to_be_visible()
        expect(self.first_name_input).to_be_visible()
        expect(self.last_name_input).to_be_visible()
        expect(self.display_name_input).to_be_visible()
        expect(self.email_input).to_be_visible()
        expect(self.save_changes_button).to_be_visible()

    def update_profile(
        self,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> None:
        """
        Update the supplied customer profile fields.

        Args:
            first_name: Optional new first name.
            last_name: Optional new last name.
        """
        if first_name is not None:
            self.first_name_input.fill(first_name)

        if last_name is not None:
            self.last_name_input.fill(last_name)

    def should_show_saved_profile(
        self,
        first_name: str,
        last_name: str,
    ) -> None:
        """
        Verify that the saved customer profile values are displayed.
        """
        expect(self.first_name_input).to_have_value(first_name)
        expect(self.last_name_input).to_have_value(last_name)

    def should_show_account_details_saved_message(self) -> None:
        """Verify that WooCommerce confirms the Account details update."""
        expect(self.alert).to_contain_text("Account details changed")

    def clear_required_name_fields(self) -> None:
        """Clear the required first-name and last-name fields."""
        self.first_name_input.fill("")
        self.last_name_input.fill("")

    def save_changes(self) -> None:
        """Submit the Account details form and wait for the page to settle."""
        self.save_changes_button.click()
        self.page.wait_for_load_state("domcontentloaded")

    def should_show_required_name_validation(self) -> None:
        """
        Verify that WooCommerce rejects an account-details update when both
        required name fields are empty.
        """
        expect(self.alert).to_be_visible()
        expect(self.first_name_required_error).to_be_visible()
        expect(self.last_name_required_error).to_be_visible()
