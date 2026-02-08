#!/bin/bash
set -e

echo "🚀 Starting WordPress stack..."
docker compose -f docker-compose.wp.yml up -d

echo "⏳ Waiting for services to be ready..."
sleep 30

echo "📦 Installing WordPress..."
docker exec wc-wp wp core install \
  --url="http://localhost:8888" \
  --title="Local Test" \
  --admin_user="admin" \
  --admin_password="admin" \
  --admin_email="admin@test.com" \
  --skip-email \
  --allow-root

echo "🛒 Installing WooCommerce..."
docker exec wc-wp wp plugin install woocommerce --activate --allow-root

echo "✅ WordPress setup complete!"
echo ""
echo "🧪 Running tests..."

# Run tests with specified profile (default: customers)
PROFILE=${1:-customers}
docker compose -f docker-compose.matrix.yml \
  --profile "$PROFILE" \
  up --abort-on-container-exit

# Capture exit code
EXIT_CODE=$?

echo ""
echo "🧹 Cleaning up..."
docker compose -f docker-compose.wp.yml down -v
docker compose -f docker-compose.matrix.yml down -v

exit $EXIT_CODE