#!/bin/bash

# --------------------------------------------------
# Bootstrap a local WooCommerce development instance.
# Provisions WordPress/WooCommerce and generates credentials
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

# --------------------------------------------------
# PATCH LOG (2026-09-20)
# --------------------------------------------------
# 1. ensure_plugin() helper — plugin provisioning is now self-healing.
#    Root cause of the "No generated credential lines received on stdin"
#    failure: WordPress' DB said wp-graphql was installed/active while
#    wp-content/plugins held no graphql files at all. `wp plugin install`
#    trusted the DB ("Plugin already installed"), `--activate` looked at
#    the filesystem ("could not be found"), WP-CLI exited non-zero with
#    "Error: No plugins activated", `set -e` killed this script, and the
#    caller saw only the downstream stdin error.
#    Every plugin is now gated on is-installed AND is-active, reinstalled
#    with --force when either is false, and verified active afterwards.
#
# 2. Fixed a missing space before a line-continuation backslash in the
#    WooCommerce is-installed check, which silently turned the service
#    name into "wp" and made that check fail on every single run.
#
# 3. Added -T to every `docker compose run`. Without it Compose allocates
#    a TTY, and the captured credential output picks up trailing \r that
#    ends up inside .env values (a classic source of later 401s).
#
# 4. Bounded the WooCommerce REST and GraphQL readiness loops. They used
#    to wait forever, which turns any future breakage into a silent hang
#    instead of a clear error. Revert the *_WAIT_ATTEMPTS lines if the
#    old infinite behaviour is preferred.
#
# NOT part of this patch, for the record:
#   - The WC_KEY/WC_SECRET presence check and the empty-password check
#     in STEP 3.2 below already existed before this patch. They are
#     unchanged here — this patch did not add credential validation.
#   - Giving MySQL a named volume (`db-data:/var/lib/mysql` in
#     docker-compose.wp.yml, alongside the existing wp-data bind mount)
#     was raised as a possible follow-up but was never made — it isn't
#     in docker-compose.wp.yml and isn't required by anything in this
#     file. Today's fix works entirely through ensure_plugin()'s
#     is-installed && is-active gate, regardless of how MySQL is
#     persisted.
# --------------------------------------------------

set -e
set -o pipefail


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
# wpcli helper — one place that knows how to invoke WP-CLI.
#
# -T is mandatory here. Without it Compose allocates a TTY whenever
# this script's stdin is a terminal, and every captured line comes back
# with a trailing \r. That \r is invisible on screen but lands inside
# .env values and breaks authentication later in confusing ways.
# ------------------------------------------------------------------
wpcli() {
  docker compose -f docker-compose.wp.yml run --rm -T \
    -e HTTP_HOST="$WP_HTTP_HOST" \
    wpcli "$@" --allow-root
}

