"""
REST authentication factory only!

Responsible for selecting the authentication strategy used by the
REST API client based on framework configuration.

GraphQL authentication is handled separately by the GraphQL client
and does not use this factory.
"""

from .oauth1_auth import OAuth1Auth

# from .oauth2_auth import OAuth2Auth
# from .jwt_auth import JWTAuth
# from .basic_auth import BasicAuth


def build_auth(auth_type: str):
    """
    Build the REST authentication strategy.

    Args:
        auth_type: REST authentication method defined in framework config

    Returns:
        AuthStrategy instance

    Raises:
        ValueError: If the requested REST authentication method is unsupported.

    Note:
        GraphQL authentication is intentionally handled separately and
        does not use this factory.
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
