"""
JSON Schema definitions for WooCommerce coupon resources.

This module exposes:
- coupon_schema: schema to validate a coupon resource returned by the API
- error_schema: schema to validate typical WooCommerce error responses (so helpers can import it safely)

Note:
- error_schema mirrors the general error schema used across other resource models to keep validation
  consistent when helpers validate error responses.
"""

# Basic coupon schema (keeps lenient behavior to allow API evolution)
coupon_schema = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "code": {"type": "string"},
        "amount": {"type": "string"},
        "discount_type": {"type": "string"},
        "date_created": {"type": "string"},
        "date_modified": {"type": "string"},
        "description": {"type": "string"},
        "usage_count": {"type": "integer"},
        "individual_use": {"type": "boolean"},
        "product_ids": {"type": "array", "items": {"type": "integer"}},
        "excluded_product_ids": {"type": "array", "items": {"type": "integer"}},
        "usage_limit": {"type": ["integer", "null"]},
        "usage_limit_per_user": {"type": ["integer", "null"]},
        "limit_usage_to_x_items": {"type": ["integer", "null"]},
        "free_shipping": {"type": "boolean"},
        "product_categories": {"type": "array"},
        "exclude_product_categories": {"type": "array"},
        "minimum_amount": {"type": "string"},
        "maximum_amount": {"type": "string"},
        "email_restrictions": {"type": "array", "items": {"type": "string"}},
        "meta_data": {"type": "array"},
        "_links": {"type": "object"},
    },
    "required": ["id", "code", "amount", "discount_type"],
    # Allow extra properties so tests don't break when WooCommerce adds fields
    "additionalProperties": True,
}

# Standard WooCommerce error response schema (kept here for helpers that import it)
# Typical error shape:
# {
#   "code": "woocommerce_rest_invalid_email",
#   "message": "Email address is invalid.",
#   "data": {
#       "status": 400,
#       "params": ["email"]
#   }
# }
error_schema = {
    "type": "object",
    "properties": {
        "code": {
            "type": "string",
            "description": "Machine-readable error code (e.g., 'woocommerce_rest_invalid_email')",
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
                    "description": "Optional list of invalid parameters or object with details",
                    "oneOf": [
                        {"type": "array", "items": {"type": "string"}},
                        {"type": "object"},  # Accepts {"email": "..."} or similar
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
