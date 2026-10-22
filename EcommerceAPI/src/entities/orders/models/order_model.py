"""
Order Pydantic models (runtime structure validation layer).

These models describe WooCommerce REST API v3 Order responses. They validate
response structure and provide typed nested objects for Order data such as
billing and shipping addresses, line items, taxes, and refunds.

Design rules
------------
- Models validate response structure only; they do not contain Order
  business rules or perform assertions.
- Models do not make API calls or access the database.
- Unknown response properties are allowed so extensions can add fields
  without invalidating the base WooCommerce response model.
- Empty strings are normalized to ``None`` to match the other API models in
  this project.
- ``set_paid`` is a write-only request property in the WooCommerce API and is
  therefore not part of this response model.

Typical usage from an Order validator::

    order = OrderModel.model_validate(order_response)

If the response has an invalid structure, Pydantic raises
``ValidationError``. To obtain a dictionary, use ``order.model_dump()``.

The field definitions follow the WooCommerce Order response properties and
the nested response example in the REST API documentation:
https://developer.woocommerce.com/docs/apis/rest-api/v3/orders/
"""

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator


class APIModel(BaseModel):
    """Base class for WooCommerce API response models in this module.

    It allows additional API fields, normalizes empty strings, and prevents
    mutation after a response has been parsed.
    """

    model_config = ConfigDict(
        extra="allow",
        frozen=True,
    )

    @model_validator(mode="before")
    def normalize_empty_strings(cls, values):
        """Normalize empty string values to ``None`` before field parsing.

        WooCommerce may return empty strings for optional response values,
        such as an unset payment method or address field.
        """
        if isinstance(values, dict):
            return {
                key: (None if value == "" else value) for key, value in values.items()
            }

        return values


class OrderAddressModel(APIModel):
    """Represent a billing or shipping address attached to an Order."""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    address_1: Optional[str] = None
    address_2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postcode: Optional[str] = None
    country: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class OrderMetaDataModel(APIModel):
    """Represent one WooCommerce Order metadata entry."""

    id: Optional[int] = None
    key: Optional[str] = None
    value: Optional[Any] = None


class OrderLineItemImageModel(APIModel):
    """Represent the product image included with a returned line item."""

    # WooCommerce documents image IDs as either integers or numeric strings.
    id: Optional[Union[int, str]] = None
    # The API may return false when an attachment cannot be resolved.
    src: Optional[Union[str, bool]] = None


class OrderLineItemTaxModel(APIModel):
    """Represent one tax amount applied to a line item."""

    id: Optional[int] = None
    total: Optional[str] = None
    subtotal: Optional[str] = None


class OrderLineItemModel(APIModel):
    """Represent a product line returned as part of an Order."""

    # -----------------------------------------------------------------
    # Required response fields
    # -----------------------------------------------------------------

    id: int
    name: str
    product_id: int
    quantity: int

    # -----------------------------------------------------------------
    # Product and pricing information
    # -----------------------------------------------------------------

    parent_name: Optional[str] = None
    variation_id: Optional[int] = None
    tax_class: Optional[str] = None
    subtotal: Optional[str] = None
    subtotal_tax: Optional[str] = None
    total: Optional[str] = None
    total_tax: Optional[str] = None

    # The REST API documents price as a string, while its response example
    # includes a numeric value. Accept both documented representations.
    price: Optional[Union[str, int, float]] = None

    # -----------------------------------------------------------------
    # Related response data
    # -----------------------------------------------------------------

    taxes: Optional[List[OrderLineItemTaxModel]] = None
    meta_data: Optional[List[OrderMetaDataModel]] = None
    sku: Optional[str] = None
    global_unique_id: Optional[str] = None
    image: Optional[OrderLineItemImageModel] = None


class OrderTaxLineModel(APIModel):
    """Represent a tax line aggregated on the Order."""

    id: Optional[int] = None
    rate_code: Optional[str] = None
    rate_id: Optional[int] = None
    label: Optional[str] = None
    compound: Optional[bool] = None
    tax_total: Optional[str] = None
    shipping_tax_total: Optional[str] = None
    meta_data: Optional[List[OrderMetaDataModel]] = None


class OrderShippingLineModel(APIModel):
    """Represent a shipping method and its totals on the Order."""

    id: Optional[int] = None
    method_title: Optional[str] = None
    method_id: Optional[str] = None
    total: Optional[str] = None
    total_tax: Optional[str] = None
    taxes: Optional[List[OrderLineItemTaxModel]] = None
    meta_data: Optional[List[OrderMetaDataModel]] = None


