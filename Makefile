# Makefile = orchestrates project execution

# These recipes use POSIX shell syntax. GNU Make on Windows defaults to
# cmd.exe unless the shell is selected explicitly, so choose Bash for the
# supported Git Bash developer environment.
ifeq ($(OS),Windows_NT)
SHELL := bash
.SHELLFLAGS := -c
endif

# What each Make target actually does?
#
# The Makefile has a clear separation of responsibilities:
#
# Target:			 Actual responsibility:
# make ensure-env	 Creates .env from .env.example if missing
# make venv			 Creates .venv using Python 3.13+ and validates it
# make up			 Starts Docker Compose infrastructure
# make setup		 Provisions WordPress/WooCommerce, generates API credentials and seeds products and UI users
# make install		 Installs the framework, development dependencies, Git hooks and Playwright browsers
# make test			 Runs the full pytest suite
# make test-ci		 Runs pytest with clean Allure results
# make run			 Orchestrates environment preparation and full test execution
# make down			 Stops containers and removes Docker volumes
# make clean		 Performs a full Docker and WordPress data reset
# make test-docker	 Runs tests inside the Docker test-runner image, then cleans up


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
#                                     WooCommerce, API credentials). It
#                                     never touches .env — it just prints
#                                     fresh credentials to stdout.
#   seed_test_products.sh         -> Seed deterministic baseline WooCommerce products.
#   seed_test_users.sh            -> Seed persistent UI customers.
#   scripts/write_env_credentials.sh -> the ONLY thing that writes
#                                     generated API credentials into .env
#   Python                        -> consumes .env, never creates it

.PHONY: up setup install test test-ci test-docker run down clean ensure-env venv guard-test-lock

DOCKER_INFRA ?= managed

# Host pytest and Docker test execution share the local WordPress database.
# The lock is acquired atomically so only one test workflow can change or use
# that environment at a time. The Makefile-owned workflows pass the internal
# flag to their recursive targets; direct Make commands are blocked while a
# test run owns the lock.
guard-test-lock:
	@if [ -d .test-execution.lock ] && [ "$$TEST_EXECUTION_LOCK_HELD_BY_MAKE" != "1" ]; then \
		echo "[ERROR] A test execution currently owns the local WooCommerce environment."; \
		if [ -f .test-execution.lock/owner.txt ]; then cat .test-execution.lock/owner.txt; fi; \
		echo "Wait for it to finish before changing or stopping the environment."; \
		exit 2; \
	fi

# --------------------------------------------------
# Project-local virtual environment.
#
# `make run` must be self-contained: it should never depend on whichever
# `python`/`pip` happens to resolve first on the developer's PATH (system
# install, Windows App Execution Alias stub, an unrelated venv another
# project activated, etc). That ambiguity is exactly what caused two
# different Python environments to silently diverge between a plain
# `git clone` and an existing dev checkout.
#
# From here on, `venv` is created once at the repo root and every
# subsequent step (install, pytest) invokes $(VENV_PYTHON) explicitly —
# never bare `python`/`pip`. Point PyCharm/VS Code at this same
# .venv and the IDE, Git Bash, and `make run` all share one environment.
# --------------------------------------------------
VENV_DIR := .venv

ifeq ($(OS),Windows_NT)
VENV_PYTHON := $(VENV_DIR)/Scripts/python.exe
else
VENV_PYTHON := $(VENV_DIR)/bin/python
endif

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
		echo "[INFO] .env not found - creating from .env.example"; \
		cp .env.example .env; \
	else \
		echo "[OK] .env already exists - leaving it untouched"; \
	fi

# --------------------------------------------------
# Create the project virtual environment if it doesn't exist yet.
#
# `make run` must never trust whatever `python`/`python3` happens to
# resolve to on PATH — that ambiguity is exactly what let a fresh
# clone create a .venv with the wrong Python version while the dev
# repo used a different one. This target searches a short list of
# known interpreter names (and, on Windows, the `py` launcher) for one
# that actually reports >= 3.13, and refuses to create .venv with
# anything older. It also re-checks the resulting .venv itself, in
# case a stale/broken one is already sitting on disk.
#
# If auto-detection can't find a qualifying interpreter (e.g. Python
# 3.13 is installed but not on PATH), point at it explicitly:
#
#   make install PYBIN=/c/Users/you/AppData/Local/Programs/Python/Python313/python.exe
#
# Every other target below must keep going through $(VENV_PYTHON) —
# never bare `python`/`pip`.
# --------------------------------------------------
PYTHON_MIN_MAJOR := 3
PYTHON_MIN_MINOR := 13
PYBIN ?=

