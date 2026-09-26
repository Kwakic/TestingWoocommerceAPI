"""
Customer state builder.

Builds partial customer state for an already-existing WooCommerce customer.

The builder does not call APIs, access the database, use pytest, register
cleanup, validate responses, or own resources.
"""

from __future__ import annotations

from typing import Any


class CustomerStateBuilder:
    """
    Build partial state for an existing customer (builds a change).

    Unlike CustomerBuilder, this class does not create a complete customer
    payload. It returns only the fields that should be changed (has no Factory dependency at all).
    """

    _SUPPORTED_FIELDS = {
        "email",
        "username",
        "password",
        "first_name",
        "last_name",
        "role",
        "billing",
        "shipping",
    }

    def __init__(self) -> None:
        """Initialize an empty customer state."""
        self._state: dict[str, Any] = {}

    def with_email(self, email: str) -> CustomerStateBuilder:
        """Set the customer's email."""
        self._state["email"] = email
        return self

    def with_username(self, username: str) -> CustomerStateBuilder:
        """Set the customer's username."""
        self._state["username"] = username
        return self

    def with_password(self, password: str) -> CustomerStateBuilder:
        """Set the customer's password."""
        self._state["password"] = password
        return self

    def with_first_name(self, first_name: str) -> CustomerStateBuilder:
        """Set the customer's first name."""
        self._state["first_name"] = first_name
        return self

    def with_last_name(self, last_name: str) -> CustomerStateBuilder:
        """Set the customer's last name."""
        self._state["last_name"] = last_name
        return self

    def with_role(self, role: str) -> CustomerStateBuilder:
        """Set the customer's WooCommerce role."""
        self._state["role"] = role
        return self

    def with_billing(self, billing: dict[str, Any]) -> CustomerStateBuilder:
        """Set the customer's billing state."""
        self._state["billing"] = dict(billing)
        return self

    def with_shipping(self, shipping: dict[str, Any]) -> CustomerStateBuilder:
        """Set the customer's shipping state."""
        self._state["shipping"] = dict(shipping)
        return self

    def with_fields(self, **fields: Any) -> CustomerStateBuilder:
        """
        Add supported customer state fields.

        Raises TypeError for fields that are not supported by the builder.
        """
        unsupported = set(fields) - self._SUPPORTED_FIELDS

        if unsupported:
            raise TypeError(
                "Unsupported customer state field(s): " + ", ".join(sorted(unsupported))
            )

        self._state.update(fields)
        return self

    def build(self) -> dict[str, Any]:
        """
        Return the prepared partial customer state.

        Raises ValueError when no state fields have been configured.
        """
        if not self._state:
            raise ValueError(
                "Customer state cannot be empty. Configure at least one field."
            )

        return dict(self._state)
