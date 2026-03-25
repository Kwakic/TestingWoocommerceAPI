"""
config_orders.py

Environment-specific host mappings for the CUSTOMERS microservice.

Only non-sensitive public endpoint roots should be kept here.
The shared config loader dynamically imports this module based on SERVICE=customers.
"""

API_HOSTS = {
    "test": "http://localhost:8888/kwakiweb/wp-json/wc/v3/",
    "staging": "",
    "dev": "",
    "prod": "",
}
