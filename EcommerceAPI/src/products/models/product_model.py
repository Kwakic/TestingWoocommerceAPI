from typing import Optional, List, Dict, Any
from pydantic import BaseModel


# ============================================================
# Supporting Models
# ============================================================

class ImageModel(APIModel):
    id: Optional[int] = None
    src: Optional[str] = None
    name: Optional[str] = None
    alt: Optional[str] = None


class CategoryModel(APIModel):
    id: int
    name: Optional[str] = None
    slug: Optional[str] = None


class MetaDataModel(APIModel):
    id: Optional[int] = None
    key: Optional[str] = None
    value: Optional[Any] = None


# ============================================================
# Product Model
# ============================================================

class ProductModel(APIModel):
    """
    Represents a WooCommerce Product object.

    Structure validation only (no business logic).

    Covers:
    • Core product fields
    • Pricing
    • Inventory
    • Relationships (categories, images)
    """

    # --- Core पहचान ---
    id: int
    name: str
    slug: Optional[str] = None
    permalink: Optional[str] = None

    # --- Dates ---
    date_created: Optional[str] = None
    date_created_gmt: Optional[str] = None
    date_modified: Optional[str] = None
    date_modified_gmt: Optional[str] = None

    # --- Status / Type ---
    type: Optional[str] = None
    status: Optional[str] = None
    featured: Optional[bool] = None
    catalog_visibility: Optional[str] = None

    # --- Descriptions ---
    description: Optional[str] = None
    short_description: Optional[str] = None

    # --- SKU / Pricing ---
    sku: Optional[str] = None
    price: Optional[str] = None
    regular_price: Optional[str] = None
    sale_price: Optional[str] = None
    on_sale: Optional[bool] = None

    # --- Inventory ---
    manage_stock: Optional[bool] = None
    stock_quantity: Optional[int] = None
    stock_status: Optional[str] = None

    # --- Dimensions ---
    weight: Optional[str] = None
    dimensions: Optional[Dict[str, Any]] = None  # keep flexible

    # --- Relationships ---
    categories: Optional[List[CategoryModel]] = None
    images: Optional[List[ImageModel]] = None

    # --- Metadata ---
    meta_data: Optional[List[MetaDataModel]] = None

    # --- Links ---
    _links: Optional[Dict[str, Any]] = None

    def __repr__(self):
        return f"ProductModel(id={self.id}, name='{self.name}', sku='{self.sku}')"