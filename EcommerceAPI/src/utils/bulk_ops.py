# EcommerceAPI/src/utils/bulk_ops.py

import logging as logger


def bulk_create_and_validate_resources(
    create_fn,
    validate_fn,
    qty: int,
    label: str = "resource",
):
    """
    🔁 Utility function to bulk create and validate multiple API resources.
    - After creating them, it checks each one to make sure it actually exists and is correct.
    - If any check fails, the function reports which resources failed.

    Args:
        create_fn (Callable[[], Tuple[str, dict]] or Callable[[int], Tuple[str, dict]]):
            A function that creates a single resource.
            - Returns:
                - identifier (e.g., email or ID) to use in validation
                - metadata (dict) for logging/debugging (optional, not used here)

        validate_fn (Callable[[str], None]): A function that validates the resource exists
            and is correct via API and DB.

        qty (int): Number of resources to create and validate.

        label (str): Label used for logging output (e.g., "customers", "product").
    """

    # Stores all unique identifiers returned by create_fn (e.g., customers emails)
    identifiers = []
    logger.info(f"🧪 Starting bulk create+validate for {qty} {label}(s)")

    # ------------------------------------------
    # 🔁 Step 1: Create Resources in a Loop
    # -----------------------------------------
    for n in range(qty):
        # It runs create_fn() exactly qty times.
        # It logs creation progress.
        # It saves all identifiers for later validation.
        logger.info(f"➕ Creating {label} {n + 1}/{qty}")
        identifier, _ = create_fn()
        # In Python, the underscore (_) is often used as a "throwaway variable" — a
        # variable that you’re deliberately choosing to ignore. You're calling create_fn(i) — which returns a tuple
        # like: (email, { "id": ..., "resource_type": ... })  You care about the first item (email), which you're
        # naming identifier. You don't need the second item (the metadata), so you use _ to indicate that
        #  It’s Pythonic shorthand to say: “I’m discarding this part of the result intentionally.”

        # Ensure creation succeeded — if not, fail fast
        assert identifier, f"❌ Failed to create {label} #{n + 1}"
        # Save the identifier for later validation
        identifiers.append(identifier)

    # ------------------------------------------
    # 🔍 Step 2: Validate All Created Resources
    # ------------------------------------------
    logger.info(f"🔍 Validating {qty} created {label}(s)")
    errors = []

    for identifier in identifiers:  # For each created identifier (email), run validate_fn() on it.
        try:
            # Call the provided validation function
            validate_fn(identifier)
        except AssertionError as e:  # Any failure is caught and saved, but doesn’t stop the test immediately
            # (so you see all errors at once). Collect validation errors but don’t fail immediately
            errors.append(str(e))

    # ❌ If any errors occurred, fail the test and report all of them
    assert not errors, f"❌ Validation failed for some {label}s:\n" + "\n".join(errors)

    logger.info(f"✅ All {qty} {label}(s) created and validated successfully")

    return identifiers


# 1️⃣	Define how to create a resource	create_fn() inside test
# 2️⃣	Define how to validate it	validate_fn() inside test
# 3️⃣	Loop: create N customers	Inside bulk_create_and_validate_resources()
# 4️⃣	Loop: validate each one	Inside bulk_create_and_validate_resources()
# 5️⃣	Assert all validations passed	Final step of the utility

