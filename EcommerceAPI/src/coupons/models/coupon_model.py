from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, model_validator


# ============================================================
# Base API Model
# ============================================================


class APIModel(BaseModel):
    """
    Base model used by API response models.

    Provides shared behavior:

    • Allows unknown fields for API evolution
    • Normalizes empty strings returned by WooCommerce
    • Prevents accidental mutation
    """

    model_config = ConfigDict(
        extra="allow",
        frozen=True,
    )

    @model_validator(mode="before")
    def normalize_empty_strings(cls, values):
        """
        Normalize WooCommerce responses that use "" instead of null.

        Example:
            "" → None
        """
        if isinstance(values, dict):
            return {
                key: (None if value == "" else value) for key, value in values.items()
            }

        return values


# ============================================================
# Metadata Model
# ============================================================


class MetaDataModel(APIModel):
    """
    Represents a WooCommerce metadata entry.
    """

    id: Optional[int] = None
    key: Optional[str] = None
    value: Optional[Any] = None


# ============================================================
# Coupon Model
# ============================================================


class CouponModel(APIModel):
    """
    Represents a WooCommerce coupon returned by the REST API.

    This model validates structure only.

    It does NOT contain:
        • business rules
        • discount calculations
        • database logic
        • API calls
        • test assertions
    """

    # -----------------------------------------------------------------
    # Required fields
    # -----------------------------------------------------------------

    id: int
    code: str
    amount: str
    discount_type: str

    # -----------------------------------------------------------------
    # Basic information
    # -----------------------------------------------------------------

    date_created: Optional[str] = None
    date_created_gmt: Optional[str] = None

    date_modified: Optional[str] = None
    date_modified_gmt: Optional[str] = None

    date_expires: Optional[str] = None
    date_expires_gmt: Optional[str] = None

    description: Optional[str] = None

    # -----------------------------------------------------------------
    # Usage
    # -----------------------------------------------------------------

    usage_count: Optional[int] = None

    individual_use: Optional[bool] = None

    usage_limit: Optional[int] = None
    usage_limit_per_user: Optional[int] = None
    limit_usage_to_x_items: Optional[int] = None

    # -----------------------------------------------------------------
    # Product restrictions
    # -----------------------------------------------------------------

    product_ids: Optional[List[int]] = None
    excluded_product_ids: Optional[List[int]] = None

    product_categories: Optional[List[int]] = None
    excluded_product_categories: Optional[List[int]] = None

    exclude_sale_items: Optional[bool] = None

    # -----------------------------------------------------------------
    # Shipping
    # -----------------------------------------------------------------

    free_shipping: Optional[bool] = None

    # -----------------------------------------------------------------
    # Amount restrictions
    # -----------------------------------------------------------------

    minimum_amount: Optional[str] = None
    maximum_amount: Optional[str] = None

    # -----------------------------------------------------------------
    # Customer restrictions
    # -----------------------------------------------------------------

    email_restrictions: Optional[List[str]] = None

    used_by: Optional[List[Any]] = None

    # -----------------------------------------------------------------
    # Metadata
    # -----------------------------------------------------------------

    meta_data: Optional[List[MetaDataModel]] = None

    # -----------------------------------------------------------------
    # Links
    # -----------------------------------------------------------------

    _links: Optional[Dict[str, Any]] = None

    # -----------------------------------------------------------------
    # Representation
    # -----------------------------------------------------------------

    def __repr__(self):
        return (
            f"CouponModel("
            f"id={self.id}, "
            f"code='{self.code}', "
            f"amount='{self.amount}', "
            f"discount_type='{self.discount_type}')"
        )
