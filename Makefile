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
#                                     WooCommerce, API credentials). It
#                                     never touches .env — it just prints
#                                     fresh credentials to stdout.
#   scripts/write_env_credentials.sh -> the ONLY thing that writes
#                                     generated API credentials into .env
#   Python                        -> consumes .env, never creates it

.PHONY: up setup install test test-ci run down clean ensure-env venv

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
				MAJ=$${VER%%.*}; MIN=$${VER##*.}; \
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
						MAJ=$${VER%%.*}; MIN=$${VER##*.}; \
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
	MAJ=$${VER%%.*}; MIN=$${VER##*.}; \
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
up: ensure-env
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
setup: ensure-env
	@echo "[SETUP] Bootstrapping WooCommerce..."
	@bash scripts/setup.sh | bash scripts/write_env_credentials.sh

# --------------------------------------------------
# Install Python framework (editable mode)
# --------------------------------------------------
install: venv
	@echo "[INSTALL] Installing EcommerceAPI framework..."
	$(VENV_PYTHON) -m pip install --upgrade pip
	$(VENV_PYTHON) -m pip install -e "./EcommerceAPI[dev]"

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
