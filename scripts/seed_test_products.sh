#!/bin/bash

# Seed deterministic baseline WooCommerce products.
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
# seed_test_products.sh
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
# Local UI fixture images
#
# Images are stored in the repository so a clean local
# environment and CI do not depend on an external host.
# --------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_DIR="$SCRIPT_DIR/../tests/ui/data/images"

ALBUM_IMAGE="ui-seed-album.jpg"
BEANIE_IMAGE="ui-seed-beanie.jpg"
HOODIE_IMAGE="ui-seed-hoodie.jpg"

# Docker needs to read the repository fixtures from the host.
# Git Bash on Windows requires a Windows-style host path.
if [[ "${OSTYPE:-}" == msys* || "${OSTYPE:-}" == cygwin* || "${OSTYPE:-}" == win32* ]]; then
    DOCKER_IMAGE_DIR="$(cygpath -w "$IMAGE_DIR")"
else
    DOCKER_IMAGE_DIR="$(cd "$IMAGE_DIR" && pwd)"
fi

# Fail early with a useful message if a fixture is missing.
for image in "$ALBUM_IMAGE" "$BEANIE_IMAGE" "$HOODIE_IMAGE"; do
    if [ ! -f "$IMAGE_DIR/$image" ]; then
        echo "❌ Missing UI image fixture: $IMAGE_DIR/$image" >&2
        exit 1
    fi
done

# --------------------------------------------------
# Ensure a product has a featured image
# --------------------------------------------------

ensure_product_image() {
    local product_id="$1"
    local product_name="$2"
    local image_file="$3"

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
        -v "$DOCKER_IMAGE_DIR:/seed-images:ro" \
        wpcli wp media import \
        "/seed-images/$image_file" \
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
    local image_file="$4"

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
            "$image_file"

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
        "$image_file"
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
