#!/bin/bash

# --------------------------------------------------
# Bootstrap a local WooCommerce development instance.
#
# Responsibilities
# ----------------
# • Install/configure WordPress
# • Install WooCommerce
# • Configure permalinks
# • Generate fresh WooCommerce API credentials


# This script intentionally does NOT:
#
# • create or modify .env
# • export environment variables
# • make CI-specific decisions
#
# Its only responsibility is provisioning WordPress/WooCommerce
# and returning fresh API credentials.
# --------------------------------------------------

set -e


# ------------------------------------------------------------------
# Git Bash on Windows automatically rewrites Unix-style paths (e.g.
# /var/www/html) into Windows paths (e.g.
# C:/Program Files/Git/var/www/html) before invoking Docker.
#
# WP-CLI commands executed inside Docker containers expect Linux
# paths, so disable MSYS path conversion when running under Git Bash.
#
# This has no effect on Linux, macOS or GitHub Actions.
# ------------------------------------------------------------------
export MSYS_NO_PATHCONV=1

# ------------------------------------------------------------------
# Local development configuration.
#
# Centralising these values avoids repeating literals throughout the
# setup script and makes future configuration changes trivial.
# ------------------------------------------------------------------

WP_URL="http://localhost:8080"
WP_HTTP_HOST="localhost:8080"
WP_TITLE="Test Shop"
WP_ADMIN_USER="admin"
WP_ADMIN_PASSWORD="admin"
WP_ADMIN_EMAIL="test@test.com"

# ------------------------------------------------------------------
# Stdout / stderr split - human vs machine output (Machine-readable output contract).
#
# This script has exactly one job: bootstrap WordPress + WooCommerce
# and hand back fresh API credentials. It does NOT know (and should
# not need to know) whether the caller wants those written to a local
# .env file, exported into $GITHUB_ENV, or something else entirely —
# that decision belongs to the caller (Makefile locally, action.yml
# in CI). Making that possible cleanly:
#
#   - fd 3 is saved as a copy of the *real* stdout
#   - fd 1 (stdout) is redirected to stderr for the rest of the
#     script, so every progress message below — including WP-CLI's
#     own output — stays visible on the terminal but is invisible to
#     anything that captures this script's stdout
#   - the final credentials block is written explicitly to fd 3
#
# Result: `bash scripts/setup.sh` still shows full progress as
# before. `OUTPUT=$(bash scripts/setup.sh)` captures ONLY the three
# WC_KEY / WC_SECRET lines — nothing else. No .env
# handling and no log-grepping required by the caller.
# ------------------------------------------------------------------
exec 3>&1
exec 1>&2


# ------------------------------------------------------------------
# Bootstrap starts here
# ------------------------------------------------------------------
echo
echo "═══════════════════════════════════════════════════════════════"
echo "🚀 Bootstrapping local WooCommerce environment"
echo "═══════════════════════════════════════════════════════════════"
echo

echo "⏳ Waiting for WordPress container..."
until curl -s http://localhost:8080/wp-json > /dev/null; do
  sleep 5
done

# ------------------------------------------------------------------
# FIX — Permissions (light, no ownership fight)
# ------------------------------------------------------------------
echo "🔧 Ensuring WordPress writable folders..."

# -T disables TTY allocation — required for this to work non-interactively
# (CI, or anywhere stdout is being captured/piped rather than a live shell).
docker compose -f docker-compose.wp.yml exec -T wordpress bash -c "
mkdir -p /var/www/html/wp-content/uploads &&
chmod -R 777 /var/www/html/wp-content
"

# STEP 1 — Install WordPress
# ------------------------------------------------------------------
echo "🔧 Checking if WordPress is installed..."

if docker compose -f docker-compose.wp.yml run --rm \
    -e HTTP_HOST="$WP_HTTP_HOST" \
    wpcli wp core is-installed --allow-root; then
  echo "✅ WordPress already installed — skipping"
else
  echo "🚀 Installing WordPress..."
  docker compose -f docker-compose.wp.yml run --rm \
    -e HTTP_HOST="$WP_HTTP_HOST" \
    wpcli wp core install \
    --url="$WP_URL" \
    --title="$WP_TITLE" \
    --admin_user="$WP_ADMIN_USER" \
    --admin_password="$WP_ADMIN_PASSWORD" \
    --admin_email="$WP_ADMIN_EMAIL" \
    --allow-root
fi

# ------------------------------------------------------------------
# STEP 2 — Ensure WooCommerce is installed and active.
#
# Installation and activation are two independent states.
# The plugin files may already exist while the plugin itself
# is inactive (for example after restoring wp-content).
#
# Always ensure the plugin is active before continuing.
# ------------------------------------------------------------------

echo "📦 Checking WooCommerce plugin..."

if ! docker compose -f docker-compose.wp.yml run --rm \
    -e HTTP_HOST="$WP_HTTP_HOST"\
    wpcli wp plugin is-installed woocommerce --allow-root
