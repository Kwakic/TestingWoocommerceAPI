# structure validation only
"""
Product Pydantic Models (RUNTIME STRUCTURE VALIDATION LAYER)

🎯 Purpose
---------------------------------------------------------------------
Define the expected structure of product objects returned by the API.

These models replace JSON Schema validation and provide:

• type validation
• nested object validation
• strong typing for tests
• cleaner error messages
• IDE autocomplete support

🧠 Design Rules
---------------------------------------------------------------------
• Models validate **structure only**
• NO business logic
• NO DB logic
• Used internally by validators

Typical usage (inside validators):

    product_model = ProductModel(**product_dict)

If validation fails → Pydantic raises ValidationError.

📌 Notes
---------------------------------------------------------------------
• WooCommerce APIs frequently return empty strings instead of null.
• A global normalizer converts "" → None to prevent validation errors.
• Error payloads are still validated via JSON schema.

---------------------------------------------------------------------
When you need a dict (for DB validators):
Use:
    product.model_dump()

"""

from typing import Optional, List, Dict, Any

from pydantic import BaseModel, ConfigDict, model_validator


# ============================================================
# Base API Model
# ============================================================


class APIModel(BaseModel):
    """
    Base model used by all API response models.

    Provides shared behavior:

    • Allows unknown fields (future-proof for API evolution)
    • Normalizes empty strings returned by APIs like WooCommerce
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
            return {k: (None if v == "" else v) for k, v in values.items()}
        return values


# ============================================================
# Dimension Model
# ============================================================


class DimensionModel(APIModel):
    """
    Represents product dimensions.
    """

    length: Optional[str] = None
    width: Optional[str] = None
    height: Optional[str] = None


# ============================================================
# Category Model
# ============================================================


class CategoryModel(APIModel):
    """
    Represents a product category.
    """

    id: int
    name: Optional[str] = None
    slug: Optional[str] = None


# ============================================================
# Tag Model
# ============================================================


class TagModel(APIModel):
    """
    Represents a product tag.
    """

    id: int
    name: Optional[str] = None
    slug: Optional[str] = None


# ============================================================
# Image Model
# ============================================================


class ImageModel(APIModel):
    """
    Represents a product image.
    """

    id: Optional[int] = None
    src: Optional[str] = None
    name: Optional[str] = None
    alt: Optional[str] = None


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
# Product Model
# ============================================================


class ProductModel(APIModel):
    """
    Represents a Product object returned by the API.

    Validation includes:
    • required fields (`id`, `name`)
    • nested category objects
    • nested image objects
    • optional WooCommerce product fields

    This model converts a raw API dictionary into a strongly typed object.

    This provides:
        - type validation
        - nested object validation
        - optional fields support

    ProductModel takes a dictionary and validates + parses it into a
    structured Python object.

    Step-by-step:
        - 📥 Input = dictionary (API response)
        - 🧱 Pydantic validates it
        - 🔄 Pydantic parses / transforms it
        - 📦 Output = ProductModel object (not dict anymore)
    """

    # -----------------------------------------------------------------
    # Required fields
    # -----------------------------------------------------------------

    id: int
    name: str

    # -----------------------------------------------------------------
    # Basic information
    # -----------------------------------------------------------------

    slug: Optional[str] = None
    permalink: Optional[str] = None

    type: Optional[str] = None
    status: Optional[str] = None
    featured: Optional[bool] = None
    catalog_visibility: Optional[str] = None

    description: Optional[str] = None
    short_description: Optional[str] = None

    sku: Optional[str] = None

    # -----------------------------------------------------------------
    # Pricing
    # -----------------------------------------------------------------

    price: Optional[str] = None
    regular_price: Optional[str] = None
    sale_price: Optional[str] = None
    on_sale: Optional[bool] = None

    # -----------------------------------------------------------------
    # Inventory
    # -----------------------------------------------------------------

    manage_stock: Optional[bool] = None
    stock_quantity: Optional[int] = None
    stock_status: Optional[str] = None

    # -----------------------------------------------------------------
    # Physical properties
    # -----------------------------------------------------------------

    weight: Optional[str] = None
    dimensions: Optional[DimensionModel] = None

    # -----------------------------------------------------------------
    # Dates
    # -----------------------------------------------------------------

    date_created: Optional[str] = None
    date_created_gmt: Optional[str] = None
    date_modified: Optional[str] = None
    date_modified_gmt: Optional[str] = None

    # -----------------------------------------------------------------
    # Relationships
    # -----------------------------------------------------------------

    categories: Optional[List[CategoryModel]] = None
    tags: Optional[List[TagModel]] = None
    images: Optional[List[ImageModel]] = None

    # -----------------------------------------------------------------
    # Metadata
    # -----------------------------------------------------------------

    meta_data: Optional[List[MetaDataModel]] = None
    _links: Optional[Dict[str, Any]] = None

    def __repr__(self):
        """
        Compact representation used in logs and assertion errors.

        Example:
            ProductModel(id=1457, name='Beanie', sku='woo-beanie')
        """
        return (
            f"ProductModel("
            f"id={self.id}, "
            f"name='{self.name}', "
            f"sku='{self.sku}')"
        )
