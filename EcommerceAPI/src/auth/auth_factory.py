"""
Authentication factory.

Builds authentication strategy based on framework configuration.
"""

from .oauth1_auth import OAuth1Auth
from .jwt_auth import JWTAuth
from .basic_auth import BasicAuth


def build_auth(settings, credentials):
    """
    Build authentication strategy based on configuration.

    Args:
        settings: framework configuration
        credentials: loaded credentials

    Returns:
        AuthStrategy instance
    """

    auth_type = settings.AUTH_TYPE.lower()

    if auth_type == "oauth1":
        return OAuth1Auth()

    # # Load WooCommerce OAuth credentials
    # wc_creds = get_wc_api_keys()
    # self.auth = OAuth1(wc_creds['wc_key'], wc_creds['wc_secret'])

    if auth_type == "jwt":
        return JWTAuth(credentials["token"])

    if auth_type == "basic":
        return BasicAuth(
            credentials["username"],
            credentials["password"]
        )

    raise ValueError(f"Unsupported authentication type: {auth_type}")