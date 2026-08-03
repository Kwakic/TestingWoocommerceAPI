#!/bin/bash

set -e

# ------------------------------------------------------------------
# Local development configuration.
#
# Centralising these values avoids repeating literals throughout the
# setup script and makes future configuration changes trivial.
# ------------------------------------------------------------------

WP_URL="http://localhost:8080"
WP_TITLE="Test Shop"
WP_ADMIN_USER="admin"
WP_ADMIN_PASSWORD="admin"
WP_ADMIN_EMAIL="test@test.com"

echo "⏳ Waiting for WordPress container..."
until curl -s http://localhost:8080/wp-json > /dev/null; do
  sleep 5
done

# ------------------------------------------------------------------
# FIX — Permissions (light, no ownership fight)
# ------------------------------------------------------------------
echo "🔧 Ensuring WordPress writable folders..."

docker exec wc-wp bash -c "
mkdir -p /var/www/html/wp-content/uploads &&
chmod -R 777 /var/www/html/wp-content
"

# ------------------------------------------------------------------
# STEP 1 — Install WordPress
# ------------------------------------------------------------------
echo "🔧 Checking if WordPress is installed..."

if docker compose -f docker-compose.wp.yml run --rm wpcli wp core is-installed --allow-root; then
  echo "✅ WordPress already installed — skipping"
else
  echo "🚀 Installing WordPress..."
  docker compose -f docker-compose.wp.yml run --rm wpcli \
wp core install \
    --url="$WP_URL" \
    --title="$WP_TITLE" \
    --admin_user="$WP_ADMIN_USER" \
    --admin_password="$WP_ADMIN_PASSWORD" \
    --admin_email="$WP_ADMIN_EMAIL" \
    --allow-root
fi

# ------------------------------------------------------------------
# STEP 2 — Install WooCommerce (FINAL FIX)
# ------------------------------------------------------------------
echo "📦 Checking WooCommerce plugin..."

if docker compose -f docker-compose.wp.yml run --rm wpcli wp plugin is-installed woocommerce --allow-root; then
  echo "✅ WooCommerce already installed — skipping"
else
  echo "🚀 Installing WooCommerce (manual workaround)..."

  docker exec wc-wp bash -c "
  apt update &&
  apt install -y unzip curl &&
  cd /var/www/html/wp-content/plugins &&
  rm -rf woocommerce woocommerce.zip &&
  curl -L -o woocommerce.zip https://downloads.wordpress.org/plugin/woocommerce.9.1.4.zip &&
  unzip -o woocommerce.zip &&
  rm -f woocommerce.zip &&
  chown -R www-data:www-data woocommerce
  "

  echo "🔌 Activating WooCommerce..."

  docker compose -f docker-compose.wp.yml run --rm wpcli \
    wp plugin activate woocommerce --allow-root
fi

# ------------------------------------------------------------------
# STEP 2.5 — 🔥 CRITICAL FIX: Permalinks (REST API routing)
# ------------------------------------------------------------------
echo "🔧 Configuring permalinks..."

docker compose -f docker-compose.wp.yml run --rm wpcli \
  wp rewrite structure '/%postname%/' --allow-root

docker compose -f docker-compose.wp.yml run --rm wpcli \
  wp rewrite flush --allow-root

# ------------------------------------------------------------------
# STEP 2.6 — 🔥 Wait for WooCommerce REST API
# ------------------------------------------------------------------
echo "⏳ Waiting for WooCommerce REST API..."

until curl -s http://localhost:8080/wp-json/wc/v3 > /dev/null; do
  echo "Waiting for WooCommerce API..."
  sleep 3
done

echo "✅ WooCommerce REST API is ready"

