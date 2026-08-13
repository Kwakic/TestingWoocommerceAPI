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
# • Generate a WordPress Application Password for GraphQL authentication


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

WOOCOMMERCE_VERSION="9.1.4"
WPGRAPHQL_VERSION="2.19.0"
WPGRAPHQL_WOOCOMMERCE_VERSION="1.0.3"

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
# before. `OUTPUT=$(bash scripts/setup.sh)` captures ONLY the generated
# credential lines — nothing else. No .env handling and no log-grepping
# required by the caller.
# ------------------------------------------------------------------
exec 3>&1
exec 1>&2

# ------------------------------------------------------------------
# Retry helper for transient failures (network, apt, downloads)
# Usage: retry <max_attempts> <command...>
# ------------------------------------------------------------------
retry() {
  local -r max="$1"; shift
  local -i i=0

  until "$@"; do
    i=$((i+1))

    if [ "$i" -ge "$max" ]; then
      echo "❌ Command failed after $max attempts: $*" >&2
      return 1
    fi

    echo "⚠️ Retry #$i for: $*" >&2
    sleep $((5 * i))
  done
}

# ------------------------------------------------------------------
# Bootstrap starts here
# ------------------------------------------------------------------
echo
echo "═══════════════════════════════════════════════════════════════"
echo "🚀 Bootstrapping local WooCommerce environment"
echo "═══════════════════════════════════════════════════════════════"
echo

echo "⏳ Waiting for WordPress container..."
# Use a slightly stricter probe to fail fast on network issues but loop until ready.
until curl -fsS --max-time 5 http://localhost:8080/wp-json > /dev/null; do
  echo "Waiting for WordPress..."
  sleep 3
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

# Run the install inside the container but wrap the host-side call in retries.
# Use DEBIAN_FRONTEND=noninteractive inside the container to avoid debconf TTY issues.
retry 5 docker compose -f docker-compose.wp.yml exec -T wordpress bash -c "
  set -e
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -qq &&
  apt-get install -y -qq unzip curl || true

  cd /var/www/html/wp-content/plugins || exit 1

  rm -rf woocommerce woocommerce.zip || true

  curl --fail -L \
    --retry 5 \
    --retry-connrefused \
    --retry-delay 5 \
    --connect-timeout 10 \
    --max-time 120 \
    -o woocommerce.zip \
    "https://downloads.wordpress.org/plugin/woocommerce.${WOOCOMMERCE_VERSION}.zip"

  unzip -oq woocommerce.zip && \
  rm -f woocommerce.zip && \
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

until curl -fsS --max-time 5 http://localhost:8080/wp-json/wc/v3 > /dev/null; do
    echo -n "."
    sleep 3
done

echo
echo "✅ WooCommerce REST API is ready"

# ------------------------------------------------------------------
# STEP 2.7 — Ensure GraphQL plugins are installed and active
#
# WPGraphQL provides the GraphQL engine.
# WPGraphQL for WooCommerce exposes WooCommerce data through GraphQL.
#
# Both plugins are provisioned here so the same environment can be
# reproduced locally and in CI. Versions are pinned above rather than
# installing "latest", so every environment gets the same combination.
# ------------------------------------------------------------------

echo "📦 Checking WPGraphQL plugin..."

if ! docker compose -f docker-compose.wp.yml run --rm \
    -e HTTP_HOST="$WP_HTTP_HOST" \
    wpcli wp plugin is-installed wp-graphql --allow-root
then
    echo "🚀 Installing WPGraphQL (pinned to $WPGRAPHQL_VERSION)..."

    # Pinned via WPGRAPHQL_VERSION — see version block above STEP 2.7.
    retry 5 docker compose -f docker-compose.wp.yml run --rm \
        -e HTTP_HOST="$WP_HTTP_HOST" \
        wpcli wp plugin install wp-graphql --version="$WPGRAPHQL_VERSION" --activate --allow-root
else
    echo "✅ WPGraphQL already installed"
fi

if ! docker compose -f docker-compose.wp.yml run --rm \
    -e HTTP_HOST="$WP_HTTP_HOST" \
    wpcli wp plugin is-active wp-graphql --allow-root
then
    echo "🔌 Activating WPGraphQL..."

    docker compose -f docker-compose.wp.yml run --rm \
        -e HTTP_HOST="$WP_HTTP_HOST" \
        wpcli wp plugin activate wp-graphql --allow-root
