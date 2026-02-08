"""
config_customers.py

Environment-specific host mappings for the CUSTOMERS microservice.

Only non-sensitive public endpoint roots should be kept here.
The shared config loader dynamically imports this module based on SERVICE=customers.
"""

API_HOSTS = {
    "test":    "http://localhost:8888/kwakiweb/wp-json/wc/v3/",
    # ✅ CRITICAL: Use service name 'wordpress' as hostname
    # No port needed (internal Docker DNS)
    # wordpress = the service name from docker-compose.wp.yml
    "docker":  "http://wordpress/wp-json/wc/v3/",
    "local":   "http://localhost:8888/wp-json/wc/v3/",
    "dev":     "http://localhost:8888/kwakiweb/wp-json/wc/v3/",
    "staging": "",
    "prod":    "",
}

# """
# config_customers.py
#
# Environment-specific host mappings for the CUSTOMERS microservice.
#
# Why this file?
# - Different environments have different URLs
# - API_ENV environment variable selects which URL to use
# - Keeps secrets out of code (credentials loaded separately)
# """
#
# API_HOSTS = {
#     # Local development (tests run on host, WordPress in Docker)
#     "test": "http://localhost:8888/kwakiweb/wp-json/wc/v3/",
#
#     # Docker environment (tests run IN Docker, same network as WordPress)
#     # ⚠️ CRITICAL: Use service name "wordpress", NOT "localhost"
#     "docker": "http://wordpress/wp-json/wc/v3/",
#
#     # Local without Docker
#     "local": "http://localhost:8888/wp-json/wc/v3/",
#
#     # Development server
#     "dev": "http://localhost:8888/kwakiweb/wp-json/wc/v3/",
#
#     # Staging environment (real server)
#     "staging": "https://staging.example.com/wp-json/wc/v3/",
#
#     # Production (real server)
#     "prod": "https://api.example.com/wp-json/wc/v3/",
# }