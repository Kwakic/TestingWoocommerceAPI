# generic_utilities.py
# Helper utils to generate random emails, passwords, strings, and coupon codes.

import logging as logger
import random
import string

# import pprint
import time
from typing import (
    Optional,
    Dict,
)  # This line is included because of type hints in the function signatures:


def generate_random_email_and_password(
    domain: Optional[str] = None, email_prefix: Optional[str] = None
) -> Dict[str, str]:
    """
    Generate a random email and password with optional custom domain and prefix.

    Args:
        domain (Optional[str]): The domain to use in the email address. Defaults to 'supersqa.com'.
        email_prefix (Optional[str]): The prefix before the email's random string. Defaults to 'testuser'.

    Returns:
        Dict[str, str]: Dictionary containing 'email' and 'password' keys.
    """

    logger.debug("📝 Generating random email and password.")

    # Below, we set our defaults, so that the user doesn't need to provide a domain
    if domain is None:
        domain = "supersqa.com"
    if email_prefix is None:
        email_prefix = "testuser"

    #
    random_string = "".join(random.choices(string.ascii_lowercase, k=10))
    email = f"{email_prefix}_{random_string}@{domain}"

    #
    password_chars = string.ascii_letters + string.digits + string.punctuation
    password = "".join(random.choices(password_chars, k=20))

    credentials = {"email": email, "password": password}
    logger.debug(f"📝 Generated credentials email and password: {credentials}")

    return credentials


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


# 📘 Code Explanation
# 1. Optional[str] = None:

#    - Why: This makes parameters optional and allows users to call the function with fewer arguments.
#    - Handled inside: We check if the argument is None, then assign a default manually (cleaner logic).

# 2. generate_random_email_and_password(...):
#     - Creates a random email like: testuser_xazcbeqpye@supersqa.com
#     - Creates a secure password with 20 characters using letters, digits, symbols
#     - Logs the output for debugging

# 3. generate_random_string(...):
#     - Generates alphabet-only string (e.g., abcdEFGh)
#     - Supports optional prefix/suffix (e.g., ID_abcdEFGh_XYZ)

# 4. generate_random_alphanumeric_string(...):
#     - Uses both letters and digits (e.g., ab9C5vZ3)
#     - Also supports optional prefix/suffix

# 5. generate_random_coupon_code(...):
#     - Generates uppercase letters only (e.g., QWERZXCVTY)
#     - Often used for discount or promo codes


# ✅ from typing import Optional, Dict
# This line is included because of type hints in the function signatures:
# Example:
# def generate_random_email_and_password(domain: Optional[str] = None, ...) -> Dict[str, str]:

#     "Optional[str]" = means the argument can be a str or None
#     "Dict[str, str]" = means the function returns a dictionary with both keys and values as strings

# 📌 Why it's useful:
#     - Improves readability
#     - Helps IDEs and tools like mypy for type checking
#     - Makes it easier for other developers to understand input/output
# If you don’t use type hints, you can remove that import. It's optional, but considered good practice in modern Python.