then
    echo "🚀 Installing WooCommerce..."

    docker compose -f docker-compose.wp.yml exec -T wordpress bash -c "
        apt-get update -qq &&
        apt-get install -y -qq unzip curl &&
        cd /var/www/html/wp-content/plugins &&
        rm -rf woocommerce woocommerce.zip &&
        curl -fsSL -o woocommerce.zip https://downloads.wordpress.org/plugin/woocommerce.9.1.4.zip &&
        unzip -oq woocommerce.zip &&
        rm -f woocommerce.zip &&
        chown -R www-data:www-data woocommerce
    "
fi

if ! docker compose -f docker-compose.wp.yml run --rm \
    -e HTTP_HOST="$WP_HTTP_HOST" \
    wpcli wp plugin is-active woocommerce --allow-root
then
    echo "🔌 Activating WooCommerce..."

    docker compose -f docker-compose.wp.yml run --rm \
    -e HTTP_HOST="$WP_HTTP_HOST" \
    wpcli wp plugin activate woocommerce --allow-root
else
    echo "✅ WooCommerce already active"
fi
# ------------------------------------------------------------------
# STEP 2.5 — 🔥 CRITICAL FIX: Permalinks (REST API routing)
# ------------------------------------------------------------------
echo "🔧 Configuring permalinks..."

docker compose -f docker-compose.wp.yml run --rm \
    -e HTTP_HOST="$WP_HTTP_HOST" \
    wpcli wp rewrite structure '/%postname%/' --allow-root

docker compose -f docker-compose.wp.yml run --rm \
    -e HTTP_HOST="$WP_HTTP_HOST" \
    wpcli wp rewrite flush --allow-root

# ------------------------------------------------------------------
# STEP 2.6 — 🔥 Wait for WooCommerce REST API
#
# WordPress may report the WooCommerce plugin as active before the
# REST API routes have finished registering. Poll the endpoint until
# it becomes available before provisioning API credentials.
# ------------------------------------------------------------------
echo -n "⏳ Waiting for WooCommerce REST API"

until curl -fsS http://localhost:8080/wp-json/wc/v3 > /dev/null; do
    echo -n "."
    sleep 3
done

echo
echo "✅ WooCommerce REST API is ready"


# ------------------------------------------------------------------
# STEP 3 — Generate fresh WooCommerce API credentials
#
# This step's responsibility ends the moment credentials exist. It
# does NOT decide where they get stored — that belongs to whoever
# called this script.
#
# • WooCommerce stores the consumer key as a one-way hash, making
#   existing credentials impossible to recover.
#
# • Rather than attempting recovery, this provisions a fresh
#   credential pair on every execution — deterministic, cheap, and
#   idempotent from the caller's point of view.
# ------------------------------------------------------------------

echo "🔑 Provisioning WooCommerce API credentials..."

CREDENTIALS=$(
docker compose -f docker-compose.wp.yml run --rm \
    -e HTTP_HOST="$WP_HTTP_HOST" \
    wpcli wp eval '
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
// Emit credentials for the caller.
//
// This is the ONLY output this script produces on its real stdout
// (fd 3) — see the stdout/stderr split note near the top of the
// file.
// ---------------------------------------------------------------

printf(
    "WC_KEY=%s\nWC_SECRET=%s\n",
    $key,
    $secret
);
' --allow-root
)

# ------------------------------------------------------------------
# STEP 3.1 — Validate credentials (in-memory, no file involved)
#
# Fail fast if provisioning did not complete successfully, before
# handing anything back to the caller. This avoids obscure pytest
# failures later in the workflow, and avoids ever handing back a
# partial/broken credential set.
# ------------------------------------------------------------------

if ! grep -q '^WC_KEY=' <<< "$CREDENTIALS" || \
   ! grep -q '^WC_SECRET=' <<< "$CREDENTIALS"; then
    echo "❌ WooCommerce credential generation returned incomplete output"
    exit 1
fi

{
echo
echo "═══════════════════════════════════════════════════════════════"
echo "✅ WordPress installed"
echo "✅ WooCommerce installed"
echo "✅ REST API available"
echo "✅ WooCommerce API credentials generated"
echo
echo "🚀 Local WooCommerce environment is ready."
echo
echo "Next steps:"
echo "    make test"
echo
echo "═══════════════════════════════════════════════════════════════"
} >&2
# ------------------------------------------------------------------
# Hand credentials back to the caller on the real stdout (fd 3).
#
# Local dev: Makefile's `setup` target pipes this into
#            scripts/write_env_credentials.sh, which merges it into
#            .env.
# CI:        action.yml captures this directly into $GITHUB_ENV —
#            no .env file involved at all.
# ------------------------------------------------------------------

# IMPORTANT
#
# This is intentionally the ONLY data emitted on the script's real
# stdout. Everything else is progress information written to stderr.
#
# This guarantees that callers (Makefile, GitHub Actions, CI, etc.)
# always receive a clean machine-readable stream without parsing logs.
echo "$CREDENTIALS" >&3