venv:
	@if [ -f "$(VENV_PYTHON)" ]; then \
		echo "[OK] Virtual environment already exists - reusing it"; \
	else \
		echo "[VENV] Looking for a Python $(PYTHON_MIN_MAJOR).$(PYTHON_MIN_MINOR)+ interpreter..."; \
		FOUND=""; \
		if [ -n "$(PYBIN)" ]; then \
			if command -v "$(PYBIN)" >/dev/null 2>&1 || [ -x "$(PYBIN)" ]; then \
				VER=$$("$(PYBIN)" -c "import sys; print('%d.%d' % sys.version_info[:2])" 2>/dev/null); \
				MAJ=$$(printf '%s\n' "$$VER" | cut -d. -f1); MIN=$$(printf '%s\n' "$$VER" | cut -d. -f2); \
				if [ "$$MAJ" = "$(PYTHON_MIN_MAJOR)" ] && [ -n "$$MIN" ] && [ "$$MIN" -ge $(PYTHON_MIN_MINOR) ] 2>/dev/null; then \
					echo "[OK] Found Python $$VER via PYBIN='$(PYBIN)'"; \
					FOUND="$(PYBIN)"; \
				fi; \
			fi; \
			if [ -z "$$FOUND" ]; then \
				echo "[ERROR] PYBIN='$(PYBIN)' is not a working Python $(PYTHON_MIN_MAJOR).$(PYTHON_MIN_MINOR)+ interpreter."; \
				exit 1; \
			fi; \
		else \
			for CAND in python$(PYTHON_MIN_MAJOR).$(PYTHON_MIN_MINOR) python$(PYTHON_MIN_MAJOR) python; do \
				if command -v "$$CAND" >/dev/null 2>&1; then \
					VER=$$("$$CAND" -c "import sys; print('%d.%d' % sys.version_info[:2])" 2>/dev/null); \
					if [ -n "$$VER" ]; then \
						MAJ=$$(printf '%s\n' "$$VER" | cut -d. -f1); MIN=$$(printf '%s\n' "$$VER" | cut -d. -f2); \
						if [ "$$MAJ" = "$(PYTHON_MIN_MAJOR)" ] && [ "$$MIN" -ge $(PYTHON_MIN_MINOR) ]; then \
							echo "[OK] Found Python $$VER via '$$CAND'"; \
							FOUND="$$CAND"; \
							break; \
						else \
							echo "[SKIP] '$$CAND' is Python $$VER - too old"; \
						fi; \
					fi; \
				fi; \
			done; \
			if [ -z "$$FOUND" ] && command -v py >/dev/null 2>&1; then \
				VER=$$(py -$(PYTHON_MIN_MAJOR).$(PYTHON_MIN_MINOR) -c "import sys; print('%d.%d' % sys.version_info[:2])" 2>/dev/null); \
				if [ -n "$$VER" ]; then \
					echo "[OK] Found Python $$VER via 'py -$(PYTHON_MIN_MAJOR).$(PYTHON_MIN_MINOR)'"; \
					FOUND="py -$(PYTHON_MIN_MAJOR).$(PYTHON_MIN_MINOR)"; \
				fi; \
			fi; \
		fi; \
		if [ -z "$$FOUND" ]; then \
			echo "[ERROR] No Python $(PYTHON_MIN_MAJOR).$(PYTHON_MIN_MINOR)+ interpreter found."; \
			echo "        Checked: python$(PYTHON_MIN_MAJOR).$(PYTHON_MIN_MINOR), python$(PYTHON_MIN_MAJOR), python, py -$(PYTHON_MIN_MAJOR).$(PYTHON_MIN_MINOR)"; \
			echo "        Install Python $(PYTHON_MIN_MAJOR).$(PYTHON_MIN_MINOR)+, or if it's already installed"; \
			echo "        but not on PATH, point at it directly:"; \
			echo "          make install PYBIN=/path/to/python.exe"; \
			exit 1; \
		fi; \
		echo "[VENV] Creating virtual environment in $(VENV_DIR) with '$$FOUND'..."; \
		$$FOUND -m venv $(VENV_DIR); \
	fi
	@VER=$$("$(VENV_PYTHON)" -c "import sys; print('%d.%d' % sys.version_info[:2])" 2>/dev/null); \
	MAJ=$$(printf '%s\n' "$$VER" | cut -d. -f1); MIN=$$(printf '%s\n' "$$VER" | cut -d. -f2); \
	if [ "$$MAJ" != "$(PYTHON_MIN_MAJOR)" ] || [ "$$MIN" -lt $(PYTHON_MIN_MINOR) ]; then \
		echo "[ERROR] $(VENV_PYTHON) is Python $$VER, but $(PYTHON_MIN_MAJOR).$(PYTHON_MIN_MINOR)+ is required."; \
		echo "        Delete $(VENV_DIR) and re-run so it can be recreated correctly."; \
		exit 1; \
	fi; \
	echo "[OK] Virtual environment is Python $$VER"