# ------------------------------------------------------------------
# ensure_plugin <slug> <source> [extra wp-cli args...]
#
# Guarantees that a plugin is BOTH present on disk AND active, and
# repairs the state if it isn't.
#
# Why this exists
# ---------------
# `wp plugin is-installed` verifies that WordPress can discover the
# plugin from the filesystem (it calls get_plugins(), which scans
# wp-content/plugins and reads real file headers). `wp plugin is-active`
# verifies a separate, DB-only fact: whether the plugin's slug is
# present in WordPress' `active_plugins` option. Those two sources can
# disagree:
#
#   - ./wp-data is a host bind mount, so plugin FILES survive
#     `docker compose down -v`
#   - the MySQL volume is Docker-managed, so the DB does NOT
#   - every wpcli invocation is a brand-new container reading that bind
#     mount through Docker Desktop's VM file sharing on Windows
#
# Delete one half without the other (or interrupt a bootstrap midway)
# and the DB can still list a plugin as active while its files are gone.
# The old code only checked is-installed (correctly false) before
# deciding whether to install, then separately checked is-active (which
# read the stale DB opinion) before deciding whether to activate — so it
# tried to activate a plugin whose install step it had just skipped,
# which failed with "Error: No plugins activated" and — under set -e —
# took the whole script down before credentials were ever generated.
#
# The gate below joins both checks with &&, so the DB-only is-active
# result is never even consulted unless the filesystem check already
# passed. When either is false it reinstalls with --force, which always
# rewrites the files rather than trusting either side's cached opinion.
# Normal healthy runs still skip the download entirely, so this costs
# nothing in the common case.
# ------------------------------------------------------------------
ensure_plugin() {
  local slug="$1"
  local source="$2"
  shift 2

  if wpcli wp plugin is-installed "$slug" && wpcli wp plugin is-active "$slug"; then
    echo "✅ $slug already installed and active"
    return 0
  fi

  echo "🚀 (Re)provisioning $slug..."

  # --force rewrites the plugin files even when WordPress believes the
  # plugin is already installed. This is the line that makes a
  # DB-says-yes / disk-says-no state repair itself instead of failing.
  retry 5 wpcli wp plugin install "$source" "$@" --force --activate

  # Verify rather than assume. A half-successful provisioning step must
  # never be allowed to reach credential generation, because the failure
  # would then surface somewhere far less obvious.
  if ! wpcli wp plugin is-active "$slug"; then
    echo "❌ $slug was installed but is not active — aborting."
    echo "   Inspect with: docker compose -f docker-compose.wp.yml run --rm -T wpcli wp plugin list --allow-root"
    exit 1
  fi

  echo "✅ $slug installed and active"
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

# Only check that the HTTP server itself is responding here — NOT that
# WordPress is installed/configured. /wp-json only exists once `wp core
# install` has run (further down this script), so probing it here would
# 404 forever on a fresh clone.
#
# Deliberately minimal, on purpose:
#   - no -f              any response at all (even a 4xx/5xx) proves Apache
#                        is up and accepting connections — that's all this
#                        check needs to know
#   - no [[ ]] / -w      one fewer moving part; a plain curl exit status is
#                        enough to answer "did the server respond?"
#   - 127.0.0.1, not
#     localhost          sidesteps IPv6/IPv4 "happy eyeballs" resolution on
#                        `localhost`, which is a known source of flaky curl
#                        calls against Docker Desktop on Windows even when
#                        the port is genuinely up and healthy
#
# Bounded, not infinite: a real startup problem should fail loudly with a
# pointer to the logs, rather than loop forever hiding the actual error.
WP_WAIT_ATTEMPTS=40   # 40 x 3s = 2 minutes
WP_WAIT_COUNT=0
until curl -sS --max-time 5 http://127.0.0.1:8080/ > /dev/null 2>&1; do
  WP_WAIT_COUNT=$((WP_WAIT_COUNT + 1))
  if [ "$WP_WAIT_COUNT" -ge "$WP_WAIT_ATTEMPTS" ]; then
    echo "❌ WordPress container did not respond after $((WP_WAIT_ATTEMPTS * 3))s."
    echo "   Check: docker compose -f docker-compose.wp.yml logs wordpress"
    exit 1
  fi
  echo "Waiting for WordPress..."
  sleep 3
done

# ------------------------------------------------------------------
# Wait for the WordPress CORE FILES to exist on the shared bind mount —
# not just for Apache to answer HTTP.
#
# The HTTP check above only proves the `wordpress` container's own
# Apache is responding, which happens only after ITS entrypoint has
# already copied WordPress core into ./wp-data. wp-cli (below), though,
# runs in its own separate, freshly-created container every time
# (`docker compose run --rm wpcli ...`), reading that same host folder
# through its own independent bind mount. On a fresh clone — especially
# on Windows, where bind mounts go through Docker Desktop's VM-backed
# file sharing — there's a brief window where a brand-new container's
# view of ./wp-data hasn't caught up yet, so the very first wp-cli call
# below can fail with "This does not seem to be a WordPress
# installation" even though the files are already on disk.
#
# wp-load.php is part of WordPress core itself — present as soon as the
# copy finishes, regardless of whether `wp core install` has run yet —
# so checking for it here is purely about closing that race window. It
# is not expected to legitimately be missing at this point; if it never
# appears, something else is actually wrong (see the log hint below).
# ------------------------------------------------------------------
echo "⏳ Waiting for WordPress core files..."
WP_FILES_ATTEMPTS=20   # 20 x 1s = 20s
WP_FILES_COUNT=0
until docker compose -f docker-compose.wp.yml exec -T wordpress \
    test -f /var/www/html/wp-load.php > /dev/null 2>&1; do
  WP_FILES_COUNT=$((WP_FILES_COUNT + 1))
  if [ "$WP_FILES_COUNT" -ge "$WP_FILES_ATTEMPTS" ]; then
    echo "❌ WordPress core files never appeared in ./wp-data after ${WP_FILES_ATTEMPTS}s."
    echo "   Check: docker compose -f docker-compose.wp.yml logs wordpress"
    exit 1
  fi
  sleep 1
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

if docker compose -f docker-compose.wp.yml run --rm -T \
    -e HTTP_HOST="$WP_HTTP_HOST" \
    wpcli wp core is-installed --allow-root; then
  echo "✅ WordPress already installed — skipping"
else
  echo "🚀 Installing WordPress..."
  docker compose -f docker-compose.wp.yml run --rm -T \
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
# STEP 1.5 — Ensure the default WordPress theme is installed and active.
#
# Twenty Twenty-Four is the default WordPress theme used by the
# reference local installation. Installing and activating it explicitly
# keeps the Docker UI consistent and reproducible.
# ------------------------------------------------------------------

DEFAULT_THEME="twentytwentyfour"

echo "🎨 Checking WordPress default theme..."

if ! docker compose -f docker-compose.wp.yml run --rm -T \
    -e HTTP_HOST="$WP_HTTP_HOST" \
    wpcli wp theme is-installed "$DEFAULT_THEME" --allow-root
then
    echo "🚀 Installing $DEFAULT_THEME..."

    retry 5 docker compose -f docker-compose.wp.yml run --rm -T \
        -e HTTP_HOST="$WP_HTTP_HOST" \
        wpcli wp theme install "$DEFAULT_THEME" --activate --allow-root
else
    echo "✅ $DEFAULT_THEME already installed"
fi

if ! docker compose -f docker-compose.wp.yml run --rm -T \
    -e HTTP_HOST="$WP_HTTP_HOST" \
    wpcli wp theme is-active "$DEFAULT_THEME" --allow-root
then
    echo "🎨 Activating $DEFAULT_THEME..."

    docker compose -f docker-compose.wp.yml run --rm -T \
        -e HTTP_HOST="$WP_HTTP_HOST" \
        wpcli wp theme activate "$DEFAULT_THEME" --allow-root
else
    echo "✅ $DEFAULT_THEME already active"
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

# CHANGED: this block used to shell into the `wordpress` container and
# hand-roll the install with apt-get + curl + unzip. Two problems with
# that:
#
#   1. The is-installed guard above it was broken — a missing space
#      before a line-continuation backslash glued the host value onto
#      the service name, so Compose was asked for a service called "wp",
#      the check failed every single run, and WooCommerce was deleted
#      (rm -rf) and re-downloaded on every bootstrap. A network blip
#      during that re-download left NO WooCommerce on disk and killed
#      the script via set -e.
#
#   2. It duplicated download/unzip/ownership logic that WP-CLI already
#      does correctly, and that is proven to work in this exact stack.
#
# ensure_plugin covers both, and applies the same installed-AND-active
# invariant that the graphql plugins now get.
ensure_plugin woocommerce woocommerce --version="$WOOCOMMERCE_VERSION"

# ------------------------------------------------------------------
# STEP 2.1 — Enable Cash on Delivery for UI checkout tests
#
# Checkout tests depend on at least one payment method being available.
# Cash on Delivery is an environment prerequisite, so it is configured
# here during bootstrap rather than inside individual Playwright tests.
#
# The update is idempotent, so repeated local/CI bootstrap runs safely
# converge on the same enabled payment-gateway state.
# ------------------------------------------------------------------
echo "💳 Enabling Cash on Delivery payment method..."

wpcli wp wc payment_gateway update cod     --enabled=true     --user="$WP_ADMIN_USER"

echo "✅ Cash on Delivery payment method enabled"

# ------------------------------------------------------------------
# STEP 2.2 — Enable customer registration on the My Account page
#
# UI registration tests depend on WooCommerce exposing the customer
# registration form from /my-account/. This is part of the test
# environment contract and therefore belongs in the bootstrap layer,
# not in individual Playwright tests.
#
# The option update is idempotent, so repeated local/CI bootstrap runs
# safely converge on the same configuration.
# ------------------------------------------------------------------
echo "👤 Enabling customer registration on My Account..."

docker compose -f docker-compose.wp.yml run --rm -T \
    -e HTTP_HOST="$WP_HTTP_HOST" \
    wpcli wp option update woocommerce_enable_myaccount_registration yes --allow-root

echo "✅ Customer registration on My Account enabled"

# ------------------------------------------------------------------
# STEP 2.2 — Configure checkout shipping destination
#
# UI checkout scenarios require WooCommerce to support a shipping
# destination separate from the customer's billing address.
#
# `shipping` means:
#   • WooCommerce defaults checkout shipping to the customer's
#     saved shipping address.
#   • Checkout can use a shipping address different from billing.
#
# This is environment configuration, not test logic, so it belongs
# in the provisioning layer and is applied consistently locally and
# in CI.
# ------------------------------------------------------------------
echo "🚚 Configuring WooCommerce shipping destination..."

docker compose -f docker-compose.wp.yml run --rm -T \
    -e HTTP_HOST="$WP_HTTP_HOST" \
    wpcli wp option update woocommerce_ship_to_destination shipping --allow-root

echo "✅ WooCommerce shipping destination set to customer shipping address"

# ------------------------------------------------------------------
# STEP 2.3 — Configure UI test shipping zone and Flat Rate method
#
# Checkout UI tests require a deterministic shipping option.
# The zone is limited to Spain because the UI test data uses Spanish
# customer addresses.
#
# The configuration is applied through the WooCommerce REST API so the
# bootstrap remains idempotent: an existing matching zone/method is
# reused, while missing configuration is created.
# ------------------------------------------------------------------
echo "🚚 Configuring Spain shipping zone and Flat Rate method..."

SHIPPING_ZONE_ID="$(
    wpcli wp eval '
        $zones = WC_Shipping_Zones::get_zones();
        foreach ($zones as $zone) {
            if ($zone["zone_name"] === "Test Shipping") {
                echo $zone["zone_id"];
                exit;
            }
        }
    '
)"

