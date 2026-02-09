# =============================================================================
# Dockerfile
# Python test runner image

# Purpose:
#   - Build a reusable pytest runner image for GitLab CI
#   - Installs the EcommerceAPI framework in editable mode
#   - Uses pytest.ini from repo root
#   - Does NOT run WordPress (CI services do that)
#   - This image is only for running pytest, not WordPress.
# =============================================================================

# -------------------------------------------------------------------
# Stage 1: Build dependencies & install framework
# -------------------------------------------------------------------
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# System deps required for wheels (psycopg2, mysqlclient, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc curl \
    && rm -rf /var/lib/apt/lists/*

# Copy ONLY the installable framework
COPY EcommerceAPI ./EcommerceAPI

# Upgrade tooling
RUN pip install --upgrade pip setuptools wheel

# Install framework + dev dependencies
RUN pip install -e './EcommerceAPI[dev]'

# -------------------------------------------------------------------
# Stage 2: Runtime image
# -------------------------------------------------------------------
FROM python:3.11-slim

WORKDIR /app

# Copy installed site-packages
COPY --from=builder /usr/local /usr/local

# Global pytest configuration (CRITICAL)
COPY pytest.ini ./pytest.ini
COPY conftest.py ./conftest.py

# Copy framework + tests
COPY EcommerceAPI ./EcommerceAPI
COPY tests ./tests

# ------------------------------------------------------------
# Default runtime environment (CI overrides)
# ------------------------------------------------------------
ENV ENV=docker
ENV LOG_DIR=/app/reports/logs
ENV AUTO_ALLURE_REPORT=true
ENV FAIL_ON_EMPTY_LIST=false
ENV STRICT_ENTITY_DISCOVERY=true

#ENV ENVIRONMENT=test
#ENV API_ENV=docker
## Logging & Reporting
#ENV ENABLE_STRUCTURED_LOGS=true
#ENV ENABLE_JSON_PRETTY=false
#ENV KEEP_STRUCTURED_LOGS=3
#ENV REDACT_SENSITIVE_FIELDS=true
#ENV LOG_PAYLOADS=false
#ENV DISABLE_LOG_EMOJIS=true
## Performance test defaults
#ENV PERF_ITERATIONS=5
#ENV REQUIRE_ENV=false


# Default command (CI overrides args)
CMD ["pytest", "-s"]
