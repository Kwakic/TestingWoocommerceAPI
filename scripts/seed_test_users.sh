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
# Customer A — stable checkout customer
# UI_CUSTOMER_USERNAME
# UI_CUSTOMER_EMAIL
# UI_CUSTOMER_PASSWORD
#
# Customer B — no saved billing address
# UI_CUSTOMER_NO_ADDRESS_USERNAME
# UI_CUSTOMER_NO_ADDRESS_EMAIL
# UI_CUSTOMER_NO_ADDRESS_PASSWORD
#
# Customer C — mutable profile customer
# UI_CUSTOMER_PROFILE_USERNAME
# UI_CUSTOMER_PROFILE_EMAIL
# UI_CUSTOMER_PROFILE_PASSWORD
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

: "${UI_CUSTOMER_NO_ADDRESS_USERNAME:?UI_CUSTOMER_NO_ADDRESS_USERNAME is required}"
: "${UI_CUSTOMER_NO_ADDRESS_EMAIL:?UI_CUSTOMER_NO_ADDRESS_EMAIL is required}"
: "${UI_CUSTOMER_NO_ADDRESS_PASSWORD:?UI_CUSTOMER_NO_ADDRESS_PASSWORD is required}"

: "${UI_CUSTOMER_PROFILE_USERNAME:?UI_CUSTOMER_PROFILE_USERNAME is required}"
: "${UI_CUSTOMER_PROFILE_EMAIL:?UI_CUSTOMER_PROFILE_EMAIL is required}"
: "${UI_CUSTOMER_PROFILE_PASSWORD:?UI_CUSTOMER_PROFILE_PASSWORD is required}"

# --------------------------------------------------
# Seed customer profiles
#
# The seed is idempotent:
# - Existing users are reused.
# - Missing users are created.
# - Existing passwords/profile data are not modified.
# --------------------------------------------------

seed_customer() {
    local username="$1"
    local email="$2"
    local password="$3"
    local description="$4"

    echo "🔎 Checking $description: $username"

    local existing_user_id
    existing_user_id=$(
        docker compose -f docker-compose.wp.yml run --rm             -e HTTP_HOST="$WP_HTTP_HOST"             wpcli wp user get             "$username"             --field=ID             --allow-root 2>/dev/null || true
    )

    if [ -n "$existing_user_id" ]; then
        echo "✅ $description already exists: $username (ID: $existing_user_id)"
        return
    fi

    echo "🌱 Creating $description: $username"

    docker compose -f docker-compose.wp.yml run --rm         -e HTTP_HOST="$WP_HTTP_HOST"         wpcli wp user create         "$username"         "$email"         --user_pass="$password"         --role=customer         --display_name="$username"         --allow-root

    echo "✅ $description created: $username"
}

seed_customer     "$UI_CUSTOMER_USERNAME"     "$UI_CUSTOMER_EMAIL"     "$UI_CUSTOMER_PASSWORD"     "Customer A (stable checkout customer)"

# --------------------------------------------------
# Customer A — baseline checkout address
# --------------------------------------------------
# Customer A is the stable checkout profile. Its saved billing and shipping
# addresses are environment prerequisites for checkout UI tests.
#
# The address is provisioned here rather than by another UI test so that
# checkout tests do not depend on state created by a previous test run.
# The operation is idempotent: running the seed again simply converges the
# existing Customer A profile to the expected baseline address.
# --------------------------------------------------
echo "🏠 Provisioning Customer A billing and shipping addresses..."

CUSTOMER_A_ID="$(
    docker compose -f docker-compose.wp.yml run --rm -T         -e HTTP_HOST="$WP_HTTP_HOST"         wpcli wp user get         "$UI_CUSTOMER_USERNAME"         --field=ID         --allow-root
)"

docker compose -f docker-compose.wp.yml run --rm -T     -e HTTP_HOST="$WP_HTTP_HOST"     wpcli wp eval '
        $customer = new WC_Customer((int) "'$CUSTOMER_A_ID'");

        // Billing address used by the checkout tests.
        $customer->set_billing_first_name("John");
        $customer->set_billing_last_name("Beck");
        $customer->set_billing_address_1("Pl.del Pueblo,10");
        $customer->set_billing_postcode("28100");
        $customer->set_billing_city("Madrid");
        $customer->set_billing_state("M");
        $customer->set_billing_country("ES");
        $customer->set_billing_phone("753357753");

        // Shipping starts with the same baseline address.
        // The checkout test then changes it to a different address.
        $customer->set_shipping_first_name("John");
        $customer->set_shipping_last_name("Beck");
        $customer->set_shipping_address_1("Pl.del Pueblo,10");
        $customer->set_shipping_postcode("28100");
        $customer->set_shipping_city("Madrid");
        $customer->set_shipping_state("M");
        $customer->set_shipping_country("ES");

        $customer->save();
    '     --allow-root

echo "✅ Customer A billing and shipping addresses configured"

seed_customer     "$UI_CUSTOMER_NO_ADDRESS_USERNAME"     "$UI_CUSTOMER_NO_ADDRESS_EMAIL"     "$UI_CUSTOMER_NO_ADDRESS_PASSWORD"     "Customer B (no-address customer)"

seed_customer     "$UI_CUSTOMER_PROFILE_USERNAME"     "$UI_CUSTOMER_PROFILE_EMAIL"     "$UI_CUSTOMER_PROFILE_PASSWORD"     "Customer C (mutable profile customer)"

echo
echo "═══════════════════════════════════════════════════════════════"
echo "👤 UI customer profiles are ready."
echo "═══════════════════════════════════════════════════════════════"
echo
echo "═══════════════════════════════════════════════════════════════"
echo
