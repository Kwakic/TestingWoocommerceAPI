"""
config_customers.py

Environment-specific host mappings for the CUSTOMERS microservice.

Only non-sensitive public endpoint roots should be kept here.
The shared config loader dynamically imports this module based on SERVICE=customers.

Why this file?
- Different environments have different URLs
- API_ENV environment variable selects which URL to use
- Keeps secrets out of code (credentials loaded separately)

Rule of thumb:
  - ENV=docker → wordpress hostname
  - ENV=local → localhost
  - CI must always use ENV=docker
"""

API_HOSTS = {
    # Local development (tests run on host, WordPress in Docker)
    "test": "http://localhost:8888/kwakiweb/wp-json/wc/v3/",
    # Docker environment (tests run IN Docker, same network as WordPress)
    # ⚠️ CRITICAL: Use service name "wordpress", NOT "localhost"
    "docker": "http://wordpress/wp-json/wc/v3/",  # ✅ For GitLab CI (uses docker-compose)
    # Local without Docker
    "local": "http://localhost:8888/kwakiweb/wp-json/wc/v3/",  # ✅ For local dev (no Docker)
    # Development server
    "dev": "http://host.docker.internal:8888/kwakiweb/wp-json/wc/v3/",  # ✅ For local Docker → local WordPress
    # Staging environment (real server)
    "staging": "https://staging.example.com/wp-json/wc/v3/",
    # Production (real server)
    "prod": "https://api.example.com/wp-json/wc/v3/",
    # CI-You run pytest on host:
    "ci": "http://localhost:8080/wp-json/wc/v3/",
}
