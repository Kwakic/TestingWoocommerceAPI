"""
Centralized custom exceptions for the test framework.
Put framework-wide exceptions here so they may be imported from multiple places:
    from EcommerceAPI.src.utils.exceptions import SchemaValidationError, UnexpectedStatusCodeError
"""


class APIRequestException(Exception):
    """
    Base exception for API request errors, with optional diagnostic data.
    Includes the raw response object and parsed response JSON for debugging.
    """

    def __init__(self, message, response=None, response_json=None):
        super().__init__(message)
        self.response = response
        self.response_json = response_json

    def __str__(self):
        # Start with the original message (guard for missing args)
        details = self.args[0] if self.args else ""

        # Safely add status code if present; no try/except needed because getattr is safe
        status = getattr(self.response, "status_code", None)
        if status is not None:
            details += f" | Status Code: {status}"

        # Convert response_json to a string with narrow exception handling and a safe fallback
        if self.response_json is not None:
            try:
                body_str = str(self.response_json)
            except (TypeError, ValueError, AttributeError):
                # If __str__ fails, try repr; if that fails too, fall back to a placeholder
                try:
                    body_str = repr(self.response_json)
                except (TypeError, ValueError, AttributeError):
                    body_str = "<unserializable response_json>"
            details += f" | Response Body: {body_str[:200]}..."
        return details


class SchemaValidationError(APIRequestException):
    """Raised when response fails JSON schema validation."""

    pass


class UnexpectedStatusCodeError(APIRequestException):
    """Raised when HTTP status doesn't match expectations."""

    pass


# class CustomerValidationError(APIRequestException):
#     """Raised when customers data mismatches between API and DB."""
#     pass


class PayloadLoggingError(Exception):
    """Raised when payload or params cannot be serialized for logging."""

    pass
