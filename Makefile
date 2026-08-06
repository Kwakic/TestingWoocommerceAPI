# Makefile = orchestrates project execution
# It controls:
# - environment bootstrap (.env)
# - docker
# - setup
# - python environment
# - tests
#
# Ownership model:
#   Makefile                      -> orchestration; the ONLY thing that
#                                     creates .env
#   .env.example                  -> static local defaults (DB, logging,
#                                     framework options)
#   scripts/setup.sh              -> dynamic infra ONLY (WordPress,
#                                     WooCommerce, API keys). It never
#                                     touches .env — it just prints fresh
#                                     credentials to stdout.
#   scripts/write_env_credentials.sh -> the ONLY thing that writes
#                                     WooCommerce credentials into .env
#   Python                        -> consumes .env, never creates it

.PHONY: up setup install test test-ci run down clean ensure-env

# --------------------------------------------------
# Ensure a local .env exists before anything else runs
#
# Deleting .env used to break `make run` completely, because setup.sh was
# the only thing that knew how to recreate it — and it only did a partial
# job. This step restores the proper ownership: the Makefile is responsible
# for .env existing at all; setup.sh is only ever responsible for the
# WooCommerce credentials inside it.
# --------------------------------------------------
ensure-env:
	@if [ ! -f .env ]; then \
		echo "📄 .env not found — creating from .env.example"; \
		cp .env.example .env; \
	else \
		echo "✅ .env already exists — leaving it untouched"; \
	fi

# --------------------------------------------------
# Start infrastructure
#
# No pre-flight cleanup needed here: docker-compose.wp.yml no longer
# pins fixed container names, so every container Compose creates is
# scoped to this project — there's nothing global left to collide with,
# and therefore nothing to force-remove. See the comment at the top of
# docker-compose.wp.yml for the full reasoning.
# --------------------------------------------------
up: ensure-env
	@echo "📁 Ensuring WordPress data directory exists..."
	@mkdir -p wp-data
	@echo "🐳 Starting Docker infrastructure..."
	# Start the Docker infrastructure before running the bootstrap.
	# This is required because the setup step uses transient WP-CLI
	# containers that depend on the WordPress and MySQL services
	# already being available. Starting Docker here also prevents
	# accidental reuse of stale containers during a fresh clone.
	docker compose -f docker-compose.wp.yml up -d
# --------------------------------------------------
# Bootstrap WordPress + WooCommerce, then merge the fresh WooCommerce
# credentials into .env.
#
# setup.sh's only output on stdout is the WC_KEY / WC_SECRET lines — everything else it prints (progress, WP-CLI
# chatter) goes to stderr, so you still see full output on the
# terminal. write_env_credentials.sh is the only thing in the whole
# project that writes those values into .env, and it never touches
# anything else in that file.
# --------------------------------------------------
setup: ensure-env
	@echo "🔧 Bootstrapping WooCommerce..."
	@bash scripts/setup.sh | bash scripts/write_env_credentials.sh

# --------------------------------------------------
# Install Python framework (editable mode)
# --------------------------------------------------
install:
	@echo "📦 Installing EcommerceAPI framework..."
	pip install -e "./EcommerceAPI[dev]"

# --------------------------------------------------
# Run tests (developer-friendly)
# --------------------------------------------------
test:
	pytest -v

# --------------------------------------------------
# Run tests (CI-style with clean Allure results)
# --------------------------------------------------
test-ci:
	pytest --clean-alluredir --alluredir=reports/allure-results -v

# --------------------------------------------------
# Full local developer workflow.
#
# This is the primary entry point for contributors.
# It prepares a complete local development environment:
#
#   • creates .env (if missing)
#   • starts the Docker infrastructure
#   • bootstraps WordPress + WooCommerce
#   • installs the Python framework
#   • runs the test suite
#
# Equivalent to:
#
#   make up
#   make setup
#   make install
#   make test
#
# Most contributors only need:
#
#   make run
# --------------------------------------------------
run: ensure-env up setup install test

#run: up setup install test -->It's functionally equivalent, avoids declaring the same dependency twice, and expresses the orchestration more cleanly.

# --------------------------------------------------
# Stop infrastructure and remove everything Docker manages
# (named/anonymous volumes + orphaned containers).
#
# NOTE: this does NOT remove ./wp-data — see `clean` below.
# --------------------------------------------------
down:
	docker compose -f docker-compose.wp.yml down -v --remove-orphans

# --------------------------------------------------
# Full clean reset, including the bind-mounted WordPress files.
#
# `down -v` cannot remove ./wp-data because it's a bind mount, not a
# Docker-managed volume — Docker has no authority to delete host folders.
# Use this target when you want a truly from-scratch environment.
# --------------------------------------------------
clean: down
	rm -rf wp-data
