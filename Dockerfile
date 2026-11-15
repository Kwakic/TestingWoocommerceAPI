# =============================================================================
# Dockerfile it is a plain text blueprint used to build an image (is a set of instructions for building a Docker image).

# Builts Python test runner image
# The image contains the environment needed to execute the framework.
# It is used to package the test code and its dependencies into a consistent environment
# Defines optional containerized test runner

# Purpose:
#   - Build a reusable pytest runner image for GitLab CI
#   - Installs the EcommerceAPI framework in editable mode
#   - Uses pytest.ini from repo root
#   - Does NOT run WordPress (CI entities do that)
#   - This image is only for running pytest, not WordPress.

 # - It locks down your exact Python version, operating system libraries, and pytest
 #   packages. This prevents the "it works on my machine" problem across different computers.
 # - Your CI server only needs Docker installed to build and run the test image. You do
 #   not have to manually configure Python environments on every build agent.
 # - Running tests inside a container keeps dependencies separate from other projects on your host machine.

# The Dockerfile builds an image containing the test execution environment:
#   - Python 3.13
#   - Your EcommerceAPI framework
#   - Python dependencies
#   - Pytest and testing dependencies
#   - The files needed to execute the test

# You only need a Dockerfile if:
#   - you want to run tests inside a container
#   - or build a custom test image

# NOTE:
# - The current CI pipeline does not need the custom Dockerfile. It runs pytest directly on the
#   GitHub-hosted Ubuntu runner.
# - make run command does not need your custom Dockerfile at all neither

# =============================================================================

# -------------------------------------------------------------------
# Stage 1: Build dependencies & install framework
# -------------------------------------------------------------------
FROM python:3.13-slim AS builder

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
RUN python -m pip install -e './EcommerceAPI[dev]'

# -------------------------------------------------------------------
# Stage 2: Runtime image
# -------------------------------------------------------------------
FROM python:3.13-slim

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
#ENV KEEP_STRUCTURED_RUNS=1
#ENV REDACT_SENSITIVE_FIELDS=true
#ENV LOG_PAYLOADS=false
#ENV DISABLE_LOG_EMOJIS=true
#ENV PLAYWRIGHT_TRACE_ARTIFACT_ENABLED=false
## Performance test defaults
#ENV PERF_ITERATIONS=5
#ENV REQUIRE_ENV=false


# Default command (CI overrides args)
CMD ["pytest", "-s"]
