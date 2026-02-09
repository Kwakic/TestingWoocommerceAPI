# schemas.py — JSON Schema definitions for WooCommerce resources

# 🧪 Example Usage in a Test:
# from EcommerceAPI.src.utilities.wooAPIUtility import WooAPIUtility
# from EcommerceAPI.data.schemas import product_schema, order_schema, customer_schema, coupon_schema
# Example:
# def test_product_schema_validation():
#     api = WooAPIUtility()
#     products = api.get("products", schema={"type": "array"})
#     if products:
#         api.get(f"products/{products[0]['id']}", schema=product_schema)

order_schema = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "status": {"type": "string"},
        "line_items": {"type": "array"},
        "payment_method": {"type": "string"},
        "billing": {"type": "object"},
        "shipping": {"type": "object"}
    },
    "required": ["id", "status", "line_items", "payment_method"]
}