# ------------------------------------------------------------------
# STEP 3 — Provision WooCommerce API Credentials
#
# This step reconciles the local development environment into a
# known-good authentication state.
#
# Design principles:
#
# • The repository .env file is the source of truth consumed by
#   the Python test framework.
#
# • WooCommerce stores the consumer key as a one-way hash, making
#   existing credentials impossible to recover.
#
# • Rather than attempting recovery, the setup provisions a fresh
#   credential pair on every execution.
#
# • The repository .env is generated on the host machine rather
#   than inside the temporary wpcli container.
#
# This guarantees that every successful execution of `make run`
# leaves the project in a fully usable state.
# ------------------------------------------------------------------

echo "🔑 Provisioning WooCommerce API credentials..."

CREDENTIALS=$(
docker compose -f docker-compose.wp.yml run --rm wpcli \
wp eval '
global $wpdb;

// ---------------------------------------------------------------
// Resolve the administrator account.
//
// Avoid assuming the administrator always has user ID 1.
// Instead, locate the administrator configured by the setup
// script so the implementation remains resilient to future
// configuration changes.
// ---------------------------------------------------------------

$admin = get_user_by("login", "admin");

if (!$admin) {
    fwrite(STDERR, "Administrator account not found.\n");
    exit(1);
}

$user_id = $admin->ID;

// ---------------------------------------------------------------
// Remove previously generated API credentials.
//
// The consumer key cannot be reconstructed because WooCommerce
// stores only its hash. Regenerating credentials is therefore
// deterministic, inexpensive and keeps the local environment
// consistent.
// ---------------------------------------------------------------

$wpdb->query(
    "DELETE FROM {$wpdb->prefix}woocommerce_api_keys"
);

// ---------------------------------------------------------------
// Generate a fresh credential pair.
// ---------------------------------------------------------------

$key = wc_rand_hash();
$secret = wc_rand_hash();

$wpdb->insert(
    "{$wpdb->prefix}woocommerce_api_keys",
    [
        "user_id"         => $user_id,
        "description"     => "Local Development",
        "permissions"     => "read_write",
        "consumer_key"    => wc_api_hash($key),
        "consumer_secret" => $secret,
        "truncated_key"   => substr($key, -7),
    ]
);

// ---------------------------------------------------------------
// Emit credentials for the host setup script.
//
// The surrounding Bash script captures this output and creates
// the repository .env file.
// ---------------------------------------------------------------

printf(
    "WC_API_URL=http://localhost:8080/wp-json/wc/v3/\nWC_KEY=%s\nWC_SECRET=%s\n",
    $key,
    $secret
);
' --allow-root
)

# ------------------------------------------------------------------
# STEP 3.1 — Prepare Repository Environment
#
# On the first execution, bootstrap the repository .env from
# .env.example.
#
# On subsequent executions, preserve the existing .env and update
# only the generated WooCommerce API credentials.
# ------------------------------------------------------------------

if [[ ! -f .env ]]; then
    echo "📄 Creating repository .env from template..."
    cp .env.example .env
fi

# ------------------------------------------------------------------
# Update only the generated WooCommerce credentials.
#
# All remaining framework configuration (database, logging,
# environment, etc.) is preserved from the template.
# ------------------------------------------------------------------

while IFS='=' read -r key value; do
    case "$key" in
        WC_API_URL|WC_KEY|WC_SECRET)
            if grep -q "^${key}=" .env; then
                sed -i "s|^${key}=.*|${key}=${value}|" .env
            else
                echo "${key}=${value}" >> .env
            fi
            ;;
    esac
done <<< "$CREDENTIALS"

# ------------------------------------------------------------------
# STEP 3.2 — Validate Environment
#
# Fail fast if credential provisioning did not complete
# successfully. This avoids obscure pytest failures later in
# the workflow.
# ------------------------------------------------------------------

if [[ ! -f .env ]]; then
    echo "❌ Failed to generate repository .env"
    exit 1
fi

source .env

if [[ \
    -z "$WC_API_URL" || \
    -z "$WC_KEY" || \
    -z "$WC_SECRET" \
]]
then
    echo "❌ Generated .env is incomplete"
    exit 1
fi

echo "✅ Repository .env generated successfully"
echo "🔐 WooCommerce API credentials provisioned"
echo "🎉 Setup complete!"