if [[ -z "$SHIPPING_ZONE_ID" ]]; then
    echo "➕ Creating Test Shipping zone for Spain..."
    SHIPPING_ZONE_ID="$(
        wpcli wp wc shipping_zone create             --name="Test Shipping"             --user="$WP_ADMIN_USER"             --porcelain
    )"
else
    echo "✅ Test Shipping zone already exists (ID: $SHIPPING_ZONE_ID)"
fi

# Configure the Spain location through WooCommerce PHP APIs.
# The WP-CLI shipping_zone command does not expose a "location"
# subcommand in the WP-CLI version used by this project.
wpcli wp eval '
    $zone_id = (int) "'$SHIPPING_ZONE_ID'";
    $zone = new WC_Shipping_Zone($zone_id);

    $locations = $zone->get_zone_locations();
    $has_spain = false;

    foreach ($locations as $location) {
        if ($location->type === "country" && $location->code === "ES") {
            $has_spain = true;
            break;
        }
    }

    if (!$has_spain) {
        $zone->add_location("ES", "country");
    }
'

if ! wpcli wp wc shipping_zone_method list "$SHIPPING_ZONE_ID"     --user="$WP_ADMIN_USER"     --fields=method_id     --format=csv     | grep -qx "flat_rate"; then

    echo "➕ Adding Flat Rate shipping method..."
    wpcli wp wc shipping_zone_method create         "$SHIPPING_ZONE_ID"         --method_id=flat_rate         --user="$WP_ADMIN_USER"
