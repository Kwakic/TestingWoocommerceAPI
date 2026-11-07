"""Reusable address presets for checkout UI scenarios."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CheckoutAddress:
    """Describe one address in both WooCommerce API and UI terminology.

    WooCommerce accepts country and province codes when a customer is created,
    while checkout displays their human-readable names. Keeping both values
    here allows test setup and UI assertions to use the same scenario data.
    """

    first_name: str
    last_name: str
    street_address: str
    city: str
    province: str
    province_code: str
    postal_code: str
    country: str
    country_code: str
    phone: str = ""

    def as_billing(self) -> dict[str, str]:
        """Return a fresh WooCommerce billing-address payload."""
        address = self._as_customer_address()
        address["phone"] = self.phone
        return address

    def as_shipping(self) -> dict[str, str]:
        """Return a fresh WooCommerce shipping-address payload."""
        return self._as_customer_address()

    def _as_customer_address(self) -> dict[str, str]:
        # Return a new dictionary each time so no test can mutate shared data.
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "address_1": self.street_address,
            "city": self.city,
            "state": self.province_code,
            "postcode": self.postal_code,
            "country": self.country_code,
        }


# The baseline valid Spanish address used by checkout scenarios. Tests can
# override or create another CheckoutAddress when a scenario needs variation.
MADRID_ADDRESS = CheckoutAddress(
    first_name="John",
    last_name="Beck",
    street_address="Pl.del Pueblo,10",
    city="Madrid",
    province="Madrid",
    province_code="M",
    postal_code="28100",
    country="Spain",
    country_code="ES",
    phone="753357753",
)
