#!/bin/bash

set -e

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
    --url="http://localhost:8080" \
    --title="Test Shop" \
    --admin_user="admin" \
    --admin_password="admin" \
    --admin_email="test@test.com" \
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
  curl -L -o woocommerce.zip https://downloads.wordpress.org/plugin/woocommerce.latest-stable.zip &&
  unzip -o woocommerce.zip &&
  rm -f woocommerce.zip &&
  chown -R www-data:www-data woocommerce
  "

  echo "🔌 Activating WooCommerce..."

  docker compose -f docker-compose.wp.yml run --rm wpcli \
    wp plugin activate woocommerce --allow-root
fi

# ------------------------------------------------------------------
# STEP 3 — Create API keys (idempotent-safe)
# ------------------------------------------------------------------
echo "🔑 Creating API keys..."

docker compose -f docker-compose.wp.yml run --rm wpcli \
  wp eval '
$user_id = 1;
global $wpdb;

// Avoid duplicate keys on rerun
$existing = $wpdb->get_var("SELECT COUNT(*) FROM {$wpdb->prefix}woocommerce_api_keys");
if ($existing > 0) {
    echo "API keys already exist — skipping\n";
    return;
}

$key = wc_rand_hash();
$secret = wc_rand_hash();

$wpdb->insert("{$wpdb->prefix}woocommerce_api_keys", [
  "user_id" => $user_id,
  "description" => "CI Key",
  "permissions" => "read_write",
  "consumer_key" => wc_api_hash($key),
  "consumer_secret" => $secret,
  "truncated_key" => substr($key, -7)
]);

// 👇 WRITE TO .env FILE (AUTO-WIRING)
file_put_contents(".env",
"WC_API_URL=http://localhost:8080/wp-json/wc/v3/\n" .
"WC_CONSUMER_KEY=$key\n" .
"WC_CONSUMER_SECRET=$secret\n"
);

echo "=====================================\n";
echo "CONSUMER KEY: $key\n";
echo "CONSUMER SECRET: $secret\n";
echo "=====================================\n";
echo "✅ .env file generated automatically\n";

' --allow-root

echo "🎉 Setup complete!"