else
    echo "✅ WPGraphQL already active"
fi


echo "📦 Checking WPGraphQL for WooCommerce plugin..."

if ! docker compose -f docker-compose.wp.yml run --rm \
    -e HTTP_HOST="$WP_HTTP_HOST" \
    wpcli wp plugin is-installed wp-graphql-woocommerce --allow-root
then
    echo "🚀 Installing WPGraphQL for WooCommerce (pinned to $WPGRAPHQL_WOOCOMMERCE_VERSION)..."

    # Pinned via WPGRAPHQL_WOOCOMMERCE_VERSION — see version block above STEP 2.7.
    # This follows GitHub's standard release-asset URL pattern
    # (releases/download/<tag>/<asset>), the same asset filename that
    # releases/latest/download/... already resolved to in a verified run.
    # Worth a manual sanity check after a version bump, since GitHub's
    # asset naming isn't guaranteed to stay identical across releases.
    retry 5 docker compose -f docker-compose.wp.yml run --rm \
        -e HTTP_HOST="$WP_HTTP_HOST" \
        wpcli wp plugin install \
        "https://github.com/wp-graphql/wp-graphql-woocommerce/releases/download/v${WPGRAPHQL_WOOCOMMERCE_VERSION}/wp-graphql-woocommerce.zip" \
        --activate \
        --allow-root
else
    echo "✅ WPGraphQL for WooCommerce already installed"
fi

if ! docker compose -f docker-compose.wp.yml run --rm \
    -e HTTP_HOST="$WP_HTTP_HOST" \
    wpcli wp plugin is-active wp-graphql-woocommerce --allow-root
then
    echo "🔌 Activating WPGraphQL for WooCommerce..."

    docker compose -f docker-compose.wp.yml run --rm \
        -e HTTP_HOST="$WP_HTTP_HOST" \
        wpcli wp plugin activate wp-graphql-woocommerce --allow-root
else
    echo "✅ WPGraphQL for WooCommerce already active"
fi


# ------------------------------------------------------------------
# STEP 2.8 — Wait for GraphQL API
#
# WordPress may report the plugins as active before the GraphQL
# endpoint is ready to accept requests.
#
# This deliberately waits indefinitely, same as the WordPress and
# WooCommerce REST readiness checks above — no arbitrary attempt
# ceiling. The script waits until the service is genuinely ready,
# not until a guess about how long that "should" take.
#
# GraphQL's HTTP 200 does NOT necessarily mean success (see
# graphql_response.py's contract) — a 200 response can still carry
# an errors[] payload. So this probe sends a real query
# ({ __typename }) and checks the response body, not just the HTTP
# status:
#   - must contain "__typename"  -> GraphQL actually answered
#   - must NOT contain "errors"  -> not a GraphQL-level failure
#
# curl runs with -s (silent, no -S) and stderr redirected to
# /dev/null, so the connection-refused/timeout attempts that are
# normal during WordPress startup don't spam the console — only the
# final "ready" state gets printed.
# ------------------------------------------------------------------

echo -n "⏳ Waiting for GraphQL API"

