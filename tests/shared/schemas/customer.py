# schemas.py — JSON Schema definitions for WooCommerce resources

customer_schema = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "email": {"type": "string"},
        "first_name": {"type": "string"},
        "last_name": {"type": "string"},
        "username": {"type": "string"},
        "date_created": {"type": "string"},
        "date_created_gmt": {"type": "string"},
        "date_modified": {"type": "string"},
        "date_modified_gmt": {"type": "string"},
        "is_paying_customer": {"type": "boolean"},
        "avatar_url": {"type": "string"},
        "meta_data": {"type": "array"},
        "role": {"type": "string"},
        "_links": {"type": "object"},  # You could add details, but optional

        "billing": {
            "type": "object",
            "properties": {
                "first_name": {"type": "string"},
                "last_name": {"type": "string"},
                "address_1": {"type": "string"},
                "address_2": {"type": "string"},
                "company": {"type": "string"},
                "city": {"type": "string"},
                "state": {"type": "string"},
                "postcode": {"type": "string"},
                "country": {"type": "string"},
                "email": {"type": "string"},
                "phone": {"type": "string"}
            },
            "required": ["first_name", "last_name", "address_1", "city", "state", "postcode", "country"],
            "additionalProperties": False
        },

        "shipping": {
            "type": "object",
            "properties": {
                "first_name": {"type": "string"},
                "last_name": {"type": "string"},
                "address_1": {"type": "string"},
                "address_2": {"type": "string"},
                "company": {"type": "string"},
                "city": {"type": "string"},
                "state": {"type": "string"},
                "postcode": {"type": "string"},
                "country": {"type": "string"},
                "phone": {"type": "string"}
            },
            "required": ["first_name", "last_name", "address_1", "city", "state", "postcode", "country"],
            "additionalProperties": False
        }
    },
    "required": ["id", "email", "billing", "shipping"],
    "additionalProperties": True  # ✅ Allow WooCommerce to evolve without breaking tests. They might add new properties
}
#
# # 🧠 Why Use "additionalProperties": true?
# #     ✅ Allows WooCommerce to return extra fields (like _links, meta_data)
# #     ✅ Avoids brittle tests that fail on schema updates
# #     ✅ Still validates expected fields strictly
#

# schemas.py

# ❗ Error response format expected from WooCommerce:
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
            "description": "Machine-readable error code (e.g., 'woocommerce_rest_invalid_email')"
        },
        "message": {
            "type": "string",
            "description": "Human-readable error message"
        },
        "data": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "integer",
                    "description": "HTTP status code (typically 400 or 500)"
                },
                "params": {
                    "description": "Optional list of invalid parameters or object with details",
                    "oneOf": [
                        {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        {
                            "type": "object"  # Accepts {"email": "..."} or similar
                        }
                    ]
                }
            },
            "required": ["status"],
            "additionalProperties": True  # ✅ Allow WooCommerce to evolve without breaking tests
        }
    },
    "required": ["code", "message", "data"],
    "additionalProperties": False  # ❌ Fail if unexpected root-level fields appear
}


# Validates:
#     ✅ Presence of id and email (if "required" is specified)
#     ✅ Data type (e.g., "email" must be a string)
#     ❌ Does not fail if extra/unexpected properties appear (this is the default)
# To make the schema strict, add "additionalProperties": False
# ✅ customer_schema with "additionalProperties": false and nested billing/shipping strict validation
# ✅ error_schema matching WooCommerce's typical error responses