else
    echo "✅ Flat Rate shipping method already exists"
fi

# Keep the method deterministic for UI tests:
# title = Flat rate, tax status = none, cost = 0.
FLAT_RATE_INSTANCE_ID="$(
    wpcli wp wc shipping_zone_method list "$SHIPPING_ZONE_ID"         --user="$WP_ADMIN_USER"         --fields=instance_id,method_id         --format=csv         | awk -F',' '$2 == "flat_rate" {print $1; exit}'
)"

if [[ -n "$FLAT_RATE_INSTANCE_ID" ]]; then
    wpcli wp eval '
        $zone_id = (int) "'$SHIPPING_ZONE_ID'";
        $instance_id = (int) "'$FLAT_RATE_INSTANCE_ID'";
        $zone = new WC_Shipping_Zone($zone_id);
        $methods = $zone->get_shipping_methods(true);

        if (isset($methods[$instance_id])) {
            $method = $methods[$instance_id];
            $method->update_option("title", "Flat rate");
            $method->update_option("tax_status", "none");
            $method->update_option("cost", "0");
        }
    '
fi

echo "✅ Spain shipping zone configured with Flat Rate at 0.00"

# ------------------------------------------------------------------
# STEP 2.5 — 🔥 CRITICAL FIX: Permalinks (REST API routing)
# ------------------------------------------------------------------
echo "🔧 Configuring permalinks..."

docker compose -f docker-compose.wp.yml run --rm -T \
    -e HTTP_HOST="$WP_HTTP_HOST" \
    wpcli wp rewrite structure '/%postname%/' --allow-root

docker compose -f docker-compose.wp.yml run --rm -T \
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

