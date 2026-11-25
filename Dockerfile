# =============================================================================
# Dockerfile it is a plain text/instructions blueprint used to build an image.

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

# Keep the browser cache inside the image so the runtime uses the exact
# browser revisions required by the Playwright package installed above.
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Install the browsers exercised by the UI workflow. --with-deps installs
# their required Linux libraries in this runtime image as well as the browser
# binaries; using the installed Playwright CLI keeps browser revisions aligned.
# Playwright's bundled Node runtime needs libatomic on this slim base before
# the CLI can install the remaining browser dependencies.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libatomic1 \
    && rm -rf /var/lib/apt/lists/* \
    && python -m playwright install --with-deps chromium firefox webkit \
    && rm -rf /var/lib/apt/lists/*

# Global pytest configuration (CRITICAL)
COPY pytest.ini ./pytest.ini
COPY conftest.py ./conftest.py

# Copy framework + tests
COPY EcommerceAPI ./EcommerceAPI
COPY tests ./tests
# Shared unit tests exercise the credential writer and manual CI selection.
COPY scripts/write_env_credentials.sh ./scripts/write_env_credentials.sh
COPY .github/scripts/generate_matrix.py ./.github/scripts/generate_matrix.py
COPY .github/scripts/generate_codeowners.py ./.github/scripts/generate_codeowners.py
COPY .github/CODEOWNERS ./.github/CODEOWNERS
COPY .github/workflows/manual-entity-tests.yml ./.github/workflows/manual-entity-tests.yml

# The image fallback is used only when the caller does not set API_ENV.
# `make test-docker` explicitly sets API_ENV=docker.
ENV ENV=docker

# Default command (the Makefile supplies the supported Docker test settings).
CMD ["pytest", "-s"]
