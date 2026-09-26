from __future__ import annotations

from typing import Any

from EcommerceAPI.src.test_data.factories.customer_factory import CustomerFactory


class CustomerBuilder:
    """
    Builder for scenario-specific customer creation data.

    The builder sits between a test and the factory:

        Test
          |
          v
        Builder ---> Factory
          |
          v
        creation data
          |
          v
        Provisioner
          |
          v
        WooCommerce

    The factory answers:
        "How do I generate a complete valid customer?"

    The builder answers:
        "What should be different for this particular scenario?"

    This keeps tests concise. A test can customize one or two fields
    without rebuilding an entire customer payload.

    Example:
        customer = (
            CustomerBuilder()
            .with_email("known@example.com")
            .build()
        )

    The builder does NOT:
    - call WooCommerce;
    - access the database;
    - use pytest fixtures;
    - register cleanup resources;
    - perform assertions;
    - validate API responses.

    IMPORTANT
    ---------
    The builder returns ``dict[str, Any]`` rather than CustomerModel.
    CustomerModel describes a customer returned by the API, including
    server-generated fields such as ``id``. This builder creates data that
    exists before the API call.
    """

    def __init__(self, factory: CustomerFactory | None = None) -> None:
        """
        Initialize the builder.

        Args:
            factory:
                Optional CustomerFactory to use. Dependency injection is
                supported so callers can provide a configured factory.
                If omitted, a normal CustomerFactory is created.
        """
        self._factory = factory or CustomerFactory()

        # Store only scenario-specific overrides here. The factory remains
        # responsible for generating all unspecified default values.
        self._overrides: dict[str, Any] = {}

    def with_email(self, email: str) -> CustomerBuilder:
        """
        Override the generated customer email.

        Useful for scenarios involving known emails, lookup operations,
        duplicate-email behavior, or email-specific validation.
        """
        self._overrides["email"] = email
        return self

    def with_password(self, password: str) -> CustomerBuilder:
        """
        Override the generated customer password.
        """
        self._overrides["password"] = password
        return self

    def with_username(self, username: str) -> CustomerBuilder:
        """
        Override the generated customer username.
        """
        self._overrides["username"] = username
        return self

    def with_name(
        self,
        first_name: str,
        last_name: str,
    ) -> CustomerBuilder:
        """
        Override both first and last name.

        The values are changed together because generated usernames and
        default addresses are derived from the customer's name.
        """
        self._overrides["first_name"] = first_name
        self._overrides["last_name"] = last_name
        return self

    def with_billing(self, billing: dict[str, Any]) -> CustomerBuilder:
        """
        Replace the generated billing address.
        """
        self._overrides["billing"] = billing
        return self

    def with_shipping(self, shipping: dict[str, Any]) -> CustomerBuilder:
        """
        Replace the generated shipping address.
        """
        self._overrides["shipping"] = shipping
        return self

    def with_fields(self, **fields: Any) -> CustomerBuilder:
        """
        Override arbitrary customer creation fields.

        This is useful while the fixture API supports additional Customer API
        fields that do not yet have a dedicated fluent builder method.
        Dedicated ``with_*`` methods remain preferable for commonly used
        scenario fields because they make tests self-documenting.
        """
        self._overrides.update(fields)
        return self

    def without_billing(self) -> CustomerBuilder:
        """
        Set billing data to an empty dictionary.

        This is intended for scenarios that explicitly test missing or
        empty billing information.

        IMPORTANT:
            This method does not claim that WooCommerce accepts an empty
            billing object. Whether that payload is valid is an API/domain
            concern and should be verified by the relevant test.
        """
        self._overrides["billing"] = {}
        return self

    def without_shipping(self) -> CustomerBuilder:
        """
        Set shipping data to an empty dictionary.

        This is intended for scenarios that explicitly test missing or
        empty shipping information.

        Whether WooCommerce accepts this payload is deliberately not
        decided by the builder.
        """
        self._overrides["shipping"] = {}
        return self

    def build(self) -> dict[str, Any]:
        """
        Produce the final customer creation payload.

        The builder does not generate all values itself. It passes the
        collected scenario overrides to CustomerFactory, which generates
        sensible defaults for everything that was not overridden.

        Returns:
            dict[str, Any]:
                Customer creation data ready for the provisioning layer.

        Example:
            customer = (
                CustomerBuilder()
                .with_name("John", "Smith")
                .with_email("john.smith@example.com")
                .build()
            )
        """
        return self._factory.build(**self._overrides)
