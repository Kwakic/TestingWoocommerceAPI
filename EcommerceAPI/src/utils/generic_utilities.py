# generic_utilities.py
# Helper utils to generate random emails, passwords, strings, and coupon codes.

import logging
import random
import string

# import pprint
import time
from typing import (
    Optional,
    Dict,
)  # This line is included because of type hints in the function signatures:

logger = logging.getLogger(__name__)


def generate_random_email(
    domain: Optional[str] = None,
    email_prefix: Optional[str] = None,
) -> str:
    """
    Generate a random email address for test data.

    Args:
        domain:
            Email domain. Defaults to ``supersqa.com`` for backward
            compatibility with the existing utility.
        email_prefix:
            Prefix before the random portion. Defaults to ``testuser``.

    Returns:
        str:
            A syntactically valid test email address.
    """
    domain = domain or "supersqa.com"
    email_prefix = email_prefix or "testuser"

    random_string = "".join(random.choices(string.ascii_lowercase, k=10))
    return f"{email_prefix}_{random_string}@{domain}"


def generate_random_password(length: int = 20) -> str:
    """
    Generate a random password suitable for test users.

    The password contains letters, digits, and punctuation.

    Args:
        length:
            Password length. Must be greater than zero.

    Returns:
        str:
            A random password.

    Raises:
        ValueError:
            If ``length`` is not positive.
    """
    if length <= 0:
        raise ValueError("'length' must be a positive integer")

    password_chars = string.ascii_letters + string.digits + string.punctuation
    return "".join(random.choices(password_chars, k=length))


def generate_random_email_and_password(
    domain: Optional[str] = None,
    email_prefix: Optional[str] = None,
) -> Dict[str, str]:
    """
    Generate random credentials using the smaller reusable generators.

    This function is kept as the backward-compatible convenience API used
    by existing tests and framework code.
    """
    logger.debug("📝 Generating random email and password.")

    credentials = {
        "email": generate_random_email(
            domain=domain,
            email_prefix=email_prefix,
        ),
        "password": generate_random_password(),
    }

    # Never log the actual password. Test credentials should not appear in logs.
    logger.debug("📝 Generated test credentials for email: %s", credentials["email"])

    return credentials


# ---------------------------------------------------------------------------
# Generic human/address data generators
# ---------------------------------------------------------------------------
# These functions intentionally generate primitive values only. They do not
# know anything about WooCommerce customers, pytest fixtures, API calls, or
# cleanup. Domain factories compose these values into domain-specific payloads.


_FIRST_NAMES = (
    "Alex",
    "Daniel",
    "David",
    "Elena",
    "Emma",
    "James",
    "John",
    "Laura",
    "Lucas",
    "Maria",
    "Michael",
    "Natalia",
    "Oliver",
    "Paula",
    "Peter",
    "Sarah",
    "Sofia",
    "Thomas",
    "Victor",
    "William",
)

_LAST_NAMES = (
    "Anderson",
    "Baker",
    "Brown",
    "Carter",
    "Clark",
    "Davis",
    "Evans",
    "Garcia",
    "Gomez",
    "Harris",
    "Johnson",
    "Lewis",
    "Martin",
    "Miller",
    "Moore",
    "Parker",
    "Robinson",
    "Smith",
    "Taylor",
    "Wilson",
)

_SPANISH_CITIES = (
    "Madrid",
    "Barcelona",
    "Valencia",
    "Seville",
    "Malaga",
    "Bilbao",
    "Alicante",
    "Murcia",
    "Zaragoza",
    "Valladolid",
    "Vigo",
    "Cordoba",
    "Granada",
    "Toledo",
    "Salamanca",
)

_SPANISH_STATE_CODES = (
    "M",
    "B",
    "V",
    "SE",
    "MA",
    "BI",
    "A",
    "MU",
    "Z",
    "VA",
    "PO",
    "CO",
    "GR",
    "TO",
    "SA",
)

_STREET_NAMES = (
    "Main Street",
    "Oak Street",
    "Maple Street",
    "Gran Via",
    "Calle Mayor",
    "Calle Real",
    "Avenida Central",
    "Calle Sol",
    "Calle Luna",
    "Calle Nueva",
    "Calle Norte",
    "Calle Sur",
)