# --------------------------------------------------
# Start infrastructure
#
# No pre-flight cleanup needed here: docker-compose.wp.yml no longer
# pins fixed container names, so every container Compose creates is
# scoped to this project — there's nothing global left to collide with,
# and therefore nothing to force-remove. See the comment at the top of
# docker-compose.wp.yml for the full reasoning.
# --------------------------------------------------
up: ensure-env guard-test-lock
	@echo "[OK] Ensuring WordPress data directory exists..."
	@mkdir -p wp-data
	@echo "[DOCKER]  Starting Docker infrastructure..."
	@if [ ! -f wp-data/wp-load.php ]; then \
		WP_CONTAINER="$$(docker compose -f docker-compose.wp.yml ps -aq wordpress 2>/dev/null)"; \
		if [ -n "$$WP_CONTAINER" ]; then \
			echo "[DOCKER]  Existing WordPress container has no core files - recreating it..."; \
			docker compose -f docker-compose.wp.yml up -d --force-recreate wordpress; \
		else \
			docker compose -f docker-compose.wp.yml up -d; \
		fi; \
	else \
		docker compose -f docker-compose.wp.yml up -d; \
	fi
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
setup: ensure-env guard-test-lock
	@echo "[SETUP] Bootstrapping WooCommerce..."
	@bash scripts/setup.sh | bash scripts/write_env_credentials.sh
	@echo "[SETUP] Seeding WooCommerce test products..."
	@bash scripts/seed_test_products.sh
	@echo "[SETUP] Seeding UI test users..."
	@set -a; . ./.env; set +a; bash scripts/seed_test_users.sh

# --------------------------------------------------
# Install Python framework (editable mode)
# --------------------------------------------------
install: venv
	@echo "[INSTALL] Installing EcommerceAPI framework..."
	$(VENV_PYTHON) -m pip install --upgrade pip
	$(VENV_PYTHON) -m pip install -e "./EcommerceAPI[dev]"
	# Install the repository Git hook so fresh clones automatically run pre-commit.
	@echo "[PRE-COMMIT] Installing Git hooks..."
	$(VENV_PYTHON) -m pre_commit install
	# Playwright is installed as a Python dev dependency above, but its
	# browser binaries are a separate installation. Keep this in the
	# project bootstrap so developers do not need to run it manually.
	@echo "[PLAYWRIGHT] Installing browser binaries..."
	$(VENV_PYTHON) -m playwright install

# --------------------------------------------------
# Run tests (developer-friendly)
# --------------------------------------------------
test: venv
	$(VENV_PYTHON) -m pytest -v

# --------------------------------------------------
# Run tests (CI-style with clean Allure results)
# --------------------------------------------------
test-ci: venv
	$(VENV_PYTHON) -m pytest --clean-alluredir --alluredir=reports/allure-results -v

