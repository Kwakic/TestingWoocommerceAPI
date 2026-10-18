from __future__ import annotations

from typing import Any

from EcommerceAPI.src.test_data.factories.customers.customer_factory import (
    CustomerFactory,
)


class CustomerBuilder:
    """
    Builder for scenario-specific customer creation data (builds a new customer).

    The builder sits between a test and the factory (depends on CustomerFactory):

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


    The builder answers:
        "What should be different for this particular scenario?"


    The Factory provides the minimum valid customer data
    (email + password). The Builder adds optional customer fields
    only when the scenario requires them.

    This keeps tests concise. A test can customize one or two fields
    without rebuilding an entire customer payload.

    Example:
        customer = (
            CustomerBuilder()
            .with_email("known@example.com")
            .with_name("John", "Smith")
            .build()
        )

    The resulting payload contains:

        {
            "email": "known@example.com",
            "password": "...",
            "first_name": "John",
            "last_name": "Smith",
        }

    For a scenario that only needs credentials:

        customer = CustomerBuilder().build()

    Result:

        {
            "email": "...",
            "password": "...",
        }

    This is useful for UI scenarios where the test needs only a
    login-capable customer and will create additional state through
    the UI itself.

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

        # Store only scenario-specific optional fields here.
        # The Factory remains responsible for generating the mandatory
        # email/password defaults.
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
        Add an explicit customer username.

        The Factory does not generate a username by default because it is
        not required for the minimum valid customer creation payload.

        It can be added here when a scenario needs to log in with or
        otherwise reference a known username.
        """
        self._overrides["username"] = username
        return self

    def with_name(
        self,
        first_name: str,
        last_name: str,
    ) -> CustomerBuilder:
        """
        Add customer first and last names.

        Names are optional customer creation data and are therefore
        generated only when the scenario explicitly requires them.
        """
        self._overrides["first_name"] = first_name
        self._overrides["last_name"] = last_name
        return self

    def with_billing(self, billing: dict[str, Any]) -> CustomerBuilder:
        """
        Add or replace the customer billing address.
        """
        self._overrides["billing"] = billing
        return self

    def with_shipping(self, shipping: dict[str, Any]) -> CustomerBuilder:
        """
        Add or replace the customer shipping address.
        """
        self._overrides["shipping"] = shipping
        return self

    def with_fields(self, **fields: Any) -> CustomerBuilder:
        """
        Add arbitrary customer creation fields.

        This is useful while the Customer API exposes additional fields
        that do not yet have a dedicated fluent builder method.

        Dedicated ``with_*`` methods remain preferable for commonly used
        scenario fields because they make tests self-documenting.

        Example:
            customer = (
                CustomerBuilder()
                .with_fields(role="customer")
                .build()
            )
        """
        self._overrides.update(fields)
        return self

    def without_billing(self) -> CustomerBuilder:
        """
        Explicitly set billing data to an empty dictionary.

        Billing is absent by default. This method is intended for scenarios
        that specifically need to send an explicit empty billing object.

        IMPORTANT:
            This method does not claim that WooCommerce accepts an empty
            billing object. Whether that payload is valid is an API/domain
            concern and should be verified by the relevant test.
        """
        self._overrides["billing"] = {}
        return self

    def without_shipping(self) -> CustomerBuilder:
        """
        Explicitly set shipping data to an empty dictionary.

        Shipping is absent by default. This method is intended for scenarios
        that specifically need to send an explicit empty shipping object.

        Whether WooCommerce accepts this payload is deliberately not
        decided by the builder.
        """
        self._overrides["shipping"] = {}
        return self

    def build(self) -> dict[str, Any]:
        """
        Produce the final customer creation payload.

        The Builder first asks CustomerFactory for the minimum valid
        customer data (email + password), then adds the scenario-specific
        optional fields collected by the Builder.

        Returns:
            dict[str, Any]:
                Customer creation data ready for the provisioning layer.

        Example 1 - minimum customer:

            customer = CustomerBuilder().build()

        Result:

            {
                "email": "...",
                "password": "...",
            }

        Example 2 - scenario-specific customer:

            customer = (
                CustomerBuilder()
                .with_name("John", "Smith")
                .with_shipping(shipping_address)
                .build()
            )

        Result:

            {
                "email": "...",
                "password": "...",
                "first_name": "John",
                "last_name": "Smith",
                "shipping": {...},
            }
        """

        # The Factory is the boundary responsible for generating the
        # mandatory customer credentials.
        #
        # Only pass credentials when they were explicitly overridden.
        # This keeps the Factory responsible for generating the defaults.
        factory_overrides: dict[str, Any] = {}

        if "email" in self._overrides:
            factory_overrides["email"] = self._overrides["email"]

        if "password" in self._overrides:
            factory_overrides["password"] = self._overrides["password"]

        customer_data = self._factory.build(**factory_overrides)

        # The Builder owns all optional scenario-specific customer state.
        # Only fields explicitly requested by the scenario are added.
        optional_fields = {
            key: value
            for key, value in self._overrides.items()
            if key not in {"email", "password"}
        }

        customer_data.update(optional_fields)

        return customer_data
