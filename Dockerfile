# Stage 1: Build stage (dependency installation)
FROM python:3.11-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install system deps required for building wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc curl && \
    rm -rf /var/lib/apt/lists/*

# Copy project files needed for installation (include package resources)
COPY pyproject_root.toml README.md ./
COPY EcommerceAPI ./EcommerceAPI

RUN pip install --upgrade pip setuptools wheel


# Install project + test/dev dependencies (use 'dev' extra consistently)
RUN pip install -e './EcommerceAPI[dev]'

# -------------------------------------------------------------------
# Stage 2: Runtime
# -------------------------------------------------------------------
FROM python:3.11-slim

WORKDIR /app

# Copy installed dependencies from builder
COPY --from=builder /usr/local /usr/local

# Copy full project for runtime execution & tests mounting in compose
COPY EcommerceAPI ./EcommerceAPI
COPY tests ./tests
COPY pyproject_root.toml README.md ./

# ------------------------------------------------------------
# Default environment — CI will override these
# ------------------------------------------------------------
ENV ENVIRONMENT=test

# Logging & Reporting (default: safe for local)
ENV ENABLE_STRUCTURED_LOGS=false
ENV ENABLE_JSON_PRETTY=false
ENV KEEP_STRUCTURED_LOGS=3
ENV LOG_DIR=/app/EcommerceAPI/reports/logs
ENV REDACT_SENSITIVE_FIELDS=true
ENV LOG_PAYLOADS=false
ENV DISABLE_LOG_EMOJIS=true

# Performance test defaults
ENV PERF_ITERATIONS=5

# Optional: enforce presence of .env in local runs (set to true only if you want fails locally)
# In CI set REQUIRE_ENV=true to fail when .env is missing or required vars not present.
ENV REQUIRE_ENV=true

# Schema smoke test toggle
ENV FAIL_ON_EMPTY_LIST=false

# Auto-generate Allure HTML report after pytest run
ENV AUTO_ALLURE_REPORT=true

# Optional: run only a specific microservice’s tests
ARG SERVICE=""
ENV SERVICE=$SERVICE

# API entity discovery during a pytest collection
ENV STRICT_ENTITY_DISCOVERY=true


# ------------------------------------------------------------
# Default CMD:
# - write Allure results to reports/<service>/allure-results or reports/allure-results
# - if AUTO_ALLURE_REPORT is true and `allure` is available, generate HTML
# Note: Allure CLI is not installed in this image to keep the image small.
# CI installs Allure at job runtime (recommended).
# ------------------------------------------------------------
CMD ["sh", "-lc", "if [ -n \"$SERVICE\" ]; then RESULTS_DIR=reports/$SERVICE/allure-results; mkdir -p \"$RESULTS_DIR\"; pytest tests/$SERVICE -s --disable-warnings --maxfail=3 --alluredir=\"$RESULTS_DIR\"; else RESULTS_DIR=reports/allure-results; mkdir -p \"$RESULTS_DIR\"; pytest tests -s --disable-warnings --maxfail=3 --alluredir=\"$RESULTS_DIR\"; fi; if [ \"$AUTO_ALLURE_REPORT\" = \"true\" ] || [ \"$AUTO_ALLURE_REPORT\" = \"1\" ]; then if command -v allure >/dev/null 2>&1; then if [ -d \"$RESULTS_DIR\" ] && [ \"$(ls -A \"$RESULTS_DIR\")\" ]; then REPORT_DIR=$(dirname \"$RESULTS_DIR\")/allure-report; allure generate \"$RESULTS_DIR\" -o \"$REPORT_DIR\" --clean || true; else echo 'No Allure results found; skipping HTML generation.'; fi; else echo 'Allure CLI not found in image; skipping HTML generation.'; fi; fi"]


#Quick run checklist & verification:
#Add the new docker-compose.matrix.yml to repo root (replace your current one if you like).
#Add the .dockerignore file to repo root (if not present).
#Build and run a single profile locally:
#    docker compose -f docker-compose.matrix.yml build
#    docker compose -f docker-compose.matrix.yml --profile customers up --abort-on-container-exit --remove-orphans
#Confirm results appear under ./reports/customers/* on host.
