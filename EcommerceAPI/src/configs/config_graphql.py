"""
Environment-specific GraphQL endpoint configuration.

This module defines the public GraphQL endpoint for each
supported execution environment.

GraphQL endpoint URLs are static, public configuration.
They are selected using the active API_ENV from runtime_config.py.

This module must not:
- read environment variables directly
- contain secrets
- contain authentication credentials
- contain runtime configuration
- contain pytest logic
"""

from EcommerceAPI.src.configs.runtime_config import get_config


GRAPHQL_HOSTS = {
    # ------------------------------------------------------------------
    # Local Docker development
    #
    # pytest:
    #     Runs directly on the host machine.
    #
    # WordPress:
    #     Runs inside Docker and exposes port 8080 to the host.
    # ------------------------------------------------------------------
    "test": "http://localhost:8080/graphql",
    # ------------------------------------------------------------------
    # Docker-to-Docker communication
    #
    # Both pytest and WordPress run inside the same Docker network.
    # ------------------------------------------------------------------
    "docker": "http://wordpress/graphql",
    # ------------------------------------------------------------------
    # Legacy local development
    #
    # Existing WordPress installation outside Docker.
    # ------------------------------------------------------------------
    "local": "http://localhost:8888/kwakiweb/graphql",
    # ------------------------------------------------------------------
    # Shared development environment
    #
    # Docker connects to WordPress running on the host machine.
    # ------------------------------------------------------------------
    "dev": "http://host.docker.internal:8888/kwakiweb/graphql",
    # ------------------------------------------------------------------
    # Shared staging environment
    # ------------------------------------------------------------------
    "staging": "https://staging.example.com/graphql",
    # ------------------------------------------------------------------
    # Production
    # ------------------------------------------------------------------
    "prod": "https://api.example.com/graphql",
    # ------------------------------------------------------------------
    # GitHub Actions
    #
    # Kept separate from "test" even though the current endpoint
    # is identical, because these represent different execution
    # contexts.
    # ------------------------------------------------------------------
    "ci": "http://localhost:8080/graphql",
}


def get_graphql_host() -> str:
    """
    Return the GraphQL endpoint for the active execution environment.

    The active environment is resolved centrally by runtime_config.py.
    This module does not read API_ENV or ENV directly.
    """

    env = get_config().ENV.lower()

    if env not in GRAPHQL_HOSTS:
        raise RuntimeError(
            f"ENV='{env}' missing from GRAPHQL_HOSTS in config_graphql.py"
        )

    return GRAPHQL_HOSTS[env]
