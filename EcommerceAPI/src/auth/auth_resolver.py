"""
Authentication resolver.

Connects runtime configuration with authentication factory.
This isolates configuration logic from APIClient.

Purpose:
    config → resolver → factory → strategy
"""

from EcommerceAPI.src.configs.runtime_config import get_config
from EcommerceAPI.src.auth.auth_factory import build_auth


def resolve_auth():
    """
    Resolve authentication strategy from framework configuration.

    Returns:
        AuthStrategy instance
    """

    cfg = get_config()

    return build_auth(cfg.AUTH_TYPE)