def generate_random_first_name() -> str:
    """Return a random first name suitable for generic test data."""
    return random.choice(_FIRST_NAMES)


def generate_random_last_name() -> str:
    """Return a random last name suitable for generic test data."""
    return random.choice(_LAST_NAMES)


def generate_random_username(
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
) -> str:
    """
    Generate a readable username from optional name components.

    The random suffix prevents collisions while keeping the username
    understandable in test reports and debugging output.
    """
    first = first_name or generate_random_first_name()
    last = last_name or generate_random_last_name()
    suffix = generate_random_combination(length=6, prefix="")
    return f"{first.lower()}.{last.lower()}.{suffix.lower()}"


def generate_random_phone(country: str = "ES") -> str:
    """
    Generate a random phone number for a supported country.

    Currently Spain is supported explicitly. The function keeps the country
    argument so country-specific formats can be added without changing the
    factory API later.
    """
    if country != "ES":
        raise ValueError(f"Unsupported phone country: {country}")

    # Spanish mobile numbers commonly begin with 6 or 7 and contain 9 digits.
    return f"{random.choice('67')}{random.randint(10000000, 99999999)}"


def generate_random_city(country: str = "ES") -> str:
    """Generate a random city name for the requested supported country."""
    if country != "ES":
        raise ValueError(f"Unsupported city country: {country}")
    return random.choice(_SPANISH_CITIES)


def generate_random_state_code(country: str = "ES") -> str:
    """Generate a random province/state code for the requested country."""
    if country != "ES":
        raise ValueError(f"Unsupported state country: {country}")
    return random.choice(_SPANISH_STATE_CODES)


def generate_random_postcode(country: str = "ES") -> str:
    """Generate a valid-looking postal code for the requested country."""
    if country != "ES":
        raise ValueError(f"Unsupported postcode country: {country}")
    return f"{random.randint(1000, 52999):05d}"


def generate_random_street_address() -> str:
    """Generate a simple, API-safe street address."""
    return f"{random.choice(_STREET_NAMES)} {random.randint(1, 200)}"


def generate_random_address(
    country: str = "ES",
) -> Dict[str, str]:
    """
    Generate a complete generic address dictionary.

    This is still a data-generation utility, not a WooCommerce-specific
    helper. A domain factory can add domain-specific fields such as email.
    """
    if country != "ES":
        raise ValueError(f"Unsupported address country: {country}")

    return {
        "address_1": generate_random_street_address(),
        "city": generate_random_city(country),
        "state": generate_random_state_code(country),
        "postcode": generate_random_postcode(country),
        "country": country,
        "phone": generate_random_phone(country),
    }


def generate_random_string(
    length: int = 10, prefix: Optional[str] = None, suffix: Optional[str] = None
) -> str:
    """
    Generate a random alphabetic string with optional prefix and suffix.

    Args:
        length (int): Length of the core random string.
        prefix (Optional[str]): String to prepend.
        suffix (Optional[str]): String to append.

    Returns:
        str: The resulting string.
    """
    core = "".join(random.choices(string.ascii_letters, k=length))

    if prefix:
        core = prefix + core
    if suffix:
        core += suffix

    return core


# ✅ Refactored version of the random string generator with strong validation and fallback options
def generate_random_combination(
    length: int = 12, prefix: Optional[str] = None, suffix: Optional[str] = None
) -> str:
    # It produces clean, random alphanumeric strings with optional prefix/suffix.
    # It raises an error if length <= 0
    """
    Generate a random alphanumeric string with optional prefix and suffix.

    Args:
        length (int): Length of the core string. Must be > 0.
        prefix (Optional[str]): String to prepend to the random core.
        suffix (Optional[str]): String to append to the random core.

    Returns:
        str: Concatenated string of prefix + random core + suffix.

    Raises:
        ValueError: If `length` is not positive.
    """
    if length <= 0:
        raise ValueError("❌ 'length' must be a positive integer")

    core = "".join(random.choices(string.ascii_letters + string.digits, k=length))

    if prefix:
        core = prefix + core
    if suffix:
        core += suffix
    return core


