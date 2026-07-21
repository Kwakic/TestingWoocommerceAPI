# contract validation

import logging
from typing import Dict

from EcommerceAPI.src.products.models.product_model import ProductModel

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# 🗄️ DB VALIDATION (PURE BUSINESS LOGIC)
# ------------------------------------------------------------------
# IMPORTANT:
# At this stage we ASSUME structure is already validated.
# So we use strict access (obj["key"]) instead of .get() to enforce contract correctness.
# ------------------------------------------------------------------
def assert_product_matches_db(
    product: ProductModel, db_product: Dict[str, any]
) -> None:
    """
    Validate that the API products object matches the corresponding database record.

    This validator performs **pure business validation**.

    Structure is already guaranteed by Pydantic.

    Important design rule:
        At this stage, the API response structure is already validated.
        Therefore, we can safely access model fields directly.

    Args:
        product (ProductModel):
            Validated products object returned by API validators.

        db_product(Dict[str, Any]):
            product record retrieved from the database via DAO.

    Raises:
        AssertionError:
            If the database record is missing or inconsistent
            with the API response.
    """

    # -------------------------------------------------------
    # 🗄️ Ensure DB record exists
    # -------------------------------------------------------
    assert db_product, "❌ No DB record found for products"

    # -------------------------------------------------------
    # 🧪 BUSINESS VALIDATION
    # -------------------------------------------------------
    # Compare API data with database values.

    assert str(db_product["ID"]) == str(product.id), "❌ DB ID does not match API ID"

    assert db_product["post_title"] == product.name, (
        f"Product title mismatch. "
        f"DB='{db_product['post_title']}' "
        f"API='{product.name}'"
    )

    # logger.info(
    #     "✅ Assertion passed: API products matches DB record (ID=%s)", product.id
    # )
