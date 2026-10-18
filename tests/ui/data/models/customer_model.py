from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DynamicCustomer:
    """Test identity for a dynamically provisioned WooCommerce customer.

    The object deliberately keeps both pieces of information needed by UI
    tests:

        customer:
            The validated WooCommerce customer returned by the API.

        username / password:
            The credentials required to authenticate the browser.

    This is test infrastructure data, not a WooCommerce domain model.
    """

    customer: dict[str, Any]
    username: str
    password: str
