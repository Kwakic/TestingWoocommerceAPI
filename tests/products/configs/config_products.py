"""
Environment-specific API endpoints for the Products service.

This module defines the base URL used by the Products API client for each
supported execution environment.

---------------------------------------------------------------------------
Architecture
---------------------------------------------------------------------------

The framework separates configuration into two categories:

1. Static configuration (this file)
   - API endpoint URLs
   - One URL per execution environment
   - Version-controlled with the repository

2. Dynamic configuration (.env)
   - WooCommerce API credentials (WC_KEY / WC_SECRET)
   - Database credentials
   - Logging configuration
   - Environment selection (API_ENV)

Only PUBLIC endpoint URLs belong in this file.

Never store:
    - usernames
    - passwords
    - API keys
    - database credentials
    - secrets of any kind

Those values belong in .env and are loaded separately.

---------------------------------------------------------------------------
How endpoint resolution works
---------------------------------------------------------------------------

The framework does NOT read WC_API_URL from .env.

Instead, the active endpoint is determined exclusively by API_ENV:

    API_ENV
        ↓
    API_HOSTS
        ↓
    Selected base URL
        ↓
    APIClient

This guarantees that every developer, Docker container and CI runner
uses a predictable endpoint without hidden overrides.

---------------------------------------------------------------------------
Typical execution environments
---------------------------------------------------------------------------

API_ENV=local
    Tests run on the developer machine against a legacy local
    WordPress installation (for example XAMPP or WAMP).

API_ENV=test
    Tests run on the developer machine while WordPress and
    WooCommerce run inside the local Docker environment.

API_ENV=docker
    Tests themselves run inside Docker containers.
    Communication happens over the Docker network using service names
    instead of localhost.

API_ENV=ci
    Tests run on a GitHub Actions runner.
    WordPress runs inside Docker services started by the workflow and
    is exposed on localhost.

This separation allows each execution environment to evolve
independently, even if two environments currently happen to use
the same endpoint.
"""

API_HOSTS = {
    # ------------------------------------------------------------------
    # Local Docker development
    #
    # This is the environment most contributors will use.
    #
    # pytest:
    #     Runs directly on the host machine.
    #
    # WordPress:
    #     Runs inside Docker and exposes port 8080 to the host.
    #
    # Communication therefore happens through localhost.
    # ------------------------------------------------------------------
    "test": "http://localhost:8080/wp-json/wc/v3/",
    # ------------------------------------------------------------------
    # Docker-to-Docker communication
    #
    # Both pytest and WordPress run inside the same Docker network.
    #
    # Containers never use localhost to communicate with each other.
    # Instead they communicate using Docker service names.
    # ------------------------------------------------------------------
    "docker": "http://wordpress/wp-json/wc/v3/",
    # ------------------------------------------------------------------
    # Legacy local development
    #
    # Used when running against an existing WordPress installation
    # outside Docker (for example XAMPP or WAMP).
    # ------------------------------------------------------------------
    "local": "http://localhost:8888/kwakiweb/wp-json/wc/v3/",
    # ------------------------------------------------------------------
    # Shared development environment
    #
    # Useful when developers need to connect from Docker to a
    # WordPress instance running on the host machine.
    # ------------------------------------------------------------------
    "dev": "http://host.docker.internal:8888/kwakiweb/wp-json/wc/v3/",
    # ------------------------------------------------------------------
    # Shared staging server
    # ------------------------------------------------------------------
    "staging": "https://staging.example.com/wp-json/wc/v3/",
    # ------------------------------------------------------------------
    # Production
    # ------------------------------------------------------------------
    "prod": "https://api.example.com/wp-json/wc/v3/",
    # ------------------------------------------------------------------
    # GitHub Actions
    #
    # Although this currently resolves to the same endpoint as "test",
    # it intentionally remains a separate environment.
    #
    # Why?
    #
    # They represent different execution contexts:
    #
    #   test -> developer workstation
    #   ci   -> GitHub Actions runner
    #
    # Keeping them separate allows CI infrastructure to change in the
    # future without affecting local development.
    # ------------------------------------------------------------------
    "ci": "http://localhost:8080/wp-json/wc/v3/",
}

################
