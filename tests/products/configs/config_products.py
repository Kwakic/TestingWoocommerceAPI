"""
Environment-specific API endpoints for the Products service.

This module contains the public API base URLs used to communicate with
the Products service in different execution environments.

The shared configuration loader imports this module automatically after
detecting the active service.

Only public endpoint URLs belong here.

Do NOT store:
- usernames
- passwords
- API keys
- database credentials

Those values are loaded separately from environment variables.

Environment selection is controlled by API_ENV.


Typical execution environments:

API_ENV=local
    Tests run locally against a locally hosted application.

API_ENV=test
    Tests run on the host while the application runs in Docker.

API_ENV=docker
    Tests execute inside Docker and communicate over the Docker network.

API_ENV=ci
    GitHub Actions runner communicates with Docker services exposed on localhost.
"""

API_HOSTS = {
    # Local README_development (tests run on host, WordPress in Docker)
    "test": "http://localhost:8888/kwakiweb/wp-json/wc/v3/",
    # Docker environment (tests run IN Docker, same network as WordPress)
    # ⚠️ CRITICAL: Use service name "wordpress", NOT "localhost".
    # Containers communicate through the Docker network,so the Docker service name is used instead of localhost.
    "docker": "http://wordpress/wp-json/wc/v3/",  # ✅ For GitLab CI (uses docker-compose)
    # Local without Docker
    "local": "http://localhost:8888/kwakiweb/wp-json/wc/v3/",  # ✅ For local dev (no Docker)
    # Development server
    "dev": "http://host.docker.internal:8888/kwakiweb/wp-json/wc/v3/",  # ✅ For local Docker → local WordPress
    # Staging environment (real server)
    "staging": "https://staging.example.com/wp-json/wc/v3/",
    # Production (real server)
    "prod": "https://api.example.com/wp-json/wc/v3/",
    # CI-You run pytest on host.
    # GitHub Actions runner communicates with the Docker services exposed on localhost:8080.
    "ci": "http://localhost:8080/wp-json/wc/v3/",
}