# --------------------------------------------------
# Run pytest in the reusable Docker test-runner image.
#
# Usage:
#   make test-docker
#   make test-docker PYTEST_ARGS='-m "customers and integration" -n auto'
#   make test-docker DOCKER_INFRA=reuse PYTEST_ARGS='tests/orders/api -n auto'
#
# managed (default) owns a fresh Compose lifecycle and refuses to take over
# any existing Compose containers. reuse requires a running, provisioned stack
# and never starts, provisions, or stops it. Both modes hold the shared test
# lock, preserve artifacts with bind mounts, restore WordPress URLs, and retain
# the original pytest/setup failure after cleanup.
# --------------------------------------------------
test-docker: ensure-env
	@set +e; \
	TEST_EXIT=0; \
	CLEANUP_EXIT=0; \
	SITE_URL_SAVED=0; \
	OWN_INFRA=0; \
	LOCK_ACQUIRED=0; \
	LOCK_DIR=.test-execution.lock; \
	LOCK_TOKEN="make-docker-$$(date +%s)-$$$$"; \
	ORIGINAL_HOME=; \
	ORIGINAL_SITEURL=; \
	if [ "$(DOCKER_INFRA)" != "managed" ] && [ "$(DOCKER_INFRA)" != "reuse" ]; then \
		echo "[ERROR] DOCKER_INFRA must be 'managed' or 'reuse'."; \
		exit 2; \
	fi; \
	if ! mkdir "$$LOCK_DIR" 2>/dev/null; then \
		echo "[ERROR] Another test execution already owns the local environment lock."; \
		if [ -f "$$LOCK_DIR/owner.txt" ]; then cat "$$LOCK_DIR/owner.txt"; fi; \
		echo "Wait for it to finish. If it was interrupted, verify no test is running before removing the stale lock directory."; \
		exit 2; \
	fi; \
	LOCK_ACQUIRED=1; \
	if ! printf 'token=%s\npid=%s\nmode=docker-%s\n' "$$LOCK_TOKEN" "$$$$" "$(DOCKER_INFRA)" > "$$LOCK_DIR/owner.txt"; then \
		rm -f "$$LOCK_DIR/owner.txt"; rmdir "$$LOCK_DIR"; \
		echo "[ERROR] Could not write the local environment lock."; \
		exit 2; \
	fi; \
	TEST_EXECUTION_LOCK_HELD_BY_MAKE=1; export TEST_EXECUTION_LOCK_HELD_BY_MAKE; \
	cleanup() { \
		STATUS=$$?; \
		trap - 0 INT TERM; \
		if [ "$$SITE_URL_SAVED" -eq 1 ]; then \
			echo "[DOCKER] Restoring WordPress site URLs..."; \
			MSYS_NO_PATHCONV=1 docker compose -f docker-compose.wp.yml run --rm -T wpcli wp option update home "$$ORIGINAL_HOME" --allow-root >/dev/null; \
			HOME_RESTORE_EXIT=$$?; \
			MSYS_NO_PATHCONV=1 docker compose -f docker-compose.wp.yml run --rm -T wpcli wp option update siteurl "$$ORIGINAL_SITEURL" --allow-root >/dev/null; \
			SITEURL_RESTORE_EXIT=$$?; \
			if [ "$$HOME_RESTORE_EXIT" -ne 0 ] || [ "$$SITEURL_RESTORE_EXIT" -ne 0 ]; then \
				echo "[ERROR] Could not restore the original WordPress site URLs."; \
				CLEANUP_EXIT=1; \
			fi; \
		fi; \
		if [ "$$OWN_INFRA" -eq 1 ]; then \
			echo "[DOCKER] Stopping managed WooCommerce infrastructure..."; \
			TEST_EXECUTION_LOCK_HELD_BY_MAKE=1 $(MAKE) --no-print-directory down; \
			DOWN_EXIT=$$?; \
			if [ "$$CLEANUP_EXIT" -eq 0 ] && [ "$$DOWN_EXIT" -ne 0 ]; then CLEANUP_EXIT=$$DOWN_EXIT; fi; \
		else \
			echo "[DOCKER] Reused WooCommerce infrastructure remains running."; \
		fi; \
		if [ "$$LOCK_ACQUIRED" -eq 1 ] && grep -Fqx "token=$$LOCK_TOKEN" "$$LOCK_DIR/owner.txt" 2>/dev/null; then \
			rm -f "$$LOCK_DIR/owner.txt"; \
			rmdir "$$LOCK_DIR" || CLEANUP_EXIT=1; \
		fi; \
		FINAL_EXIT=$$TEST_EXIT; \
		if [ "$$FINAL_EXIT" -eq 0 ]; then FINAL_EXIT=$$CLEANUP_EXIT; fi; \
		if [ "$$FINAL_EXIT" -eq 0 ] && [ "$$STATUS" -ne 0 ]; then FINAL_EXIT=$$STATUS; fi; \
		exit "$$FINAL_EXIT"; \
	}; \
	trap cleanup 0; \
	trap 'TEST_EXIT=130; exit 130' INT; \
	trap 'TEST_EXIT=143; exit 143' TERM; \
	EXISTING_CONTAINERS=$$(docker compose -f docker-compose.wp.yml ps -aq 2>/dev/null); \
	if [ "$(DOCKER_INFRA)" = "managed" ]; then \
		if [ -n "$$EXISTING_CONTAINERS" ]; then \
			echo "[ERROR] Managed mode will not take over an existing Compose environment."; \
			echo "Use DOCKER_INFRA=reuse for a running, provisioned stack, or stop it explicitly before a managed run."; \
			TEST_EXIT=2; \
			exit "$$TEST_EXIT"; \
		fi; \
		OWN_INFRA=1; \
		echo "[DOCKER] Starting a managed WooCommerce environment..."; \
		TEST_EXECUTION_LOCK_HELD_BY_MAKE=1 $(MAKE) --no-print-directory up; \
		TEST_EXIT=$$?; \
		if [ "$$TEST_EXIT" -eq 0 ]; then \
			TEST_EXECUTION_LOCK_HELD_BY_MAKE=1 $(MAKE) --no-print-directory setup; \
			TEST_EXIT=$$?; \
		fi; \
	else \
		if [ -z "$$EXISTING_CONTAINERS" ]; then \
			echo "[ERROR] Reuse mode requires an existing running Compose environment."; \
			TEST_EXIT=2; \
			exit "$$TEST_EXIT"; \
		fi; \
		DB_RUNNING=$$(docker compose -f docker-compose.wp.yml ps -q db); \
		WP_RUNNING=$$(docker compose -f docker-compose.wp.yml ps -q wordpress); \
		if [ -z "$$DB_RUNNING" ] || [ -z "$$WP_RUNNING" ]; then \
			echo "[ERROR] Reuse mode requires both db and wordpress services to be running."; \
			TEST_EXIT=2; \
			exit "$$TEST_EXIT"; \
		fi; \
		echo "[DOCKER] Reusing the existing provisioned WooCommerce environment..."; \
	fi; \
	if [ "$$TEST_EXIT" -eq 0 ]; then \
		ORIGINAL_HOME_RAW=$$(MSYS_NO_PATHCONV=1 docker compose -f docker-compose.wp.yml run --rm -T wpcli wp option get home --allow-root); \
		HOME_GET_EXIT=$$?; \
		ORIGINAL_HOME=$$(printf '%s' "$$ORIGINAL_HOME_RAW" | tr -d '\r'); \
		ORIGINAL_SITEURL_RAW=$$(MSYS_NO_PATHCONV=1 docker compose -f docker-compose.wp.yml run --rm -T wpcli wp option get siteurl --allow-root); \
		SITEURL_GET_EXIT=$$?; \
		ORIGINAL_SITEURL=$$(printf '%s' "$$ORIGINAL_SITEURL_RAW" | tr -d '\r'); \
		if [ "$$HOME_GET_EXIT" -ne 0 ] || [ "$$SITEURL_GET_EXIT" -ne 0 ] || [ -z "$$ORIGINAL_HOME" ] || [ -z "$$ORIGINAL_SITEURL" ]; then \
			echo "[ERROR] Could not read the current WordPress site URLs."; \
			TEST_EXIT=1; \
		else \
			SITE_URL_SAVED=1; \
			MSYS_NO_PATHCONV=1 docker compose -f docker-compose.wp.yml run --rm -T wpcli wp option update home http://wordpress --allow-root >/dev/null; \
			TEST_EXIT=$$?; \
			if [ "$$TEST_EXIT" -eq 0 ]; then \
				MSYS_NO_PATHCONV=1 docker compose -f docker-compose.wp.yml run --rm -T wpcli wp option update siteurl http://wordpress --allow-root >/dev/null; \
				TEST_EXIT=$$?; \
			fi; \
		fi; \
	fi; \
	if [ "$$TEST_EXIT" -eq 0 ]; then \
		mkdir -p reports test-results; \
		TEST_EXIT=$$?; \
	fi; \
	if [ "$$TEST_EXIT" -eq 0 ]; then \
		DB_CONTAINER=$$(docker compose -f docker-compose.wp.yml ps -q db); \
		if [ -z "$$DB_CONTAINER" ]; then \
			echo "[ERROR] Could not find the Compose db container to resolve its network."; \
			TEST_EXIT=1; \
		else \
			DB_ENVIRONMENT=$$(docker inspect -f '{{range .Config.Env}}{{println .}}{{end}}' "$$DB_CONTAINER"); \
			DB_USER=$$(printf '%s\n' "$$DB_ENVIRONMENT" | sed -n 's/^MYSQL_USER=//p'); \
			DB_PASSWORD=$$(printf '%s\n' "$$DB_ENVIRONMENT" | sed -n 's/^MYSQL_PASSWORD=//p'); \
			DB_DATABASE=$$(printf '%s\n' "$$DB_ENVIRONMENT" | sed -n 's/^MYSQL_DATABASE=//p'); \
			NETWORK=$$(docker inspect -f '{{range $$name, $$network := .NetworkSettings.Networks}}{{printf "%s " $$name}}{{end}}' "$$DB_CONTAINER"); \
			NETWORK=$$(printf '%s\n' "$$NETWORK" | cut -d' ' -f1); \
			if [ -z "$$DB_USER" ] || [ -z "$$DB_PASSWORD" ] || [ -z "$$DB_DATABASE" ]; then \
				echo "[ERROR] Could not resolve application DB credentials from the Compose db container."; \
				TEST_EXIT=1; \
			elif [ -z "$$NETWORK" ]; then \
				echo "[ERROR] Could not resolve the Compose network from the db container."; \
				TEST_EXIT=1; \
			else \
				HOST_ROOT=$$(pwd -W 2>/dev/null || pwd); \
				MSYS_NO_PATHCONV=1 docker run --rm \
					--network "$$NETWORK" \
					--env-file .env \
					-e AUTO_ALLURE_REPORT=false \
					-e "DB_USER=$$DB_USER" \
					-e "DB_PASSWORD=$$DB_PASSWORD" \
					-e "DB_DATABASE=$$DB_DATABASE" \
					-e API_ENV=docker \
					-e DOCKER_INFRA="$(DOCKER_INFRA)" \
					-e TEST_EXECUTION_LOCK_HELD_BY_MAKE=0 \
					-e DB_HOST=db \
					-e DB_PORT=3306 \
					-e LOG_DIR=/app/reports/logs \
					--mount "type=bind,source=$$HOST_ROOT/reports,target=/app/reports" \
					--mount "type=bind,source=$$HOST_ROOT/test-results,target=/app/test-results" \
					ecommerceapi-test-runner pytest --clean-alluredir \
						--tracing retain-on-failure \
						--screenshot only-on-failure \
						--video retain-on-failure \
						--output test-results -v $(PYTEST_ARGS); \
				TEST_EXIT=$$?; \
			fi; \
		fi; \
	fi; \
	exit "$$TEST_EXIT"