# -------------------------------------------
# 🧩 Extract remaining fields
# -------------------------------------------
# 🔧 Since the create_customer() method accepts both positional email/password arguments and arbitrary **kwargs, it's
# easy to mistakenly pass those keys in both places during testing.
def strip_keys(d: dict, exclude=("email", "password")) -> dict:
    # d: dict → Type Hint (d should be a dict). In Python 3 is used to indicate what type a parameter should be.
    # d: the input dictionary we want to clean, "exclude": a tuple of keys to remove (default is ("email", "password"))
    # You can override it, for example, strip_keys(my_dict, exclude=("id", "token"))
    """
    Returns a new dict with specified keys removed.
    Useful for avoiding duplication when passing payload both as direct args and kwargs.
    """
    return {
        k: v for k, v in d.items() if k not in exclude
    }  # Loops through every key-value pair in the input
    # dictionary d and Keeps only those keys that are not in the exclude tuple.


# Then in your test file: customers = create_customer_for_test(email=email, password=password, **strip_keys(payload))
# Instead of doing this every time: additional_fields = {
#     k: v for k, v in payload.items() if k not in ("email", "password")
# }
# You'd just write:
# from EcommerceAPI.src.utils.genericUtilities import strip_keys
# email = payload.get("email")
# password = payload.get("password")
#
# customers = create_customer_for_test(
#     email=email,
#     password=password,
#     expected_status_code=400,
#     auto_generate=False,
#     **strip_keys(payload)
# )


# That line only becomes necessary if: You’re passing a full payload dict using **payload AND you want to avoid
# sending email and password twice (once directly, once inside **kwargs).

# This line removes the 'email' and 'password' keys from the original payload and stores any remaining fields in a
# new dictionary called `additional_fields`. In other words: It creates a new dictionary with all key-value pairs
# except "email" and "password".
# Example:
# payload = {"email": "bademail", "password": "TestPass1", "first_name": "John", "age": 30}
# additional_fields = {"first_name": "John", "age": 30}
# Purpose:
# Prevents duplicate values when calling the factory method, as `email` and `password` will be passed explicitly.

# additional_fields = {
#     k: v for k, v in payload.items() if k not in ("email", "password")
# }

# or:
# additional_fields = {
#     k: v             # For each key k and value v in the dictionary
#     for k, v in payload.items()  # .items() gives us (key, value) pairs
#     if k not in ("email", "password")  # Skip keys "email" and "password"
# }

# or:
# # Full Equivalent Block Version:
# additional_fields = {}
# for k, v in payload.items():
#     if k not in ("email", "password"):
#         additional_fields[k] = v

# 🔠 What Do k and v Mean? They are just placeholder variable names that represent:
#     k: the key from the dictionary (e.g., "first_name")
#     v: the value associated with that key (e.g., "Alice")
# payload.items() gives you each key-value pair from the dictionary.


# ✅ Safe version for test usage
def safe_product_name(prefix: str = "Product") -> str:
    # Combines a short random string with a timestamp-based suffix for uniqueness.
    # Always returns a non-empty, API-safe product name.
    # Ideal for use in tests to prevent:
    #  - Name collisions
    #  - Invalid/missing names
    #  - Empty/blank strings
    """
    Generate a safe, unique product name for test use.

    Returns:
        str: A product name that is guaranteed to be non-empty and unique.
    """
    # Timestamp-based suffix to help ensure uniqueness across tests
    timestamp_suffix = str(int(time.time() * 1000))[-6:]
    return generate_random_combination(
        length=6, prefix=f"{prefix}-", suffix=timestamp_suffix
    )


def generate_random_coupon_code(length=10, prefix="", suffix=""):
    """
    Generate a random coupon code with optional prefix and suffix.

    :param length: Length of the random middle part (non-negative integer)
    :param prefix: Optional string prefix
    :param suffix: Optional string suffix
    :return: Full coupon code as a string
    """
    if not isinstance(length, int) or length < 0:
        raise ValueError("`length` must be a non-negative integer.")

    prefix = str(prefix) if prefix else ""
    suffix = str(suffix) if suffix else ""

    middle = "".join(random.choices(string.ascii_uppercase, k=length))
    return f"{prefix}{middle}{suffix}"


# if __name__ == "__main__":
#     from pprint import pprint
#
#     # pprint(generate_random_email_and_password())
#     pprint(generate_random_string(prefix="Test_", suffix="_End"))
#     # pprint(generate_random_combination(prefix='Item-', suffix='-XYZ'))
#     # pprint(generate_random_coupon_code(suffix='2025'))
