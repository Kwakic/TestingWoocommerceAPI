"""
JSON Schema for WooCommerce product resource (relaxed regular_price)

Notes:
- regular_price is NOT mandatory for all product types (e.g., variable/grouped parents,
  placeholder products). The schema will validate:
    - numeric price strings like "12.99"
    - empty string "" when no price is set
    - null (if the API returns null)
- The schema allows additionalProperties at the root level (like your customers schema),
  so WooCommerce can evolve without breaking these preflight checks.
- An `product_error_schema` is provided to match typical WooCommerce error responses
  (same style as your existing error_schema in the customers schema).
"""

from typing import Dict, Any

# Schema for normal product object responses
product_schema: Dict[str, Any] = {
    "type": "object",
    # core fields we expect to be present for product objects in single-item GETs
    "required": ["id", "name", "type", "status"],
    "properties": {
        "id": {"type": "integer"},
        "name": {"type": "string"},
        "type": {
            "type": "string",
            "enum": ["simple", "grouped", "external", "variable"],
        },
        # regular_price may be:
        #   - a numeric string (e.g. "12.99")
        #   - an empty string "" if no price is set on this product
        #   - null if the API uses null for missing values
        "regular_price": {
            "anyOf": [
                {"type": "string", "pattern": r"^\d+(\.\d{1,2})?$"},
                {"type": "string", "enum": [""]},
                {"type": "null"},
            ],
            "description": "Product's regular price as string (may be empty or null when unset)",
        },
        "status": {"type": "string"},
        # common additional properties that may appear; we keep them permissive
        "sku": {"type": ["string", "null"]},
        "price": {"type": ["string", "null"]},  # sometimes used as current price
        "permalink": {"type": "string"},
        "date_created": {"type": "string"},
        "date_created_gmt": {"type": "string"},
        # more properties can be added here as needed
        "_links": {"type": "object"},
    },
    # allow WooCommerce to add new fields without breaking this preflight check
    "additionalProperties": True,
}

# Schema for error responses that some endpoints return (same style as your error_schema)
product_error_schema: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "code": {
            "type": "string",
            "description": "Machine-readable error code (e.g., 'woocommerce_rest_invalid_param')",
        },
        "message": {"type": "string", "description": "Human-readable error message"},
        "data": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "integer",
                    "description": "HTTP status code (typically 400 or 500)",
                },
                "params": {
                    "description": "Optional list of invalid params or extra data",
                    "oneOf": [
                        {"type": "array", "items": {"type": "string"}},
                        {"type": "object"},
                    ],
                },
            },
            "required": ["status"],
            "additionalProperties": True,
        },
    },
    "required": ["code", "message", "data"],
    "additionalProperties": False,
}
