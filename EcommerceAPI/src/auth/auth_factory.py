"""
Authentication factory.

Responsible for selecting the correct authentication
strategy based on framework configuration.

Auth strategies manage their own credential loading.
"""

from .oauth1_auth import OAuth1Auth
# from .oauth2_auth import OAuth2Auth
# from .jwt_auth import JWTAuth
# from .basic_auth import BasicAuth


def build_auth(auth_type: str):
    """
    Build authentication strategy.

    Args:
        auth_type: authentication method defined in framework config

    Returns:
        AuthStrategy instance

    You can add following authentication methods if needed:

    if auth_type == "oauth1":
        return OAuth1Auth()

    if auth_type == "oauth2":
        return OAuth2Auth()

    if auth_type == "jwt":
        return JWTAuth()

    if auth_type == "basic":
        return BasicAuth()

    """

    auth_type = auth_type.lower()

    if auth_type == "oauth1":
        return OAuth1Auth()

    raise ValueError(
        f"Unsupported authentication type: {auth_type}. "
        f"This framework currently supports only OAuth1."
    )


# pytest
#   ↓
# config_pytest plugin
#   ↓
# runtime_config.get_config()
#   ↓
# FrameworkConfig.AUTH_TYPE
#   ↓
# auth_resolver.resolve_auth()
#   ↓
# auth_factory.build_auth()
#   ↓
# AuthStrategy
#   ↓
# APIClient
#   ↓
# HttpClient
#   ↓
# requests