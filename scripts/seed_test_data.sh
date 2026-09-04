#!/bin/bash

# --------------------------------------------------
# Seed deterministic baseline WooCommerce data.
#
# Responsibilities
# ----------------
# • Create products required by UI/E2E tests
# • Keep seed data stable across test runs
# • Avoid creating duplicates
#
# This script intentionally does NOT:
# • create or modify .env
# • generate API credentials
# • delete test-created data
#
# Test-created data remains owned by the individual
# tests and their fixtures.
# --------------------------------------------------
# The bootstrap is idempotent, existing infrastructure is reused
# setup.sh
#     ↓
#WooCommerce already exists
#     ↓
#seed_test_data.sh
#     ↓
#SKU ui-seed-album exists
#     ↓
#SKIP
#
#SKU ui-seed-beanie exists
#     ↓
#SKIP
#
#SKU ui-seed-hoodie exists
#     ↓
#SKIP
# --------------------------------------------------

set -e

export MSYS_NO_PATHCONV=1

WP_HTTP_HOST="localhost:8080"

# --------------------------------------------------
# Baseline products
#
# These products are environment fixtures, not
# test-owned data. Tests may safely rely on them
# existing after the environment bootstrap.
# --------------------------------------------------

seed_product() {
    local name="$1"
    local sku="$2"
    local price="$3"

    echo "🔎 Checking seed product: $name"

    existing_id=$(
        docker compose -f docker-compose.wp.yml run --rm \
            -e HTTP_HOST="$WP_HTTP_HOST" \
            wpcli wp wc product list \
            --sku="$sku" \
            --field=id \
            --user=admin \
            --allow-root
    )

    if [ -n "$existing_id" ]; then
        echo "✅ Seed product already exists: $name (ID: $existing_id)"
        return
    fi

    echo "🌱 Creating seed product: $name"

    docker compose -f docker-compose.wp.yml run --rm \
        -e HTTP_HOST="$WP_HTTP_HOST" \
        wpcli wp wc product create \
        --name="$name" \
        --type=simple \
        --status=publish \
        --sku="$sku" \
        --regular_price="$price" \
        --in_stock=true \
        --catalog_visibility=visible \
        --user=admin \
        --allow-root

    echo "✅ Created seed product: $name"
}

echo
echo "═══════════════════════════════════════════════════════════════"
echo "🌱 Seeding WooCommerce test data"
echo "═══════════════════════════════════════════════════════════════"
echo

seed_product "UI Seed - Album" "ui-seed-album" "15.00"
seed_product "UI Seed - Beanie" "ui-seed-beanie" "18.00"
seed_product "UI Seed - Hoodie" "ui-seed-hoodie" "45.00"

echo
echo "✅ WooCommerce baseline test data is ready."
echo
