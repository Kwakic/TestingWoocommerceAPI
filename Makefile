# Makefile = orchestrates project execution
# It controls:
# - docker
# - setup
# - python environment
# - tests

.PHONY: up setup install test test-ci run down

# --------------------------------------------------
# Start infrastructure
# --------------------------------------------------
up:
	docker compose -f docker-compose.wp.yml up -d

# --------------------------------------------------
# Bootstrap WordPress + WooCommerce
# --------------------------------------------------
setup:
	bash scripts/setup.sh

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
# Full execution (what users run)
# --------------------------------------------------
run: up setup install test

# --------------------------------------------------
# Stop infrastructure
# --------------------------------------------------
down:
	docker compose -f docker-compose.wp.yml down
