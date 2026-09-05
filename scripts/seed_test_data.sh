#!/bin/bash

# Seed deterministic baseline WooCommerce data.
#
# Responsibilities
# ----------------
# • Create products required by UI/E2E tests
# • Keep seed data stable across test runs
# • Avoid creating duplicates
# • Ensure baseline products have featured images
#
# This script intentionally does NOT:
# • create or modify .env
# • generate API credentials
# • delete test-created data
#
# Test-created data remains owned by the individual
# tests and their fixtures.

# --------------------------------------------------
# Idempotent baseline seeding
#
# setup.sh
#     ↓
# WordPress + WooCommerce ready
#     ↓
# seed_test_data.sh
#     ↓
# Product exists?
#     ├── YES
#     │    ↓
#     │  Featured image exists?
#     │    ├── YES → SKIP
#     │    └── NO  → Import and assign image
#     │
#     └── NO
#          ↓
#        Create product
#          ↓
#        Import and assign image
#
# Running the seed repeatedly is safe:
# • Existing products are not duplicated
# • Existing product images are not re-imported
# • Missing images are added automatically
# --------------------------------------------------

set -e

export MSYS_NO_PATHCONV=1

WP_HTTP_HOST="localhost:8080"

# --------------------------------------------------
# WooCommerce sample images
#
# These are fixed URLs from WooCommerce's sample data.
# They are used only as visual fixtures for the UI/E2E
# baseline products.
# --------------------------------------------------

ALBUM_IMAGE="https://woocommercecore.mystagingwebsite.com/wp-content/uploads/2017/12/album-1.jpg"
BEANIE_IMAGE="https://woocommercecore.mystagingwebsite.com/wp-content/uploads/2017/12/beanie-2.jpg"
HOODIE_IMAGE="https://woocommercecore.mystagingwebsite.com/wp-content/uploads/2017/12/hoodie-2.jpg"

# --------------------------------------------------
# Ensure a product has a featured image
# --------------------------------------------------

ensure_product_image() {
    local product_id="$1"
    local product_name="$2"
    local image_url="$3"

    echo "🖼️ Checking featured image: $product_name"

    local thumbnail_id

    thumbnail_id=$(
        docker compose -f docker-compose.wp.yml run --rm \
            -e HTTP_HOST="$WP_HTTP_HOST" \
            wpcli wp post meta get \
            "$product_id" \
            _thumbnail_id \
            --allow-root 2>/dev/null || true
    )

    if [ -n "$thumbnail_id" ]; then
        echo "✅ Featured image already exists: $product_name"
        return
    fi

    echo "📷 Importing featured image: $product_name"

    docker compose -f docker-compose.wp.yml run --rm \
        -e HTTP_HOST="$WP_HTTP_HOST" \
        wpcli wp media import \
        "$image_url" \
        --post_id="$product_id" \
        --title="$product_name" \
        --alt="$product_name" \
        --featured_image \
        --allow-root

    echo "✅ Featured image assigned: $product_name"
}

# --------------------------------------------------
# Baseline product
# --------------------------------------------------

seed_product() {
    local name="$1"
    local sku="$2"
    local price="$3"
    local image_url="$4"

    echo "🔎 Checking seed product: $name"

    local existing_id

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

        # Important:
        # Existing products must also receive the image if the
        # image fixture was added after the product was created.
        ensure_product_image \
            "$existing_id" \
            "$name" \
            "$image_url"

        return
    fi

    echo "🌱 Creating seed product: $name"

    local product_id

    product_id=$(
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
            --porcelain \
            --allow-root
    )

    echo "✅ Created seed product: $name (ID: $product_id)"

    ensure_product_image \
        "$product_id" \
        "$name" \
        "$image_url"
}

echo
echo "═══════════════════════════════════════════════════════════════"
echo "🌱 Seeding WooCommerce test data"
echo "═══════════════════════════════════════════════════════════════"
echo

seed_product \
    "UI Seed - Album" \
    "ui-seed-album" \
    "15.00" \
    "$ALBUM_IMAGE"

seed_product \
    "UI Seed - Beanie" \
    "ui-seed-beanie" \
    "18.00" \
    "$BEANIE_IMAGE"

seed_product \
    "UI Seed - Hoodie" \
    "ui-seed-hoodie" \
    "45.00" \
    "$HOODIE_IMAGE"

echo
echo "✅ WooCommerce baseline test data is ready."
echo
