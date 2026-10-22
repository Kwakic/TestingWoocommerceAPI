# structure validation only
"""
Customer Pydantic Models (RUNTIME STRUCTURE VALIDATION LAYER)

🎯 Purpose
---------------------------------------------------------------------
Define the expected structure of customers objects returned by the API.

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

    customer_model = CustomerModel(**customer_dict)

If validation fails → Pydantic raises ValidationError.

📌 Notes
---------------------------------------------------------------------
• WooCommerce APIs frequently return empty strings instead of null.
• A global normalizer converts "" → None to prevent validation errors.
• Error payloads are still validated via JSON schema.

---------------------------------------------------------------------
When you need a dict (for DB validators):
Use:
    customers.model_dump()

"""
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, EmailStr, ConfigDict, model_validator


# ============================================================
# Base API Model
# ============================================================


class APIModel(BaseModel):
    """
    Base model used by all API response models.

    Provides shared behavior:

    • Allows unknown fields (future-proof for API evolution)
    • Normalizes empty strings returned by APIs like WooCommerce
    • Enables assignment validation
    """

    model_config = ConfigDict(
        extra="allow",  # Allow unknown API fields
        frozen=True,  # Prevent any field change. Make an object immutable
        # validate_assignment=True  # Validate when fields are changed. Note: If the model is frozen, mutation is
        # impossible, so validate_assignment becomes useless.
    )

    @model_validator(mode="before")
    def normalize_empty_strings(cls, values):
        """
        Normalize WooCommerce responses that use "" instead of null.

        Example:
            ""  →  None

        This prevents validation errors for Optional fields such as
        email, phone, postcode, etc.
        """
        if isinstance(values, dict):
            return {k: (None if v == "" else v) for k, v in values.items()}
        return values


# ============================================================
# Address Model
# ============================================================


class AddressModel(APIModel):
    """
    Represents billing or shipping address information.
    """

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    address_1: Optional[str] = None
    address_2: Optional[str] = None
    company: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postcode: Optional[str] = None
    country: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


# ============================================================
# Customer Model
# ============================================================


class CustomerModel(APIModel):
    """
    Represents a Customer object returned by the API.

    Validation includes:
    • required fields (`id`, `email`)
    • nested address objects
    • optional WooCommerce fields
    • email validation via `EmailStr`

    This model converts a raw API dictionary into a strongly typed object.

    This provides:
        - type validation
        - email validation
        - nested object validation
        - optional fields support

    CustomerModel takes a dictionary and validates + parses it into a structured Python object.
    Step-by-step:
        - 📥 Input = dictionary (API response)
        - 🧱 Pydantic validates it
        - 🔄 Pydantic parses / transforms it
        - 📦 Output = CustomerModel object (not dict anymore)
    """

    id: int
    email: EmailStr

    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    billing: AddressModel
    shipping: AddressModel

    date_created: Optional[str] = None
    date_created_gmt: Optional[str] = None
    date_modified: Optional[str] = None
    date_modified_gmt: Optional[str] = None

    is_paying_customer: Optional[bool] = None
    avatar_url: Optional[str] = None
    role: Optional[str] = None

    meta_data: Optional[List[Dict[str, Any]]] = None
    _links: Optional[Dict[str, Any]] = None

    def __repr__(self):
        """
        Compact representation used in logs and assertion errors.

        Example:
            CustomerModel(id=1457, email=test@example.com)
        """
        return f"CustomerModel(id={self.id}, email={self.email})"