until RESPONSE=$(curl -s --max-time 5 \
    -H "Content-Type: application/json" \
    -X POST \
    -d '{"query":"{ __typename }"}' \
    http://localhost:8080/graphql 2>/dev/null) &&
    grep -q '"__typename"' <<< "$RESPONSE" &&
    ! grep -q '"errors"' <<< "$RESPONSE"
do
    echo -n "."
    sleep 3
done

echo
echo "✅ GraphQL API is ready"

# ------------------------------------------------------------------
# STEP 3 — Generate fresh API credentials# ------------------------------------------------------------------
#
# This step provisions the credentials required by both API surfaces:
#
#   • WooCommerce REST API → WC_KEY / WC_SECRET
#   • WPGraphQL mutations  → WP_ADMIN_APP_PASSWORD
#
# The credentials are generated here and emitted to the caller. This
# script does NOT write .env directly; the caller decides where the
# machine-readable output is stored (local .env or CI environment).
#
# WooCommerce credentials are regenerated because WooCommerce stores
# the consumer key as a one-way hash and the original key cannot be
# recovered.
#
# The GraphQL Application Password is also regenerated on each setup.
# The previous Application Passwords are revoked first so repeated
# provisioning does not accumulate stale credentials.
# ------------------------------------------------------------------

echo "🔑 Provisioning WooCommerce API credentials..."

CREDENTIALS=$(
  docker compose -f docker-compose.wp.yml run --rm \
    -e HTTP_HOST="$WP_HTTP_HOST" \
    wpcli wp eval '
global $wpdb;

// ---------------------------------------------------------------
// Resolve the administrator account.
// ---------------------------------------------------------------

$admin = get_user_by("login", "admin");

if (!$admin) {
    fwrite(STDERR, "Administrator account not found.\n");
    exit(1);
}

$user_id = $admin->ID;

// ---------------------------------------------------------------
// Remove previously generated WooCommerce API credentials.
//
// The consumer key cannot be reconstructed because WooCommerce
// stores only its hash. Regenerating credentials keeps the local
// environment deterministic.
// ---------------------------------------------------------------

$wpdb->query(
    "DELETE FROM {$wpdb->prefix}woocommerce_api_keys"
);

// ---------------------------------------------------------------
// Generate a fresh WooCommerce credential pair.
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
// Emit WooCommerce credentials.
// ---------------------------------------------------------------

printf(
    "WC_KEY=%s\nWC_SECRET=%s\n",
    $key,
    $secret
);
' --allow-root
)

# ------------------------------------------------------------------
# STEP 3.1 — Generate a fresh WordPress Application Password
#
# WPGraphQL mutation authentication uses WordPress Application
# Passwords over HTTP Basic Auth. This is deliberately separate from
# the WooCommerce OAuth1 credentials used by the REST API.
#
# WP_ENVIRONMENT_TYPE=local is configured in docker-compose.wp.yml,
# which allows Application Password authentication on this plain-HTTP
# local stack.
#
# The password is created with --porcelain so only the secret itself
# is captured. It is never printed as human-readable setup output.
# ------------------------------------------------------------------

echo "🔐 Provisioning GraphQL Application Password..."

docker compose -f docker-compose.wp.yml run --rm \
    -e HTTP_HOST="$WP_HTTP_HOST" \
    wpcli wp user application-password delete \
    "$WP_ADMIN_USER" --all --allow-root >/dev/null 2>&1 || true

WP_ADMIN_APP_PASSWORD=$(
    docker compose -f docker-compose.wp.yml run --rm \
        -e HTTP_HOST="$WP_HTTP_HOST" \
        wpcli wp user application-password create \
        "$WP_ADMIN_USER" "GraphQL API" --porcelain --allow-root
)

# ------------------------------------------------------------------
# STEP 3.2 — Validate generated credentials
#
# Fail fast if any required credential is missing before handing the
# machine-readable output back to the caller.
# ------------------------------------------------------------------

if ! grep -q '^WC_KEY=' <<< "$CREDENTIALS" || \
   ! grep -q '^WC_SECRET=' <<< "$CREDENTIALS"; then
    echo "❌ WooCommerce credential generation returned incomplete output"
    exit 1
fi

if [[ -z "$WP_ADMIN_APP_PASSWORD" ]]; then
    echo "❌ GraphQL Application Password generation returned no password"
    exit 1
fi

# ------------------------------------------------------------------
# STEP 3.3 — Add GraphQL credentials to the machine-readable output
#
# WP_ADMIN_USER is static configuration and is therefore not emitted
# here. It is already defined in .env.example and matches the admin
# account provisioned above.
# ------------------------------------------------------------------

CREDENTIALS="${CREDENTIALS}"$'\n'"WP_ADMIN_APP_PASSWORD=${WP_ADMIN_APP_PASSWORD}"

{
echo
echo "═══════════════════════════════════════════════════════════════"
echo "✅ WordPress installed"
echo "✅ WooCommerce installed"
echo "✅ REST API available"
echo "✅ GraphQL API available"
echo "✅ WooCommerce API credentials generated"
echo "✅ GraphQL Application Password generated"
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
#            scripts/write_env_credentials.sh, which merges the
#            generated credentials into .env.
#
# CI: action.yml can capture the same machine-readable stream into
#     the CI environment without requiring a local .env file.
#
# IMPORTANT:
# This is intentionally the ONLY data emitted on the script's real
# stdout. Everything else is progress information written to stderr.
# ------------------------------------------------------------------

echo "$CREDENTIALS" >&3
