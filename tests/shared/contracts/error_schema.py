# error_schema.py — JSON Schema definitions for WooCommerce resources

"""
Error schema validator - test contract validation

It checks if:
  - keys exist
  - values not empty
  - response is dict
  - status exists

Your schema checks structure strictly:
    - correct types
    - required fields
    - nested objects
    - allowed shapes

Example from your schema:
    - "code" must be a string
    - "message" must be a string
    - "data.status" must be an integer
    - "params" must be either array OR object


Error response format expected from WooCommerce:
    {
      "code": "woocommerce_rest_invalid_email",
      "message": "Email address is invalid.",
      "data": {
          "status": 400,
          "params": ["email"]
      }
    }

"""

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
