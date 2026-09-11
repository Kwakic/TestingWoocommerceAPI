"""
UI password-recovery tests for WooCommerce customer accounts.

These tests validate the customer password-recovery entry point and negative
identifier handling. Password-reset UI mechanics remain encapsulated in the
CustomerPasswordRecoveryPage Page Object.

The test covers:
 - lost password page is accessible
 - invalid username/email is rejected
"""

import pytest
from playwright.sync_api import Page

from tests.ui.pages.customer_password_recovery_page import (
    CustomerPasswordRecoveryPage,
)

pytestmark = [
    pytest.mark.ui,
    pytest.mark.security,
]


def test_customer_can_open_password_recovery_page(
    page: Page,
    ui_base_url: str,
) -> None:
    """
    Verify that the customer can access the password-recovery workflow.

    The test validates the user-facing "Lost your password?" entry point and
    confirms that the dedicated password-recovery page is displayed.
    """
    # Arrange: Build the password-recovery Page Object.
    recovery_page = CustomerPasswordRecoveryPage(
        page=page,
        base_url=ui_base_url,
    )

    # Act: Open the password-recovery page.
    recovery_page.open()

    # Assert: Verify that the expected recovery page is displayed.
    recovery_page.should_be_loaded()


def test_customer_cannot_request_password_reset_for_unknown_email(
    page: Page,
    ui_base_url: str,
) -> None:
    """
    Verify that password recovery rejects an unknown username or email.

    This validates the negative password-recovery contract observed in the
    WooCommerce UI: an unknown identifier must not produce a valid reset
    request.
    """
    # Arrange: Build the password-recovery Page Object.
    recovery_page = CustomerPasswordRecoveryPage(
        page=page,
        base_url=ui_base_url,
    )

    # Act: Submit an identifier that does not belong to a customer account.
    recovery_page.request_reset(username_or_email="unknown@example.com")

    # Assert: Verify that WooCommerce rejects the unknown identifier.
    recovery_page.should_show_invalid_identifier_error()
