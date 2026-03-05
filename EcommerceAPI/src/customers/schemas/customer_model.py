# structure validation only
"""
Customer Pydantic Model (STRUCTURE VALIDATION LAYER)

🎯 Purpose:
- Define the expected structure of a customer object returned by API
- Replace jsonschema validation over time
- Provide type safety and better error messages

🧠 Design Rules:
- This model ONLY validates structure (types, required fields)
- NO business logic here
- Used by validators (NOT directly by tests initially)

📌 Usage (internal):
    CustomerModel(**customer_dict)

If validation fails → raises ValidationError

🚫 Do NOT:
- Add business rules here
- Add DB logic
- Use this directly in tests (for now)
"""

from pydantic import BaseModel, EmailStr


class CustomerModel(BaseModel):
    """
    Represents a Customer object returned by the API.

    Minimal required fields for validation.

    CustomerModel takes a dictionary and validates + parses it into a structured Python object.
    Step-by-step:
        - 📥 Input = dictionary (API response)
        - 🧱 Pydantic validates it
        - 🔄 Pydantic parses / transforms it
        - 📦 Output = CustomerModel object (not dict anymore)
    """

    id: int
    email: EmailStr
    username: str
    # username: Optional[str] = None
