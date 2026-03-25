"""
Authentication Strategy Interface - Base Class.

This module defines the contract used by the framework to apply authentication to outgoing HTTP requests.

Enterprise design principle:
----------------------------
Authentication must be PLUGGABLE and NOT embedded inside APIClient
or HttpClient.

Each authentication implementation modifies request arguments
(headers, auth object, certificates, etc.) before the request is sent.

Supported implementations may include:
    - OAuth1
    - OAuth2
    - JWT
    - Basic Auth
    - HMAC
    - mTLS

Example:
       JWT: headers["Authorization"] = f"Bearer {self.token}"
       Basic: request_kwargs["auth"] = (self.username, self.password)
       OAuth1: request_kwargs["auth"] = self.oauth

    The factory simply selects which strategy to use:
       - auth_type = settings.AUTH_TYPE.lower()

    Then returns the proper strategy:
    if auth_type == "oauth1":
        return OAuth1Auth()

Authentication must be controlled by configuration, not by the client.

The flow:

runtime_config
      │
      ▼
auth_resolver
      │
      ▼
auth_factory
      │
      ▼
AuthStrategy
      │
      ▼
APIClient
      │
      ▼
HttpClient
      │
      ▼
requests

"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class AuthStrategy(ABC):
    """
    Base authentication strategy.

    Implementations modify request kwargs
    before they are sent to the HTTP client.
    """

    @abstractmethod
    def apply(self, request_kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply authentication configuration to request arguments.

        Args:
            request_kwargs: dictionary of arguments passed to requests

        Returns:
            Updated request kwargs
        """
        pass
