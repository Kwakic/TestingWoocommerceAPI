#!/bin/bash
#
# --------------------------------------------------
# Merge generated WooCommerce credentials into .env
#
# INPUT
# -----
# Reads KEY=VALUE pairs from stdin.
#
# OUTPUT
# ------
# Updates only the dynamic WooCommerce entries:
#
#   WC_API_URL
#   WC_KEY
#   WC_SECRET
#
# Static configuration (database, logging, API_ENV,
# etc.) remains owned by .env.example.
#
# This separation keeps setup.sh focused solely on
# provisioning WordPress/WooCommerce while this script
# owns repository configuration updates.
# --------------------------------------------------


# write_env_credentials.sh
#
# Single responsibility: read WC_API_URL / WC_KEY / WC_SECRET lines
# from stdin and merge them into the local .env file — updating
# existing keys in place, appending any that are missing, and
# leaving every other line in .env completely untouched.
# In other words --> merge generated WooCommerce credentials into the
# repository .env file while preserving every other configuration entry.

#
# This is the ONLY place in the whole project that writes WooCommerce
# credentials into .env. scripts/setup.sh never touches .env directly
# (see the stdout/stderr split note near the top of that file).
#
# Usage:
#   bash scripts/setup.sh | bash scripts/write_env_credentials.sh

set -e

if [[ ! -f .env ]]; then
    echo "❌ .env not found. Run 'make ensure-env' first." >&2
    exit 1
fi

UPDATED=0

while IFS='=' read -r key value; do
    [[ -z "$key" ]] && continue

    case "$key" in
        WC_API_URL|WC_KEY|WC_SECRET)
            if grep -q "^${key}=" .env; then
                sed -i "s|^${key}=.*|${key}=${value}|" .env
            else
                echo "${key}=${value}" >> .env
            fi
            UPDATED=$((UPDATED + 1))
            ;;
    esac
done

if [[ "$UPDATED" -eq 0 ]]; then
    echo "❌ No WC_API_URL / WC_KEY / WC_SECRET lines received on stdin — nothing to write" >&2
    exit 1
fi

echo "✅ .env updated with WooCommerce credentials ($UPDATED value(s))" >&2