# CHANGED: bounded instead of infinite. An unbounded loop turns any
# future breakage into a silent hang with no diagnosis; this fails
# loudly and points at the logs instead.
WC_REST_ATTEMPTS=60   # 60 x 3s = 3 minutes
WC_REST_COUNT=0
until curl -fsS --max-time 5 http://localhost:8080/wp-json/wc/v3 > /dev/null; do
    WC_REST_COUNT=$((WC_REST_COUNT + 1))
    if [ "$WC_REST_COUNT" -ge "$WC_REST_ATTEMPTS" ]; then
        echo
        echo "❌ WooCommerce REST API never became ready after $((WC_REST_ATTEMPTS * 3))s."
        echo "   Check: docker compose -f docker-compose.wp.yml logs wordpress"
        exit 1
    fi
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

# This is the exact step that broke the bootstrap. The old code
# checked plugin state in separate steps. In the broken state,
# `is-installed` correctly returned false because the plugin files
# were gone, but the stale DB state still caused the later activation
# path to be attempted, producing:
#
#   Warning: wp-graphql: Plugin already installed.
#   Warning: The 'wp-graphql' plugin could not be found.
#   Error: No plugins activated.
#
# ...exited non-zero, and set -e ended the script long before STEP 3.
# The caller then reported the empty-stdin symptom instead of this.
ensure_plugin wp-graphql wp-graphql --version="$WPGRAPHQL_VERSION"


echo "📦 Checking WPGraphQL for WooCommerce plugin..."

# Pinned via WPGRAPHQL_WOOCOMMERCE_VERSION — see version block above.
# This follows GitHub's standard release-asset URL pattern
# (releases/download/<tag>/<asset>). Worth a manual sanity check after a
# version bump, since GitHub's asset naming isn't guaranteed to stay
# identical across releases — a renamed asset shows up here as a
# retry-exhausted install, not as a confusing failure three steps later.
ensure_plugin wp-graphql-woocommerce \
  "https://github.com/wp-graphql/wp-graphql-woocommerce/releases/download/v${WPGRAPHQL_WOOCOMMERCE_VERSION}/wp-graphql-woocommerce.zip"


# ------------------------------------------------------------------
# STEP 2.8 — Wait for GraphQL API
#
# WordPress may report the plugins as active before the GraphQL
# endpoint is ready to accept requests.
#
# This is deliberately bounded, like the WooCommerce REST readiness
# check above. A real GraphQL startup failure should fail clearly
# rather than leaving the bootstrap hanging indefinitely.
#
# The 3-minute ceiling is a second line of defence: ensure_plugin()
# should prevent an invalid plugin state from reaching this point,
# but this bound prevents an unexpected GraphQL failure from becoming
# an infinite wait.
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

# CHANGED: bounded instead of infinite, same reasoning as the REST
# probe above. Previously, a wp-graphql plugin that was active in the DB
# but missing from disk would leave this loop spinning forever with no
# explanation. ensure_plugin should now prevent that state entirely —
# this bound is the second line of defence.
GRAPHQL_WAIT_ATTEMPTS=60   # 60 x 3s = 3 minutes
GRAPHQL_WAIT_COUNT=0

until RESPONSE=$(curl -s --max-time 5 \
    -H "Content-Type: application/json" \
    -X POST \
    -d '{"query":"{ __typename }"}' \
    http://localhost:8080/graphql 2>/dev/null) &&
    grep -q '"__typename"' <<< "$RESPONSE" &&
    ! grep -q '"errors"' <<< "$RESPONSE"
do
    GRAPHQL_WAIT_COUNT=$((GRAPHQL_WAIT_COUNT + 1))
    if [ "$GRAPHQL_WAIT_COUNT" -ge "$GRAPHQL_WAIT_ATTEMPTS" ]; then
        echo
        echo "❌ GraphQL API never became ready after $((GRAPHQL_WAIT_ATTEMPTS * 3))s."
        echo "   Last response: ${RESPONSE:-<no response>}"
        echo "   Check: docker compose -f docker-compose.wp.yml run --rm -T wpcli wp plugin list --allow-root"
        exit 1
    fi
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
  docker compose -f docker-compose.wp.yml run --rm -T \
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
' --allow-root | tr -d '\r'
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

docker compose -f docker-compose.wp.yml run --rm -T \
    -e HTTP_HOST="$WP_HTTP_HOST" \
    wpcli wp user application-password delete \
    "$WP_ADMIN_USER" --all --allow-root >/dev/null 2>&1 || true

WP_ADMIN_APP_PASSWORD=$(
    docker compose -f docker-compose.wp.yml run --rm -T \
        -e HTTP_HOST="$WP_HTTP_HOST" \
        wpcli wp user application-password create \
        "$WP_ADMIN_USER" "GraphQL API" --porcelain --allow-root | tr -d '\r'
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
