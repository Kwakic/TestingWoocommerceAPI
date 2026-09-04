"""
Configuration for the WooCommerce storefront UI tests.

This module contains static UI environment configuration only.

Design principles:
    - No credentials or secrets.
    - No test logic.
    - No Playwright lifecycle management.
    - One storefront URL is defined per execution environment.
    - Environment naming follows the same convention as the API framework.
"""

UI_HOSTS = {
    # ------------------------------------------------------------------
    # Local Docker development
    #
    # pytest:
    #     Runs directly on the host machine.
    #
    # WordPress:
    #     Runs inside Docker and exposes port 8080 to the host.
    #
    # Communication therefore happens through localhost.
    # ------------------------------------------------------------------
    "test": "http://localhost:8080/",
    # ------------------------------------------------------------------
    # Docker-to-Docker communication
    #
    # Both pytest and WordPress run inside the same Docker network.
    # ------------------------------------------------------------------
    "docker": "http://wordpress/",
    # ------------------------------------------------------------------
    # Legacy local development
    #
    # Used when running against an existing WordPress installation
    # outside Docker (for example XAMPP or WAMP).
    # ------------------------------------------------------------------
    "local": "http://localhost:8888/kwakiweb/",
    # ------------------------------------------------------------------
    # Shared development environment
    # ------------------------------------------------------------------
    "dev": "http://host.docker.internal:8888/kwakiweb/",
    # ------------------------------------------------------------------
    # Shared staging environment
    #
    # TODO: Replace with the real storefront URL when staging is available.
    # ------------------------------------------------------------------
    "staging": "https://staging.example.com/",
    # ------------------------------------------------------------------
    # Production
    #
    # TODO: Replace with the real storefront URL when production testing
    # is introduced.
    # ------------------------------------------------------------------
    "prod": "https://www.example.com/",
    # ------------------------------------------------------------------
    # GitHub Actions
    #
    # This intentionally remains separate from "test" even though both
    # currently resolve to localhost:8080.
    #
    # test -> developer workstation
    # ci   -> GitHub Actions runner
    #
    # Keeping them separate allows CI infrastructure to evolve
    # independently from local development.
    # ------------------------------------------------------------------
    "ci": "http://localhost:8080/",
}