class OrderFeeLineModel(APIModel):
    """Represent a fee included in the Order."""

    id: Optional[int] = None
    name: Optional[str] = None
    tax_class: Optional[str] = None
    tax_status: Optional[str] = None
    total: Optional[str] = None
    total_tax: Optional[str] = None
    taxes: Optional[List[OrderLineItemTaxModel]] = None
    meta_data: Optional[List[OrderMetaDataModel]] = None


class OrderCouponLineModel(APIModel):
    """Represent a coupon applied to the Order."""

    id: Optional[int] = None
    code: Optional[str] = None
    discount: Optional[str] = None
    discount_tax: Optional[str] = None
    meta_data: Optional[List[OrderMetaDataModel]] = None


class OrderRefundModel(APIModel):
    """Represent a refund associated with the Order."""

    id: int
    reason: Optional[str] = None
    total: Optional[str] = None


class OrderModel(APIModel):
    """Represent a WooCommerce Order object returned by the REST API.

    The model validates the main Order response fields and their nested
    structures. It does not check whether a status transition, payment, total,
    or other value is valid for a particular business scenario.

    Required response fields are ``id``, ``order_key``, ``status``,
    ``currency``, ``customer_id``, ``payment_method``, and ``line_items``.
    ``payment_method`` is required in the response, but may be ``None`` after
    the shared normalizer processes an empty string.

    Example:

        order = OrderModel.model_validate(order_response)
        order_id = order.id
        first_product_id = order.line_items[0].product_id

    The response's ``_links`` property is available as ``links`` on this
    model because Pydantic reserves leading-underscore attributes.
    """

    # -----------------------------------------------------------------
    # Required identity and status fields
    # -----------------------------------------------------------------

    id: int
    order_key: str
    status: str
    currency: str
    customer_id: int
    payment_method: Optional[str]

    # -----------------------------------------------------------------
    # Order identifiers and origin
    # -----------------------------------------------------------------

    parent_id: Optional[int] = None
    number: Optional[str] = None
    created_via: Optional[str] = None
    version: Optional[str] = None

    # -----------------------------------------------------------------
    # Dates and totals
    # -----------------------------------------------------------------

    date_created: Optional[str] = None
    date_created_gmt: Optional[str] = None
    date_modified: Optional[str] = None
    date_modified_gmt: Optional[str] = None
    date_paid: Optional[str] = None
    date_paid_gmt: Optional[str] = None
    date_completed: Optional[str] = None
    date_completed_gmt: Optional[str] = None

    discount_total: Optional[str] = None
    discount_tax: Optional[str] = None
    shipping_total: Optional[str] = None
    shipping_tax: Optional[str] = None
    cart_tax: Optional[str] = None
    total: Optional[str] = None
    total_tax: Optional[str] = None
    prices_include_tax: Optional[bool] = None

    # -----------------------------------------------------------------
    # Customer and payment information
    # -----------------------------------------------------------------

    customer_ip_address: Optional[str] = None
    customer_user_agent: Optional[str] = None
    customer_note: Optional[str] = None
    payment_method_title: Optional[str] = None
    transaction_id: Optional[str] = None
    cart_hash: Optional[str] = None

    # -----------------------------------------------------------------
    # Addresses and line data
    # -----------------------------------------------------------------

    billing: Optional[OrderAddressModel] = None
    shipping: Optional[OrderAddressModel] = None
    line_items: List[OrderLineItemModel]
    tax_lines: Optional[List[OrderTaxLineModel]] = None
    shipping_lines: Optional[List[OrderShippingLineModel]] = None
    fee_lines: Optional[List[OrderFeeLineModel]] = None
    coupon_lines: Optional[List[OrderCouponLineModel]] = None
    refunds: Optional[List[OrderRefundModel]] = None
    meta_data: Optional[List[OrderMetaDataModel]] = None

    # WooCommerce returns this key with a leading underscore. Use a regular
    # Python attribute while preserving the API key as the validation alias.
    links: Optional[Dict[str, Any]] = Field(default=None, alias="_links")

    def __repr__(self):
        """Return a compact representation for logs and assertion errors.

        Example:
            OrderModel(id=727, status='processing', customer_id=0)
        """
        return (
            f"OrderModel("
            f"id={self.id}, "
            f"status='{self.status}', "
            f"customer_id={self.customer_id})"
        )
