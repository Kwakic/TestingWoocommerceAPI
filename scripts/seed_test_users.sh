#!/bin/bash

# Seed persistent test users required by UI/E2E tests.
#
# Responsibilities
# ----------------
# • Create the dedicated customer account required by UI tests
# • Keep UI test users stable across test runs
# • Avoid creating duplicate accounts
# • Allow credentials to be supplied by the environment
#
# This script intentionally does NOT:
# • create or modify .env
# • generate WooCommerce API credentials
# • delete test-created users
# • manage pytest fixtures or test lifecycle
#
# UI test users are environment-level prerequisites. They are provisioned
# during environment setup and can be reused by multiple UI tests.
#
# Expected environment variables
# ------------------------------
# UI_CUSTOMER_USERNAME
# UI_CUSTOMER_EMAIL
# UI_CUSTOMER_PASSWORD
#
# The values should be supplied by the caller:
# • local development → .env / Makefile
# • CI → GitHub Actions environment / secrets
#
# Idempotent provisioning
# -----------------------
# setup.sh
#     ↓
# WordPress + WooCommerce ready
#     ↓
# seed_test_products.sh
#     ↓
# Baseline products ready
#     ↓
# seed_test_users.sh
#     ↓
# UI customer exists?
#     ├── YES → SKIP
#     └── NO  → Create customer
#
# Running the seed repeatedly is safe:
# • Existing users are not duplicated
# • Existing credentials are not changed
# • Test-created users remain owned by their individual tests/fixtures
#
# IMPORTANT:
# The username is the primary identity check because WordPress requires
# usernames to be unique. Checking only by email can incorrectly conclude
# that the user does not exist when the username is already registered.
# --------------------------------------------------

set -euo pipefail

export MSYS_NO_PATHCONV=1

WP_HTTP_HOST="localhost:8080"

# --------------------------------------------------
# Validate required configuration
# --------------------------------------------------

: "${UI_CUSTOMER_USERNAME:?UI_CUSTOMER_USERNAME is required}"
: "${UI_CUSTOMER_EMAIL:?UI_CUSTOMER_EMAIL is required}"
: "${UI_CUSTOMER_PASSWORD:?UI_CUSTOMER_PASSWORD is required}"

# --------------------------------------------------
# Seed customer account
# --------------------------------------------------

echo "🔎 Checking UI test customer: $UI_CUSTOMER_USERNAME"

# WordPress usernames are unique, so use the configured username
# as the primary idempotency check.
EXISTING_USER_ID=$(
    docker compose -f docker-compose.wp.yml run --rm \
        -e HTTP_HOST="$WP_HTTP_HOST" \
        wpcli wp user get \
        "$UI_CUSTOMER_USERNAME" \
        --field=ID \
        --by=login \
        --allow-root 2>/dev/null || true
)

if [ -n "$EXISTING_USER_ID" ]; then
    echo "✅ UI test customer already exists: $UI_CUSTOMER_USERNAME (ID: $EXISTING_USER_ID)"
else
    echo "🌱 Creating UI test customer: $UI_CUSTOMER_USERNAME"

    docker compose -f docker-compose.wp.yml run --rm \
        -e HTTP_HOST="$WP_HTTP_HOST" \
        wpcli wp user create \
        "$UI_CUSTOMER_USERNAME" \
        "$UI_CUSTOMER_EMAIL" \
        --user_pass="$UI_CUSTOMER_PASSWORD" \
        --role=customer \
        --display_name="$UI_CUSTOMER_USERNAME" \
        --allow-root

    echo "✅ UI test customer created: $UI_CUSTOMER_USERNAME"
fi

echo
echo "═══════════════════════════════════════════════════════════════"
echo "👤 UI test users are ready."
echo "═══════════════════════════════════════════════════════════════"
echo