# --------------------------------------------------
# Full local Docker host-based developer workflow.
#
# This is the primary entry point for contributors.
# It prepares a complete local development environment:
#
#   • creates .env (if missing)
#   • starts the Docker infrastructure
#   • bootstraps WordPress + WooCommerce
#   • installs the Python framework
#   • runs pytest on the host against the Docker Compose services (API_ENV=test)
#
# Workflow steps:
#
#   make up (Starts Docker Compose infrastructure)
#   make setup (Provisions WordPress/WooCommerce, generates API credentials and seeds products and UI users)
#   make install (Installs the framework, development dependencies, Git hooks and Playwright browsers)
#   pytest with API_ENV=test and the running Compose database credentials
#
# Most contributors only need:
#
#   make run
# --------------------------------------------------
run:
	@set +e; \
		TEST_EXIT=0; \
		LOCK_ACQUIRED=0; \
		LOCK_DIR=.test-execution.lock; \
		LOCK_TOKEN="make-run-$$(date +%s)-$$$$"; \
		if ! mkdir "$$LOCK_DIR" 2>/dev/null; then \
			echo "[ERROR] Another test execution already owns the local environment lock."; \
			if [ -f "$$LOCK_DIR/owner.txt" ]; then cat "$$LOCK_DIR/owner.txt"; fi; \
			exit 2; \
		fi; \
		LOCK_ACQUIRED=1; \
		if ! printf 'token=%s\npid=%s\nmode=host-run\n' "$$LOCK_TOKEN" "$$$$" > "$$LOCK_DIR/owner.txt"; then \
			rm -f "$$LOCK_DIR/owner.txt"; rmdir "$$LOCK_DIR"; \
			echo "[ERROR] Could not write the local environment lock."; \
			exit 2; \
		fi; \
		cleanup() { \
			STATUS=$$?; \
			trap - 0 INT TERM; \
			if [ "$$LOCK_ACQUIRED" -eq 1 ] && grep -Fqx "token=$$LOCK_TOKEN" "$$LOCK_DIR/owner.txt" 2>/dev/null; then \
				rm -f "$$LOCK_DIR/owner.txt"; \
				rmdir "$$LOCK_DIR" || { if [ "$$TEST_EXIT" -eq 0 ]; then TEST_EXIT=2; fi; }; \
			fi; \
			if [ "$$TEST_EXIT" -ne 0 ]; then exit "$$TEST_EXIT"; fi; \
			exit "$$STATUS"; \
		}; \
		trap cleanup 0; \
		trap 'TEST_EXIT=130; exit 130' INT; \
		trap 'TEST_EXIT=143; exit 143' TERM; \
		TEST_EXECUTION_LOCK_HELD_BY_MAKE=1 $(MAKE) --no-print-directory ensure-env up setup install; \
		TEST_EXIT=$$?; \
		if [ "$$TEST_EXIT" -ne 0 ]; then exit "$$TEST_EXIT"; fi; \
		DB_CONTAINER="$$(docker compose -f docker-compose.wp.yml ps -q db)"; \
		if [ -z "$$DB_CONTAINER" ]; then \
			echo "[ERROR] Could not find the Compose db container for host-based pytest."; \
			TEST_EXIT=1; exit "$$TEST_EXIT"; \
		fi; \
		DB_ENVIRONMENT="$$(docker inspect -f '{{range .Config.Env}}{{println .}}{{end}}' "$$DB_CONTAINER")"; \
		RUN_DB_USER="$$(printf '%s\n' "$$DB_ENVIRONMENT" | sed -n 's/^MYSQL_USER=//p')"; \
		RUN_DB_PASSWORD="$$(printf '%s\n' "$$DB_ENVIRONMENT" | sed -n 's/^MYSQL_PASSWORD=//p')"; \
		RUN_DB_DATABASE="$$(printf '%s\n' "$$DB_ENVIRONMENT" | sed -n 's/^MYSQL_DATABASE=//p')"; \
		if [ -z "$$RUN_DB_USER" ] || [ -z "$$RUN_DB_PASSWORD" ] || [ -z "$$RUN_DB_DATABASE" ]; then \
			echo "[ERROR] Could not read application DB credentials from the Compose db container."; \
			TEST_EXIT=1; exit "$$TEST_EXIT"; \
		fi; \
		echo "[TEST] Running host-based pytest against Docker Compose (API_ENV=test)..."; \
		TEST_EXECUTION_LOCK_HELD_BY_MAKE=1 \
		API_ENV=test \
		DB_USER="$$RUN_DB_USER" \
		DB_PASSWORD="$$RUN_DB_PASSWORD" \
		DB_HOST=127.0.0.1 \
		DB_PORT=3306 \
		DB_DATABASE="$$RUN_DB_DATABASE" \
		DB_TABLE_PREFIX=wp_ \
		$(VENV_PYTHON) -m pytest -v; \
		TEST_EXIT=$$?; \
		exit "$$TEST_EXIT"

# --------------------------------------------------
# Stop infrastructure and remove everything Docker manages
# (named/anonymous volumes + orphaned containers).
#
# NOTE: this does NOT remove ./wp-data — see `clean` below.
# --------------------------------------------------
down: guard-test-lock
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
