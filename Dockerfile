# Stage 1: Build stage (dependency installation)
FROM python:3.11-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install system deps required for building wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc curl && \
    rm -rf /var/lib/apt/lists/*

# Copy only the EcommerceAPI package (it contains pyproject.toml internally)
COPY EcommerceAPI ./EcommerceAPI

# Copy README.md ONLY if it exists at root (optional)
# If README.md is inside EcommerceAPI/, remove this line
COPY README.md ./README.md

RUN pip install --upgrade pip setuptools wheel

# Install project + dev dependencies
RUN pip install -e './EcommerceAPI[dev]'

# -------------------------------------------------------------------
# Stage 2: Runtime
# -------------------------------------------------------------------
FROM python:3.11-slim

WORKDIR /app

# Copy installed dependencies from builder
COPY --from=builder /usr/local /usr/local

# Copy framework and tests
COPY EcommerceAPI ./EcommerceAPI
COPY tests ./tests

# Copy README.md ONLY if needed at runtime (optional)
COPY README.md ./README.md

# ------------------------------------------------------------
# Default environment (CI will override these)
# ------------------------------------------------------------
ENV ENVIRONMENT=test
ENV API_ENV=docker

# Logging & Reporting
ENV ENABLE_STRUCTURED_LOGS=true
ENV ENABLE_JSON_PRETTY=false
ENV KEEP_STRUCTURED_LOGS=3
ENV LOG_DIR=/app/reports/logs
ENV REDACT_SENSITIVE_FIELDS=true
ENV LOG_PAYLOADS=false
ENV DISABLE_LOG_EMOJIS=true

# Performance test defaults
ENV PERF_ITERATIONS=5
ENV REQUIRE_ENV=false
ENV FAIL_ON_EMPTY_LIST=false
ENV AUTO_ALLURE_REPORT=true
ENV STRICT_ENTITY_DISCOVERY=true