"""
OAuth1 authentication strategy for WooCommerce APIs.

This strategy loads WooCommerce API credentials using the
existing credentials utility and applies OAuth1 authentication
to outgoing HTTP requests.

This preserves backward compatibility with the previous
framework behavior where APIClient directly handled OAuth1.
"""

from typing import Dict, Any
from requests_oauthlib import OAuth1

from EcommerceAPI.src.utils.credentials_utility import get_wc_api_keys
from EcommerceAPI.src.auth.base_auth import AuthStrategy


class OAuth1Auth(AuthStrategy):
    """
    OAuth1 authentication strategy.
    """

    def __init__(self) -> None:
        """
        Load WooCommerce API credentials and initialize OAuth1 auth object.
        """

        wc_creds = get_wc_api_keys()

        self.oauth = OAuth1(wc_creds["wc_key"], wc_creds["wc_secret"])

    def apply(self, request_kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inject OAuth1 authentication into request kwargs.
        """

        request_kwargs["auth"] = self.oauth
        return request_kwargs
