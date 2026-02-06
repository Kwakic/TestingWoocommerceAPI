# configs/

This folder contains internal configuration implementation details.

⚠️ Do not read environment variables directly from code here.
⚠️ Do not add new configuration flags without updating the framework contract.

Authoritative documentation:
- docs/CONFIG_CONTRACT.md — configuration rules and ownership
- docs/ENVIRONMENT_CONFIG_GUIDE.md — how to use and troubleshoot config

If a value affects framework behavior, it must be defined in:
EcommerceAPI.plugins._config
