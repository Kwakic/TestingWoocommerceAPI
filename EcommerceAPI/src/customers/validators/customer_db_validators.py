# contract validation

import logging
from typing import Dict

from EcommerceAPI.src.customers.models.customer_model import CustomerModel

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# 🗄️ DB VALIDATION (PURE BUSINESS LOGIC)
# ------------------------------------------------------------------
# IMPORTANT:
# At this stage we ASSUME structure is already validated.
# So we use strict access (obj["key"]) instead of .get() to enforce contract correctness.
# ------------------------------------------------------------------
def assert_customer_matches_db(
    customer: CustomerModel, db_customer: Dict[str, any]
) -> None:
    """
    Validate that the API customers object matches the corresponding database record.

    This validator performs **pure business validation**.

    Structure is already guaranteed by Pydantic.

    Important design rule:
        At this stage, the API response structure is already validated.
        Therefore, we can safely access model fields directly.

    Args:
        customer (CustomerModel):
            Validated customers object returned by API assertions.

        db_customer (Dict[str, Any]):
            Customer record retrieved from the database via DAO.

    Raises:
        AssertionError:
            If the database record is missing or inconsistent
            with the API response.
    """

    # -------------------------------------------------------
    # 🗄️ Ensure DB record exists
    # -------------------------------------------------------
    assert db_customer, "❌ No DB record found for customers"

    # -------------------------------------------------------
    # 🧪 BUSINESS VALIDATION
    # -------------------------------------------------------
    # Compare API data with database values.

    assert str(db_customer["ID"]) == str(customer.id), "❌ DB ID does not match API ID"

    assert (
        db_customer["user_email"] == customer.email
    ), "❌ DB email does not match API email"

    logger.info(
        "✅ Assertion passed: API customers matches DB record (ID=%s)", customer.id
    )
