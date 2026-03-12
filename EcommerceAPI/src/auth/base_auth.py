"""
Authentication Strategy Base Class.

This module defines the contract used by the framework to apply
authentication to outgoing HTTP requests.

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