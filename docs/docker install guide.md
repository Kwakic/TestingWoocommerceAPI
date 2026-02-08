🐳 Complete Docker Setup Guide for WooCommerce API Testing

A comprehensive guide to running WooCommerce tests in Docker containers
📋 Table of Contents

    Introduction
    Why Docker for Testing?
    Architecture Overview
    Prerequisites
    Project Structure
    Configuration Files Explained
    Step-by-Step Setup
    Running Tests
    Common Issues & Troubleshooting
    CI/CD Integration
    Quick Reference

🎯 Introduction

This guide teaches you how to run a complete WooCommerce API test suite using Docker. Instead of testing against 
production or requiring a local XAMPP/MAMP setup, everything runs in isolated Docker containers on the same network.
What You'll Build


    ✅ WordPress + WooCommerce running in Docker
    ✅ MySQL database in Docker
    ✅ Pytest test runner in Docker
    ✅ All containers communicating on a private network
    ✅ Automated test reports (Allure)
    ✅ CI/CD ready configuration

🤔 Why Docker for Testing?
The Problem Without Docker

Traditional setup:
Code

Your laptop (host)
├── XAMPP/MAMP (WordPress on localhost:8888)
├── Python virtual environment
└── Tests run on host, hit localhost:8888

Issues:

    ❌ Different environments on dev/CI/staging
    ❌ "Works on my machine" syndrome
    ❌ Manual setup required on every machine
    ❌ Can't run multiple test suites in parallel
    ❌ Hard to replicate production environment

The Solution: Full Docker Environment

Docker architecture:
Code

┌─────────────────────────────────────────────────┐
│          Docker Network: wc-net                 │
│                                                 │
│  ┌──────────────┐     ┌──────────────┐        │
│  │   pytest     │────▶│  WordPress   │        │
│  │  container   │     │      +       │        │
│  │              │     │ WooCommerce  │        │
│  └──────────────┘     └──────┬───────┘        │
│                              │                 │
│                       ┌──────▼───────┐        │
│                       │    MySQL     │        │
│                       │   Database   │        │
│                       └──────────────┘        │
└─────────────────────────────────────────────────┘

Benefits:

    ✅ Consistent: Same environment everywhere (dev, CI, production)
    ✅ Isolated: Tests don't interfere with your local system
    ✅ Portable: Works on Windows, Mac, Linux
    ✅ Reproducible: Docker images guarantee exact dependencies
    ✅ Scalable: Run multiple test suites in parallel
    ✅ Service Discovery: Containers talk via hostnames (no localhost hacks)

🏗️ Architecture Overview
Network Architecture
Code

Host Machine (your laptop)
    │
    │ Port 8888:80 (optional - browser access)
    │
    ▼
┌───────────────────────────────────────────────────┐
│  Docker Network: testecommerceapi_wc-net          │
│  (bridge network - internal DNS)                  │
│                                                   │
│  ┌─────────────────────────────────────────┐    │
│  │  wordpress (service name = hostname)     │    │
│  │  - Internal: http://wordpress:80         │    │
│  │  - External: http://localhost:8888       │    │
│  │  - WooCommerce REST API endpoint         │    │
│  └─────────────────┬───────────────────────┘    │
│                    │                             │
│                    │ WORDPRESS_DB_HOST=db        │
│                    ▼                             │
│  ┌─────────────────────────────────��───────┐    │
│  │  db (MySQL service)                      │    │
│  │  - Internal: mysql://db:3306             │    │
│  │  - No external port (security)           │    │
│  └─────────────────────────────────────────┘    │
│                    ▲                             │
│                    │                             │
│  ┌─────────────────┴───────────────────────┐    │
│  │  customers (pytest test container)       │    │
│  │  - API_ENV=docker                        │    │
│  │  - URL: http://wordpress/wp-json/wc/v3/  │    │
│  │  - Reads: /app/tests (mounted)           │    │
│  │  - Writes: /app/reports (mounted)        │    │
│  └─────────────────────────────────────────┘    │
│                                                   │
│  ┌─────────────────────────────────────────┐    │
│  │  orders (pytest test container)          │    │
│  │  - Same config as customers              │    │
│  │  - Runs different test suite             │    │
│  └─────────────────────────────────────────┘    │
└───────────────────────────────────────────────────┘

Key Concepts
1. Service Names = Hostnames

In Docker Compose, service names automatically become DNS hostnames:
YAML

    services:
      wordpress:  # ← This becomes hostname "wordpress"
        image: wordpress:6.4-php8.2-apache`

Inside containers on the same network:

    ✅ http://wordpress → resolves to WordPress container IP
    ✅ http://db → resolves to MySQL container IP
    ❌ http://localhost:8888 → DOES NOT WORK (localhost = the container itself)

2. Port Mapping vs Internal Ports
YAML

        wordpress:
          ports:
            - "8888:80"  # Host:Container

    Left side (8888): Port on your host machine (for browser access)
    Right side (80): Port inside the container
    Other containers: Don't use localhost:8888, they use http://wordpress:80 (or just http://wordpress)

3. Volumes for Persistence & Communication
YAML

        volumes:
          - ./tests:/app/tests:ro      # Mount host folder into container (read-only)
            - ./reports:/app/reports     # Bidirectional: container writes, host reads`

Why:

 - Tests stay on host (easy to edit)
 - Results written by container appear on host
 - No need to rebuild image when tests change

✅ Prerequisites
Required Software

    bash
    
    # Check versions
    docker --version        # Docker 20.10+ recommended
    docker compose version  # Docker Compose v2.0+ (plugin version)
    git --version

Windows Users (Git Bash)

- Use Git Bash terminal (not CMD or PowerShell)
- Enable WSL2 backend for Docker Desktop
  - Ensure line endings are set to LF:

          bash
             git config --global core.autocrlf input

📂 Project Structure

Your repository should look like this:
Code

TestEcommerceAPI/
├── .dockerignore                    # Files to exclude from Docker build
├── .env                             # API credentials (NOT in git)
├── .gitignore                       # Git ignore rules
├── Dockerfile                       # Test container image definition
├── docker-compose.wp.yml            # WordPress + MySQL infrastructure
├── docker-compose.matrix.yml        # Test runner services
├── .gitlab-ci.yml                   # CI/CD pipeline (optional)
│
├── EcommerceAPI/                    # Your test framework package
│   ├── pyproject.toml               # Python package definition
│   ├── config_customers.py          # Environment configs
│   └── ...                          # Framework code
│
├── tests/                           # Test suites (mounted into containers)
│   ├── customers/                   # Customer API tests
│   │   ├── test_create_customer.py
│   │   └── test_list_customers.py
│   ├── orders/                      # Order API tests
│   └── shared/                      # Common utilities
│
└── reports/                         # Test results (generated by container)
    ├── customers/
    │   └── allure-results/
    ├── orders/
    │   └── allure-results/
    └── logs/

📝 Configuration Files Explained
1. .dockerignore

Purpose: Tells Docker which files to exclude from the build context (makes builds faster and images smaller).
dockerignore

# ==============================
# Python bytecode
# ==============================
__pycache__/
*.pyc
*.pyo
*.pyd

# ==============================
# Virtual environments
# ==============================
.venv/
venv/
ENV/

# ==============================
# Test / coverage / build artifacts
# ==============================
.pytest_cache/
htmlcov/
dist/
build/
*.egg-info/

# ==============================
# Reports (generated at runtime)
# ==============================
reports/

# ==============================
# Git / IDE
# ==============================
.git/
.gitignore
.vscode/
.idea/

# ==============================
# Environment secrets
# ==============================
.env
.env.*

# ==============================
# OS junk
# ==============================
.DS_Store
Thumbs.db

Why each section:

- Bytecode: Python regenerates this, no need in image
- Virtual envs: Docker installs dependencies fresh
- Reports: Generated at runtime, not part of the image
- Git/IDE: Not needed in container
- .env: Contains secrets, should NEVER be in image
- OS junk: System files not relevant to container

2. Dockerfile

Purpose: Defines how to build the pytest test runner image.
Dockerfile

# ============================================================
# Stage 1: Build stage (dependency installation)
# ============================================================
# Why multi-stage? Keeps final image small by leaving build tools behind.

FROM python:3.11-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1    # Don't create .pyc files
ENV PYTHONUNBUFFERED=1            # Print logs immediately (don't buffer)
WORKDIR /app

# Install system dependencies needed to compile Python packages
# (gcc, build-essential for wheels like cryptography, lxml)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc curl && \
    rm -rf /var/lib/apt/lists/*   # Clean up to reduce layer size

# Copy only framework package (contains pyproject.toml)
COPY EcommerceAPI ./EcommerceAPI

# Copy README if it exists (some packages require it)
COPY README.md ./README.md

# Upgrade pip/setuptools/wheel to latest versions
RUN pip install --upgrade pip setuptools wheel

# Install framework + dev dependencies (pytest, allure, etc.)
# This installs into /usr/local (system Python)
RUN pip install -e './EcommerceAPI[dev]'

# ============================================================
# Stage 2: Runtime image
# ============================================================
# Why separate stage? Final image doesn't need gcc/build-essential.

FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder (includes pytest, requests, etc.)
COPY --from=builder /usr/local /usr/local

# Copy framework and tests into the image
# (Tests can also be mounted at runtime via volumes)
COPY EcommerceAPI ./EcommerceAPI
COPY tests ./tests
COPY README.md ./README.md

# ============================================================
# Environment Variables (defaults for all test runs)
# ============================================================
# These can be overridden by docker-compose.matrix.yml

ENV ENVIRONMENT=test
ENV API_ENV=docker                    # Tells config to use docker URLs

# Logging configuration
ENV ENABLE_STRUCTURED_LOGS=true       # JSON logs for parsing
ENV ENABLE_JSON_PRETTY=false          # Compact JSON (not pretty-printed)
ENV KEEP_STRUCTURED_LOGS=3            # Keep last 3 log files
ENV LOG_DIR=/app/reports/logs         # Where logs are written
ENV REDACT_SENSITIVE_FIELDS=true      # Hide passwords in logs
ENV LOG_PAYLOADS=false                # Don't log request/response bodies
ENV DISABLE_LOG_EMOJIS=true           # CI-friendly logs (no emojis)

# Test behavior
ENV PERF_ITERATIONS=5                 # How many times to run perf tests
ENV REQUIRE_ENV=false                 # Don't fail if .env missing (use env vars)
ENV FAIL_ON_EMPTY_LIST=false          # Allow empty API responses in tests
ENV AUTO_ALLURE_REPORT=true           # Generate HTML report after tests
ENV STRICT_ENTITY_DISCOVERY=true      # Fail if API entities not found

# No CMD here — docker-compose.matrix.yml controls execution

Key Concepts:
Concept	            Explanation
Multi-stage build -	First stage compiles dependencies, second stage copies only runtime files. Result: smaller image.
ENV variables     -	Set defaults that can be overridden at runtime. Think of them as configuration.
WORKDIR /app      - Sets the "current directory" inside the container. All paths are relative to this.
COPY vs volumes   - COPY bakes files into the image. Volumes mount files at runtime (allows changes without rebuild).

3.docker-compose.wp.yml

Purpose: Defines WordPress + MySQL infrastructure. This is your "test environment backend."
YAML

version: "3.9"

services:
  # ============================================================
  # MySQL Database
  # ============================================================
  # Why separate database? WordPress needs persistent storage
  # for posts, users, WooCommerce products, etc.
  
  db:
    image: mysql:8.0                  # Official MySQL image
    container_name: wc-db             # Fixed name (easier to reference)
    
    environment:
      # Database credentials (WordPress will use these)
      MYSQL_DATABASE: wordpress
      MYSQL_USER: wp
      MYSQL_PASSWORD: wp
      MYSQL_ROOT_PASSWORD: root
    
    volumes:
      # Persist database data on host (survives container restart)
      - db_data:/var/lib/mysql
    
    networks:
      - wc-net                        # Connect to shared network
    
    healthcheck:
      # Ensure MySQL is ready before WordPress starts
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 5s                    # Check every 5 seconds
      retries: 10                     # Try 10 times before failing

  # ============================================================
  # WordPress + WooCommerce
  # ============================================================
  
  wordpress:
    image: wordpress:6.4-php8.2-apache
    container_name: wc-wp
    
    depends_on:
      db:
        condition: service_healthy    # Wait for MySQL to be ready
    
    environment:
      # Tell WordPress how to connect to database
      WORDPRESS_DB_HOST: db           # Hostname = service name!
      WORDPRESS_DB_NAME: wordpress
      WORDPRESS_DB_USER: wp
      WORDPRESS_DB_PASSWORD: wp
    
    ports:
      # Map host port 8888 to container port 80
      # This is ONLY for browser access from your laptop
      # Other containers use http://wordpress (no port needed)
      - "8888:80"
    
    volumes:
      # Persist WordPress files (themes, plugins, uploads)
      - wp_data:/var/www/html
    
    networks:
      - wc-net

# ============================================================
# Named Volumes (persistent storage)
# ============================================================
# Why volumes? Data survives even if containers are deleted.

volumes:
  db_data:    # MySQL data files
  wp_data:    # WordPress installation files

# ============================================================
# Network Definition
# ============================================================
# Why custom network? Allows containers to find each other by name.

networks:
  wc-net:
    driver: bridge

Why This File:
Reason                 	Explanation
Separation of concerns	- Infrastructure (WordPress/MySQL) is separate from test execution (pytest containers).
Long-running services	- WordPress stays running while you run multiple test suites.
Manual control	        -  You start WordPress once (docker compose -f docker-compose.wp.yml up -d), then run tests many times.

4.docker-compose.matrix.yml

Purpose: Defines pytest test runner containers. One service per microservice/test suite.
YAML

version: "3.9"

# ============================================================
# Reusable Template (YAML Anchor)
# ============================================================
# Why template? Avoid repeating the same config for every service.

x-test-template: &test-template
  build:
    context: .                        # Build from current directory
    dockerfile: Dockerfile            # Use our custom Dockerfile
  
  image: ecommerceapi-tests:latest    # Tag the built image
  
  environment:
    # Override Dockerfile defaults
    API_ENV: docker                   # Use docker URLs (http://wordpress)
    ENABLE_STRUCTURED_LOGS: "true"
    AUTO_ALLURE_REPORT: "true"
    LOG_DIR: "/app/reports/logs"
    ENABLE_JSON_PRETTY: "false"
    KEEP_STRUCTURED_LOGS: "3"
    
    # Pass secrets from host environment
    WC_KEY: "${WC_KEY}"               # Reads from .env or export
    WC_SECRET: "${WC_SECRET}"
  
  volumes:
    # Mount tests read-only (container can't modify your test files)
    - ./tests:/app/tests:ro
    
    # Mount reports read-write (container writes results to host)
    - ./reports:/app/reports
  
  networks:
    - wc-net                          # Join WordPress network

# ============================================================
# Test Services (one per test suite)
# ============================================================

services:
  # Customer API tests
  customers:
    <<: *test-template                # Inherit from template
    profiles: ["customers"]           # Only run when --profile customers
    
    command:
      # pytest arguments (entry point is already pytest from Python image)
      - tests/customers               # Test directory
      - -s                            # Show print statements
      - --disable-warnings            # Hide deprecation warnings
      - --maxfail=3                   # Stop after 3 failures
      - --alluredir=reports/customers/allure-results  # Output directory

  # Order API tests
  orders:
    <<: *test-template
    profiles: ["orders"]
    command:
      - tests/orders
      - -s
      - --disable-warnings
      - --maxfail=3
      - --alluredir=reports/orders/allure-results

# ============================================================
# Network (connects to existing WordPress network)
# ============================================================

networks:
  wc-net:
    external: true                    # Network already exists (created by wp.yml)

Key Concepts:
Concept	                           Why It Matters
Profiles	                       - Lets you choose which services to run: --profile customers runs only customer tests.
YAML anchors (& and <<:)	       - Define config once, reuse many times. Keeps file DRY.
external: true	                   - Network was created by docker-compose.wp.yml, we just join it.
Read-only mounts	               - Tests are mounted :ro so container can't accidentally modify your code.
Environment variable interpolation - ${WC_KEY} reads from .env file or shell export.

5.config_customers.py

Purpose: Environment-specific API endpoint URLs for the customers service.
Python

"""
config_customers.py

Environment-specific host mappings for the CUSTOMERS microservice.

Why this file?
- Different environments have different URLs
- API_ENV environment variable selects which URL to use
- Keeps secrets out of code (credentials loaded separately)
"""

API_HOSTS = {
    # Local development (tests run on host, WordPress in Docker)
    "test": "http://localhost:8888/kwakiweb/wp-json/wc/v3/",
    
    # Docker environment (tests run IN Docker, same network as WordPress)
    # ⚠️ CRITICAL: Use service name "wordpress", NOT "localhost"
    "docker": "http://wordpress/wp-json/wc/v3/",
    
    # Local without Docker
    "local": "http://localhost:8888/wp-json/wc/v3/",
    
    # Development server
    "dev": "http://localhost:8888/kwakiweb/wp-json/wc/v3/",
    
    # Staging environment (real server)
    "staging": "https://staging.example.com/wp-json/wc/v3/",
    
    # Production (real server)
    "prod": "https://api.example.com/wp-json/wc/v3/",
}

How It Works:

- Dockerfile sets ENV API_ENV=docker
- Your framework reads this config file
- Selects URL based on API_ENV
- All API calls go to http://wordpress/wp-json/wc/v3/

🚀 Step-by-Step Setup
Step 1: Start WordPress + MySQL

Command:

        bash

        docker compose -f docker-compose.wp.yml up -d

What happens:
Code

[+] Running 5/5
 ✔ Network testecommerceapi_wc-net   Created    0.1s
 ✔ Volume testecommerceapi_db_data   Created    0.0s
 ✔ Volume testecommerceapi_wp_data   Created    0.0s
 ✔ Container wc-db                   Healthy    12.2s  ← MySQL ready
 ✔ Container wc-wp                   Started    12.5s  ← WordPress running

Why -d (detached mode)?

    Containers run in background
    Terminal is free for other commands
    Logs don't spam your screen

Verify it worked:

    bash
    
    docker ps

Expected output:
Code

CONTAINER ID   IMAGE                         STATUS                 PORTS                    NAMES
1532bb7c386d   wordpress:6.4-php8.2-apache   Up 2 minutes           0.0.0.0:8888->80/tcp    wc-wp
80888d039eb1   mysql:8.0                     Up 2 minutes (healthy) 3306/tcp                wc-db

Step 2: Check Network Exists

Command:

    bash
    
    docker network ls | grep wc

Expected output:
Code

    f0a3e47c2493   testecommerceapi_wc-net   bridge   local

Why this matters:

- Network name has your project directory prefix (testecommerceapi_)
- This is the network pytest containers will join
- If name differs, update docker-compose.matrix.yml

Step 3: Configure WordPress
3a. Access WordPress Admin

Open browser:

    Code
    
    http://localhost:8888/wp-admin

3b. Complete Initial Setup

If first time running:

   1. Select language → Click Continue
   2. Site information:
        Title: Test WooCommerce
        Username: admin
        Password: admin123 (or use strong password)
        Email: your email
   3. Click Install WordPress
   4. Log in with credentials

3c. Install WooCommerce Plugin

Option A: Via Admin UI

   1.  Go to Plugins → Add New
   2. Search "WooCommerce"
   3. Click Install Now → Activate
   4. Skip setup wizard (click "Skip this step" at bottom)

Option B: Via Command Line (Faster)
bash

    # Install and activate WooCommerce
    docker exec wc-wp wp plugin install woocommerce --activate --allow-root
    
    # Skip onboarding wizard
    docker exec wc-wp wp option update woocommerce_onboarding_profile '{"skipped":true}' --format=json --allow-root

Why WP-CLI method is better:

  - Faster (no clicking through wizard)
  - Scriptable (can add to setup script)
  - CI-friendly (no manual steps)

Step 4: Generate API Credentials
4a. Navigate to REST API Settings

Direct URL:

    Code
    
    http://localhost:8888/wp-admin/admin.php?page=wc-settings&tab=advanced&section=keys

Or manually:

    WooCommerce → Settings → Advanced → REST API

4b. Create API Key

   1. Click Add Key button
   2. Fill form:
        Description: Docker Tests
        User: Select admin
        Permissions: Read/Write
   3. Click Generate API Key

4c. Copy Credentials

You'll see:
    
    Code
    
    Consumer key:     ck_abc123...
    Consumer secret:  cs_xyz789...

⚠️ CRITICAL: Copy these NOW! You can't see the secret again.
Step 5: Save Credentials

Create .env file in project root:

    bash
    
    cd ~/TestEcommerceAPI
    nano .env  # or use your favorite editor

File contents:

    bash
    
    WC_KEY=ck_YOUR_ACTUAL_KEY_HERE
    WC_SECRET=cs_YOUR_ACTUAL_SECRET_HERE

Verify:

    bash
    
    cat .env

Set permissions (recommended):

    bash
    
    chmod 600 .env  # Only you can read/write

Why .env file?

    -Keeps secrets out of code
    -Docker Compose automatically reads it
    -Easy to change without modifying config files
    .gitignore should exclude it (never commit!)

Step 6: Build Test Image

Command:

    bash
    
    docker compose -f docker-compose.matrix.yml --profile customers build

Why` --profile customers?`

   - Without it, Docker sees 0 services to build (all have profiles)
   - Profile "activates" the service for this command
   - You can use --profile customers --profile orders to build both

What happens:

Code

    [+] Building 45.2s (12/12) FINISHED
     => [internal] load build definition from Dockerfile
     => [internal] load .dockerignore
     => [builder 1/6] FROM python:3.11-slim
     => [builder 2/6] WORKDIR /app
     => [builder 3/6] RUN apt-get update && apt-get install...
     => [builder 4/6] COPY EcommerceAPI ./EcommerceAPI
     => [builder 5/6] RUN pip install --upgrade pip...
     => [builder 6/6] RUN pip install -e './EcommerceAPI[dev]'
     => [stage-1 1/4] WORKDIR /app
     => [stage-1 2/4] COPY --from=builder /usr/local /usr/local
     => [stage-1 3/4] COPY EcommerceAPI ./EcommerceAPI
     => [stage-1 4/4] COPY tests ./tests
     => exporting to image
     => => naming to docker.io/library/ecommerceapi-tests:latest

Build layers explained:
Layer               	    Purpose
FROM python:3.11-slim  -	Base image (Debian + Python)
RUN apt-get install... -    Install system tools (gcc, curl)
COPY EcommerceAPI	   -    Copy framework code into image
RUN pip install -e     -    Install Python dependencies
COPY tests	           -    Copy test files into image

Verify image exists:

    bash
    
    docker images | grep ecommerceapi

Expected:

Code

    ecommerceapi-tests   latest   abc123def456   2 minutes ago   450MB

Step 7: Run Tests

Command:
bash


    docker compose -f docker-compose.matrix.yml \
      --profile customers \
      up --abort-on-container-exit --remove-orphans

Flags explained:
Flag	                   What It Does
--profile customers	      - Run only the "customers" service
up	                      - Start containers
--abort-on-container-exit -	Stop all containers when tests finish
--remove-orphans	      .- Clean up containers from previous runs

Expected output:

Code

    [+] Running 1/1
     ✔ Container testecommerceapi-customers-1  Created    0.1s
    Attaching to customers-1
    customers-1  | ============================= test session starts ==============================
    customers-1  | platform linux -- Python 3.11.x, pytest-8.x.x
    customers-1  | rootdir: /app
    customers-1  | plugins: allure-pytest-2.x.x
    customers-1  | collected 15 items
    customers-1  |
    customers-1  | tests/customers/test_create_customer.py .                              [  6%]
    customers-1  | tests/customers/test_list_customers.py .                               [ 13%]
    customers-1  | tests/customers/test_update_customer.py .                              [ 20%]
    customers-1  | ...
    customers-1  |
    customers-1  | ======================== 15 passed in 12.34s ===============================
    customers-1 exited with code 0

Exit codes:
Code	Meaning
0   -	All tests passed ✅
1   -	Some tests failed ❌
2	-   pytest error (syntax, import, etc.)

Step 8: Check Results

List report files:

    bash
    
    ls -R reports/

Expected structure:

Code

    reports/
    ├── customers/
    │   └── allure-results/
    │       ├── 12345-test-result.json
    │       ├── 67890-test-result.json
    │       └── ...
    └── logs/
        └── test_2026-02-06_20-30-45.log

View Allure report (if Allure CLI installed):

    bash

    allure serve reports/customers/allure-results

This opens a browser with interactive test results.


🐛 Common Issues & Troubleshooting
Issue 1: "No services to build"

Error:
Code

    time="..." level=warning msg="No services to build"

Cause: Services use profiles, but you didn't specify one.

Fix:
    bash
    
    docker compose -f docker-compose.matrix.yml --profile customers build

Issue 2: "Network wc-net declared as external, but could not be found"

Error:
Code

    ERROR: Network wc-net declared as external, but could not be found

Cause: Network name has project prefix, but compose file expects exact name.

Check actual network name:

    bash
    
    docker network ls | grep wc

Output:
Code

    testecommerceapi_wc-net   ← Actual name

Fix in docker-compose.matrix.yml:
YAML

    networks:
      wc-net:
        name: testecommerceapi_wc-net  # Use actual name
        external: true

Issue 3: "depends_on service wordpress: invalid compose project"

Error:
Code

    service "customers" depends on undefined service "wordpress": invalid compose project

Cause: depends_on: wordpress references a service in a different compose file.

Fix: Remove depends_on from docker-compose.matrix.yml:
YAML

    x-test-template: &test-template
      build: ...
      networks:
        - wc-net
      # ❌ Remove this:
      # depends_on:
      #   - wordpress

Why it's safe: Tests connect via network, don't need formal dependency.

Issue 4: "/pyproject_root.toml: not found"

Error:
Code

    failed to calculate checksum: "/pyproject_root.toml": not found

Cause: Dockerfile tries to copy a file that doesn't exist at repo root.

Fix: Update Dockerfile to copy only existing files:
Dockerfile

    # ❌ Remove this:
    # COPY pyproject_root.toml README.md ./
    
    # ✅ Use this:
    COPY EcommerceAPI ./EcommerceAPI
    COPY README.md ./README.md  # Only if README.md exists

Issue 5: Tests fail with "Connection refused"

Error in test output:
Code

    requests.exceptions.ConnectionError: Failed to establish connection to http://wordpress

Diagnosis steps:
A. Verify WordPress is running

    bash
    
    docker ps | grep wordpress

B. Test DNS resolution

    bash
    
    docker run --rm --network testecommerceapi_wc-net \
      alpine:latest ping -c 3 wordpress

Expected:
Code

    PING wordpress (172.18.0.3): 56 data bytes
    64 bytes from 172.18.0.3: seq=0 ttl=64 time=0.123 ms

C. Test HTTP connection
bash

    docker run --rm --network testecommerceapi_wc-net \
      curlimages/curl:latest curl -v http://wordpress

Expected:
Code

    < HTTP/1.1 302 Found
    < Location: http://wordpress/wp-admin/install.php

D. Verify config uses correct URL

Check config_customers.py:
Python

    API_HOSTS = {
        "docker": "http://wordpress/wp-json/wc/v3/",  # ✅ Correct
        # NOT "http://localhost:8888"  ❌
    }

Check Dockerfile sets API_ENV:
Dockerfile

    ENV API_ENV=docker  # ✅ Must be set

Issue 6: "401 Unauthorized" from API

Error in test logs:
Code

    401 Client Error: Unauthorized for url: http://wordpress/wp-json/wc/v3/customers

Causes:
A. Credentials not passed to container

Check if env vars are set:

    bash
    
    docker compose -f docker-compose.matrix.yml --profile customers \
      run --rm customers env | grep WC_

Expected:
Code

    WC_KEY=ck_abc123...
    WC_SECRET=cs_xyz789...

If empty:

    Verify .env file exists and has correct format
    Export variables in terminal: export WC_KEY=ck_...

B. Wrong credentials

Test credentials manually:

    bash
    
    curl -u "$(grep WC_KEY .env | cut -d= -f2):$(grep WC_SECRET .env | cut -d= -f2)" \
      http://localhost:8888/wp-json/wc/v3/system_status

Expected: JSON response with system info

If 401:

    Regenerate API key in WooCommerce settings
    Ensure permissions are Read/Write

Issue 7: WordPress shows "Error establishing database connection"

Cause: MySQL container not ready when WordPress started.

Fix: Already implemented via healthcheck in docker-compose.wp.yml:
YAML

    db:
      healthcheck:
        test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
    
    wordpress:
      depends_on:
        db:
          condition: service_healthy  # ✅ Waits for healthcheck

If still occurs:
    bash
    
    # Restart WordPress after MySQL is healthy
    docker compose -f docker-compose.wp.yml restart wordpress

Issue 8: Port 8888 already in use

Error:
Code

    Error: Bind for 0.0.0.0:8888 failed: port is already allocated

Find what's using the port:
    bash
    
    # Windows (Git Bash)
    netstat -ano | grep 8888
    
    # Mac/Linux
    lsof -i :8888

Solutions:
Option A: Stop the conflicting service
    bash
    
    # If it's another Docker container
    docker ps  # Find container ID
    docker stop <container_id>

Option B: Use different port

Edit docker-compose.wp.yml:
YAML

    wordpress:
      ports:
        - "8889:80"  # Changed from 8888

Then access: http://localhost:8889
🔄 CI/CD Integration

Your .gitlab-ci.yml already uses this Docker setup. Here's how it works:
Architecture in CI
Code

    GitLab Runner
        │
        ├─ Install Docker
        │
        ├─ Start WordPress (compose -f docker-compose.wp.yml up -d)
        │
        ├─ Wait for health check
        │
        ├─ Generate matrix.yml (dynamically creates test jobs)
        │
        ├─ Run tests in parallel:
        │  ├─ customers_test (Docker container)
        │  └─ orders_test (Docker container)
        │
        ├─ Collect artifacts (reports/)
        │
        └─ Generate Allure report

Key CI Sections
1. Preflight (runs once)
YAML

    shared_preflight:
      stage: preflight
      script:
        - pip install -e './EcommerceAPI[dev]'
        - pytest tests/shared/preflight -s --maxfail=1

Purpose:

    Validate schema
    Check test data
    Fail fast before expensive test matrix

2. Deployment (manual gate)
YAML

    deploy_test:
      stage: deploy
      when: manual  # Requires approval
      environment:
        name: test
      script:
        - echo "🚀 Deploying to test"

Why manual:

    Control when tests run
    Approval workflow
    Cost control (especially for staging/prod)

3. Dynamic Matrix Generation
YAML

    discover_services:
      script:
        - services=$(find tests -maxdepth 1 -type d ! -name shared)
        - |
          echo "stages:" > matrix.yml
          for s in $services; do
            echo "  ${s}_test:" >> matrix.yml
            echo "    script:" >> matrix.yml
            echo "      - pytest tests/${s}" >> matrix.yml
          done
      artifacts:
        paths:
          - matrix.yml

Why dynamic:

    Add new test suite → automatically included
    No manual YAML editing
    Scales to hundreds of services

4. Child Pipeline
YAML

    run_entity_matrix:
      trigger:
        include:
          - artifact: matrix.yml
        strategy: depend

What happens:

    Reads generated matrix.yml
    Spawns parallel jobs (one per service)
    Each job runs in isolated Docker container

📚 Quick Reference
Essential Commands

    bash
    
    # ============================================================
    # WordPress Management
    # ============================================================
    
    # Start WordPress + MySQL
    docker compose -f docker-compose.wp.yml up -d
    
    # Stop (keeps data)
    docker compose -f docker-compose.wp.yml stop
    
    # Stop and remove containers (keeps volumes)
    docker compose -f docker-compose.wp.yml down
    
    # Stop and remove everything (⚠️ deletes database!)
    docker compose -f docker-compose.wp.yml down -v
    
    # View logs
    docker compose -f docker-compose.wp.yml logs -f wordpress
    
    # ============================================================
    # Test Image Management
    # ============================================================
    
    # Build test image
    docker compose -f docker-compose.matrix.yml --profile customers build
    
    # Rebuild without cache
    docker compose -f docker-compose.matrix.yml --profile customers build --no-cache
    
    # Remove image
    docker rmi ecommerceapi-tests:latest
    
    # ============================================================
    # Running Tests
    # ============================================================
    
    # Run single service
    docker compose -f docker-compose.matrix.yml \
      --profile customers \
      up --abort-on-container-exit --remove-orphans
    
    # Run multiple services
    docker compose -f docker-compose.matrix.yml \
      --profile customers --profile orders \
      up --abort-on-container-exit --remove-orphans
    
    # Run interactively (shell access)
    docker compose -f docker-compose.matrix.yml \
      --profile customers \
      run --rm customers bash
    
    # ============================================================
    # Debugging
    # ============================================================
    
    # Check running containers
    docker ps
    
    # Check networks
    docker network ls
    
    # Inspect network
    docker network inspect testecommerceapi_wc-net
    
    # Test connectivity
    docker run --rm --network testecommerceapi_wc-net \
      curlimages/curl:latest curl http://wordpress
    
    # Check container logs
    docker logs wc-wp
    
    # Shell into WordPress container
    docker exec -it wc-wp bash
    
    # Shell into test container (after starting it)
    docker exec -it testecommerceapi-customers-1 bash
    
    # ============================================================
    # Cleanup
    # ============================================================
    
    # Remove stopped containers
    docker container prune -f
    
    # Remove unused images
    docker image prune -a -f
    
    # Remove unused volumes (⚠️ deletes data!)
    docker volume prune -f
    
    # Remove unused networks
    docker network prune -f
    
    # Nuclear option (remove everything)
    docker system prune -a --volumes -f


🐳 Command Breakdown

    bash
    
    docker build -t woocommerce-test .

What it does:

    docker build: Builds a Docker image from a Dockerfile
    -t woocommerce-test: Tags (names) the image as "woocommerce-test"
    .: Uses the current directory as the build context (where to find Dockerfile and files to copy)

📊 Output Explanation
1. Build Summary
Code

    [+] Building 29.9s (16/16) FINISHED

    Total time: 29.9 seconds
    Completed: 16 out of 16 steps
    Build was successful ✅

2. Build Steps Breakdown
Initial Setup
Code

    => [internal] load build definition from Dockerfile (0.0s)
    => [internal] load metadata for docker.io/library/python:3.11-slim (1.1s)
    => [internal] load .dockerignore (0.0s)

    Docker reads your Dockerfile
    Checks Docker Hub for the Python 3.11 base image
    Reads .dockerignore to know what files to exclude

Stage 1: Builder (Building Dependencies)
Code

    => [builder 1/7] FROM docker.io/library/python:3.11-slim

What: Pulls the base Python image Time: Cached (0.0s) - already downloaded previously
Code

    => CACHED [builder 2/7] WORKDIR /app (0.0s)

What: Sets working directory to /app Status: CACHED - reused from previous build (much faster!)
Code

    => CACHED [builder 3/7] RUN apt-get update && apt-get install... (0.0s)

What: Installs system dependencies (gcc, build tools) Status: CACHED - no changes, reused from previous build
Code

    => [builder 4/7] COPY EcommerceAPI ./EcommerceAPI (0.1s)

What: Copies your framework code into the image Time: 0.1s (fast copy)
Code

    => [builder 5/7] COPY README.md ./README.md (0.1s)

What: Copies README file
Code

    => [builder 6/7] RUN pip install --upgrade pip setuptools wheel (4.3s)

What: Updates pip and build tools Time: 4.3 seconds
Code

    => [builder 7/7] RUN pip install -e './EcommerceAPI[dev]' (15.5s)

What: Installs your Python package and all dev dependencies (pytest, allure, etc.) Time: 15.5 seconds (longest step - downloading packages from PyPI)
Stage 2: Runtime Image (Final Optimized Image)
Code

    => [stage-1 3/6] COPY --from=builder /usr/local /usr/local (2.1s)

What: Copies installed Python packages from builder stage Why: Multi-stage build - keeps image smaller by excluding build tools
Code

    => [stage-1 4/6] COPY EcommerceAPI ./EcommerceAPI (0.2s)
    => [stage-1 5/6] COPY tests ./tests (0.1s)
    => [stage-1 6/6] COPY README.md ./README.md (0.1s)

What: Copies your code into the final image
Exporting Final Image
Code

    => exporting to image (5.0s)
    => => exporting layers (2.6s)
    => => exporting manifest sha256:a9b5cf10... (0.0s)
    => => exporting config sha256:8fe94e79... (0.0s)
    => => naming to docker.io/library/woocommerce-test:latest (0.0s)
    => => unpacking to docker.io/library/woocommerce-test:latest

What:

    Creates the final Docker image
    Generates image ID (SHA256 hash)
    Tags it as woocommerce-test:latest
    Makes it available for docker run

🎯 Key Takeaways
✅ What Happened:

    ✅ Built a multi-stage Docker image (builder + runtime)
    ✅ Installed all Python dependencies
    ✅ Created an optimized image named woocommerce-test
    ✅ Image is ready to run tests

⚡ Performance Notes:

    CACHED steps = super fast (reused from previous builds)
    Non-cached steps = code changed, needs rebuild
    Total time: 29.9s = reasonable for a full build

📦 Image Size:

The multi-stage build keeps your image smaller by:

    Stage 1: Installs build tools + dependencies
    Stage 2: Only copies installed packages (no gcc, no build tools)

🚀 Next Steps

Now that the image is built, you can:
1. Verify the image exists:
    bash
    
    docker images | grep woocommerce-test

2. Run tests with this image:
    bash
    
    docker run --rm woocommerce-test pytest tests/customers -v

3. Or use with docker-compose:
    bash
    
    docker compose -f docker-compose.matrix.yml --profile customers up

💡 Pro Tips
To rebuild without cache (fresh build):
    bash
    
    docker build --no-cache -t woocommerce-test .

To see detailed build output:
    bash
    
    docker build --progress=plain -t woocommerce-test .

To inspect the image:
    bash
    
    docker inspect woocommerce-test

To check image size:
    bash
    
    docker images woocommerce-test




Environment Variables Reference
Variable	                Default	            Purpose
API_ENV	                    docker	            Selects URL from config_customers.py
WC_KEY	                    (required)	        WooCommerce consumer key
WC_SECRET	                (required)      	WooCommerce consumer secret
ENABLE_STRUCTURED_LOGS      true	            JSON logging format
LOG_DIR	                    /app/reports/logs	Where logs are written
AUTO_ALLURE_REPORT      	true	            Generate HTML report after tests
REQUIRE_ENV	                false	            Fail if .env missing

Port Reference
Service	    Internal Port	External Port	Purpose
WordPress	80     	8888	HTTP access
MySQL	    3306	(none)	Database (internal only)

File Structure Quick Lookup
Code

    Where is...?
    
    ├─ Test code?               → tests/
    ├─ Test results?            → reports/
    ├─ Logs?                    → reports/logs/
    ├─ Framework code?          → EcommerceAPI/
    ├─ API credentials?         → .env (create manually)
    ├─ WordPress data?          → Docker volume: wp_data
    ├─ MySQL data?              → Docker volume: db_data
    ├─ Infrastructure config?   → docker-compose.wp.yml
    ├─ Test runner config?      → docker-compose.matrix.yml
    ├─ Image definition?        → Dockerfile
    └─ CI pipeline?             → .gitlab-ci.yml

🎓 Summary
What You've Built

✅ Complete Docker-based test environment:

    WordPress + WooCommerce (real backend)
    MySQL database (persistent storage)
    Pytest runners (isolated test execution)
    Shared network (service discovery)
    Volume mounts (bidirectional data flow)

✅ Production-ready features:

    Multi-stage Docker builds (optimized images)
    Profile-based test selection (run what you need)
    Environment-specific configs (dev/staging/prod)
    CI/CD integration (GitLab pipelines)
    Allure reporting (interactive HTML reports)

✅ Best practices:

    Secrets management (.env file)
    Read-only test mounts (prevent accidental edits)
    Health checks (reliable startup order)
    Minimal attack surface (no unnecessary ports)

Architecture Recap
Code

┌────────────────────────────────────────────────────────┐
│  Host Machine (your laptop)                           │
│                                                        │
│  ┌──────────────────────────────────────────────────┐ │
│  │  Docker Network: testecommerceapi_wc-net         │ │
│  │                                                  │ │
│  │  ┌──────────┐    ┌──────────┐    ┌──────────┐ │ │
│  │  │  pytest  │──��▶│WordPress │───▶│  MySQL   │ │ │
│  │  │customer  │    │    +     │    │          │ │ │
│  │  │  tests   │    │WooCommerce│    │          │ │ │
│  │  └────┬─────┘    └──────────┘    └──────────┘ │ │
│  │       │                                        │ │
│  │       │ Mount volumes                          │ │
│  │       ▼                                        │ │
│  └───────┼────────────────────────────────────────┘ │
│          │                                          │
│  ┌───────▼───────┐                                 │
│  │  ./reports/   │◀─── Test results written here   │
│  │  ./tests/     │◀─── Test code mounted here      │
│  └───────────────┘                                  │
└────────────────────────────────────────────────────────┘

Next Steps

  1.  Add more test suites:
        Copy customers service in docker-compose.matrix.yml
        Change profile name and test directory
        Run with --profile <newservice>

  2.  Customize reports:
        Install Allure decorators in tests
        Add screenshots on failure
        Integrate with CI artifacts

  3.  Scale testing:
        Run multiple profiles in parallel
        Use GitLab matrix strategy
        Add performance benchmarks

  4.  Enhance CI:
        Add deployment jobs
        Integrate Slack notifications
        Create test dashboards

📖 Additional Resources

    Docker Compose documentation: https://docs.docker.com/compose/
    WooCommerce REST API docs: https://woocommerce.github.io/woocommerce-rest-api-docs/
    Pytest documentation: https://docs.pytest.org/
    Allure reporting: https://docs.qameta.io/allure/

🎉 Congratulations! You now have a professional Docker-based testing environment. Happy testing! 🚀






### 📋 Complete Setup & Execution Order
🏗️ Phase 1: Infrastructure Setup (One-Time Setup)

Step 1: Start WordPress + MySQL (Backend Infrastructure)
    bash
    
    docker compose -f docker-compose.wp.yml up -d

What happens:

    ✅ Creates Docker network: testecommerceapi_wc-net
    ✅ Starts MySQL container (wc-db)
    ✅ Starts WordPress container (wc-wp)
    ✅ Maps port 8888 on your host to WordPress

Verification:
    bash
    
    docker ps
# You should see: wc-wp and wc-db running

Status: ✅ WordPress + MySQL running ✅ Private network created

Step 2: Configure WordPress (One-Time)
    bash
    
    # Open browser
    http://localhost:8888/wp-admin

What to do:

    Complete WordPress installation (language, admin user, password)
    Install WooCommerce plugin
    Generate API credentials (Consumer Key + Secret)
    Save credentials to .env file

Verification:
    bash
    
    cat .env
    # Should show: WC_KEY=ck_... and WC_SECRET=cs_...

Status: ✅ WooCommerce configured ✅ API credentials ready
🐳 Phase 2: Build Test Image (One-Time or When Code Changes)

Step 3: Build Test Runner Image
    bash
    
    docker compose -f docker-compose.matrix.yml --profile customers build

OR (what you just did):
    bash
    
    docker build -t woocommerce-test .

What happens:

    ✅ Reads Dockerfile
    ✅ Installs Python dependencies (pytest, allure, requests, etc.)
    ✅ Copies your test framework code
    ✅ Creates image: ecommerceapi-tests:latest (or woocommerce-test)

Verification:
    bash
    
    docker images | grep -E "ecommerceapi|woocommerce"

Status: ✅ Test runner image ready

▶️ Phase 3: Run Tests (Repeatable - Do This Every Time)
Step 4: Run Tests
    bash
    
    docker compose -f docker-compose.matrix.yml \
      --profile customers \
      up --abort-on-container-exit --remove-orphans

What happens:

    ✅ Creates test container from your image
    ✅ Joins the testecommerceapi_wc-net network
    ✅ Mounts ./tests folder (read-only)
    ✅ Mounts ./reports folder (read-write)
    ✅ Runs: pytest tests/customers
    ✅ Generates Allure reports
    ✅ Container stops and removes itself

Verification:
    bash
    
    ls -la reports/customers/allure-results/
    # Should see JSON test result files

Status: ✅ Tests executed ✅ Reports generated
🎯 Complete Hierarchy Diagram
Code

┌─────────────────────────────────────────────────────────────────┐
│                    COMPLETE DOCKER TEST SETUP                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  PHASE 1: INFRASTRUCTURE (One-Time Setup)                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Step 1: Start Backend Infrastructure                          │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ $ docker compose -f docker-compose.wp.yml up -d          │ │
│  └──────────────────────────────────────────────────────────┘ │
│           │                                                     │
│           ├─► Creates Network: testecommerceapi_wc-net         │
│           ├─► Starts MySQL Container (wc-db)                   │
│           └─► Starts WordPress Container (wc-wp)               │
│                                                                 │
│  Step 2: Configure WordPress                                   │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ 1. Browse to http://localhost:8888                       │ │
│  │ 2. Install WooCommerce plugin                            │ │
│  │ 3. Generate API credentials                              │ │
│  │ 4. Save to .env file                                     │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ✅ Result: Backend ready for testing                          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  PHASE 2: BUILD TEST IMAGE (When Code Changes)                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Step 3: Build Test Runner Image                               │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ $ docker compose -f docker-compose.matrix.yml \          │ │
│  │     --profile customers build                            │ │
│  └──────────────────────────────────────────────────────────┘ │
│           │                                                     │
│           ├─► Reads Dockerfile                                 │
│           ├─► Installs Python dependencies                     │
│           ├─► Copies test framework code                       │
│           └─► Creates image: ecommerceapi-tests:latest         │
│                                                                 │
│  ✅ Result: Test image ready                                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  PHASE 3: RUN TESTS (Every Test Execution)                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Step 4: Execute Tests                                          │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ $ docker compose -f docker-compose.matrix.yml \          │ │
│  │     --profile customers up \                             │ │
│  │     --abort-on-container-exit --remove-orphans           │ │
│  └──────────────────────────────────────────────────────────┘ │
│           │                                                     │
│           ├─► Creates test container                           │
│           ├─► Joins network with WordPress                     │
│           ├─► Mounts ./tests (code)                            │
│           ├─► Mounts ./reports (results)                       │
│           ├─► Runs pytest                                      │
│           ├─► Generates Allure reports                         │
│           └─► Container stops & removes                        │
│                                                                 │
│  ✅ Result: Test results in ./reports/                         │
└─────────────────────────────────────────────────────────────────┘

📊 What You've Actually Built

Let me show you what's running right now on your machine:
    bash
    
    # Check what's running
    docker ps

Expected Output:
Code

    CONTAINER ID   IMAGE                           STATUS          PORTS                  NAMES
    abc123def456   wordpress:6.4-php8.2-apache    Up 10 minutes   0.0.0.0:8888->80/tcp   wc-wp
    789ghi012jkl   mysql:8.0                      Up 10 minutes   3306/tcp               wc-db

What you have:

    ✅ 2 containers running (WordPress + MySQL)
    ✅ 1 Docker network (testecommerceapi_wc-net)
    ✅ 1 Docker image built (woocommerce-test or ecommerceapi-tests)
    ✅ Test code ready (in ./tests folder)

🎯 What Happens When You Run Tests
Code

Your Host Machine
    │
    ├── ./tests/              ← Your test code (editable)
    ├── ./reports/            ← Test results (generated)
    └── .env                  ← API credentials
         │
         │
    ┌────▼─────────────────────────────────────────────┐
    │   Docker Network: testecommerceapi_wc-net        │
    │                                                   │
    │   ┌─────────────┐         ┌─────────────┐       │
    │   │  MySQL      │◄────────┤ WordPress   │       │
    │   │  (wc-db)    │         │  (wc-wp)    │       │
    │   │  Running    │         │  Running    │       │
    │   └─────────────┘         └──────▲──────┘       │
    │                                  │               │
    │                                  │ HTTP          │
    │                           ┌──────┴──────┐       │
    │                           │  Test       │       │
    │                           │  Container  │       │
    │                           │  (created)  │       │
    │                           │             │       │
    │                           │  Reads:     │       │
    │                           │  ./tests    │       │
    │                           │             │       │
    │                           │  Writes:    │       │
    │                           │  ./reports  │       │
    │                           └─────────────┘       │
    │                           (starts, runs, exits) │
    └───────────────────────────────────────────────────┘

🔄 Typical Daily Workflow
Morning Setup (Once)
    bash
    
    # 1. Start infrastructure (if not already running)
    docker compose -f docker-compose.wp.yml up -d

    # 2. Verify it's running
    docker ps

Development Cycle (Repeat)
    bash
    
    # 3. Edit your test files in ./tests/
    # (Use VS Code, PyCharm, etc.)
    
    # 4. Run tests (no rebuild needed if only tests changed)
    docker compose -f docker-compose.matrix.yml \
      --profile customers \
      up --abort-on-container-exit
    
    # 5. Check results
    ls reports/customers/allure-results/
    
    # 6. View Allure report (optional)
    allure serve reports/customers/allure-results/

When You Change Framework Code
    bash
    
    # Rebuild image (framework code changed)
    docker compose -f docker-compose.matrix.yml --profile customers build
    
    # Then run tests again
    docker compose -f docker-compose.matrix.yml \
      --profile customers \
      up --abort-on-container-exit

End of Day Cleanup (Optional)
    bash
    
    # Stop WordPress (keeps data)
    docker compose -f docker-compose.wp.yml stop
    
    # OR completely remove (deletes database)
    docker compose -f docker-compose.wp.yml down -v

✅ Current Status Check

Run these commands to see what you have:
    bash
    
    # 1. Check running containers
    docker ps
    
    # 2. Check networks
    docker network ls | grep wc
    
    # 3. Check images
    docker images | grep -E "ecommerceapi|woocommerce|wordpress|mysql"
    
    # 4. Check if WordPress is accessible
    curl http://localhost:8888
    
    # 5. Check test files
    ls -la tests/
    
    # 6. Check if .env exists
    cat .env

🎯 Answer to Your Question
"So after the build of image, the next step is already to run test?"

Answer: Not quite! Here's the order:

    ✅ Start WordPress + MySQL (you may have done this)
    ✅ Configure WordPress (generate API keys)
    ✅ Build test image ← YOU JUST DID THIS
    ⏭️ Run tests ← THIS IS YOUR NEXT STEP

Next Command to Execute:
    bash
    
    docker compose -f docker-compose.matrix.yml \
      --profile customers \
      up --abort-on-container-exit --remove-orphans

📝 Quick Reference Card
What	Command	Frequency
Start WordPress	docker compose -f docker-compose.wp.yml up -d	Once (or after restart)
Build test image	docker compose -f docker-compose.matrix.yml --profile customers build	When code changes
Run tests	docker compose -f docker-compose.matrix.yml --profile customers up --abort-on-container-exit	Every test run
Stop WordPress	docker compose -f docker-compose.wp.yml stop	End of day (optional)


# Docker Setup and Execution Order Guide

This guide provides an overview of the complete Docker setup and execution order for the TestEcommerceAPI project. It is divided into three main phases:

## Phase 1: Infrastructure Setup
In this phase, we start the required services: WordPress and MySQL, and configure WordPress for the application.

### Steps:
1. **Start the MySQL Container**:
   ```bash
   docker run --name mysql-db -e MYSQL_ROOT_PASSWORD=root -e MYSQL_DATABASE=wordpress -d mysql:5.7
   ```
   - This command starts a MySQL database container with the specified root password and database.

2. **Start the WordPress Container**:
   ```bash
   docker run --name wordpress --link mysql-db:mysql -p 8000:80 -d wordpress
   ```
   - This command links the WordPress container to the MySQL container. WordPress will be accessible on port 8000.

3. **Configure WordPress**:
   - Access the WordPress instance at `http://localhost:8000` to set up the site and connect it to the MySQL database.

### Hierarchy Diagram:
```
Infrastructure Setup
└── MySQL Container
└── WordPress Container
```

---

## Phase 2: Build Test Image
In this phase, we create a Docker image specifically for running tests within our application.

### Steps:
1. **Create a Dockerfile for the Test Runner**:
   ```Dockerfile
   FROM php:7.4-cli
   WORKDIR /app
   COPY . .
   RUN composer install
   CMD ["phpunit"]
   ```
   - This Dockerfile sets up a PHP environment, installs the necessary dependencies, and prepares the PHPUnit testing framework.

2. **Build the Test Image**:
   ```bash
   docker build -t test-runner .
   ```
   - Use this command to build the Docker image tagged as `test-runner`.

### Workflow Example:
- The test image can be built from the project root containing the `Dockerfile`.

---

## Phase 3: Run Tests
In the final phase, we execute the tests to ensure the application functions as expected.

### Steps:
1. **Run the Test Runner**:
   ```bash
   docker run --network=host test-runner
   ```
   - This command runs the test suite in the context of our network setup.

### Verification Commands:
- Check logs for a specific container:
   ```bash
   docker logs wordpress
   ```

---

## Quick Reference Card:
| Command                                   | Phase                       | Description                                      |
|-------------------------------------------|-----------------------------|--------------------------------------------------|
| `docker run ... mysql`                    | Phase 1 Infrastructure Setup | Start MySQL container                             |
| `docker run ... wordpress`                | Phase 1 Infrastructure Setup | Start WordPress container                         |
| `docker build -t test-runner .`          | Phase 2 Build Test Image    | Build Docker image for tests                     |
| `docker run --network=host test-runner`  | Phase 3 Run Tests           | Execute tests in the test runner container       |




### Command Comparison
Command 1: With Flags ✅ (Recommended for Tests)
    bash
    
    docker compose -f docker-compose.matrix.yml \
      --profile customers \
      up --abort-on-container-exit --remove-orphans

What it does:

`--abort-on-container-exit `→ Stops all containers when the test container finishes
`--remove-orphans` → Removes containers from other compose files (like wc-wp, wc-db)

Behavior:
Code

1. Test container starts
2. Test runs
3. Test finishes (pass or fail)
4. ✅ All containers stop automatically
5. You get your terminal back

Use when:

    ✅ Running tests in CI/CD
    ✅ Running tests locally and want auto-cleanup
    ✅ You want the process to exit after tests complete

Command 2: Without Flags (Interactive Mode)
bash

    `docker compose -f docker-compose.matrix.yml --profile customers up`

What it does:

    Starts containers and keeps them running
    Shows live logs
    You must press Ctrl+C to stop

Behavior:
Code

1. Test container starts
2. Test runs
3. Test finishes
4. ❌ Container keeps running (waiting for more tests)
5. Logs keep streaming
6. You must press Ctrl+C to stop

Use when:

    🔍 Debugging (you want to inspect logs after tests)
    🔍 Running multiple test iterations manually
    🔍 Need to exec into the container after tests

⚠️ About --remove-orphans

IMPORTANT: This flag is dangerous when you have docker-compose.wp.yml running!
    `bash
    
    --remove-orphans  # ⚠️ Will STOP and REMOVE wc-wp and wc-db!`

It considers wc-wp and wc-db as "orphans" because they're from a different compose file.

### 🎯 Recommended Commands

**For Local Development** (Keep WordPress Running)

    bash
    
    # Start WordPress (in background)
    docker compose -f docker-compose.wp.yml up -d
    
    # Run tests WITHOUT --remove-orphans
    docker compose -f docker-compose.matrix.yml --profile customers up --abort-on-container-exit

✅ Tests stop automatically
✅ WordPress keeps running
✅ You can run tests multiple times

**For CI/CD Pipeline**

    `bash
    
    # Start WordPress
    docker compose -f docker-compose.wp.yml up -d
    
    # Run tests with cleanup
    docker compose -f docker-compose.matrix.yml \
      --profile customers \
      up --abort-on-container-exit --remove-orphans`

✅ Everything stops after tests
✅ Clean environment

For Debugging (See All Logs)
    `
    bash
    
    # Run without --abort-on-container-exit
    docker compose -f docker-compose.matrix.yml \
      --profile customers \
      up
    
    # Press Ctrl+C when done`

✅ See full logs
✅ Can scroll through output
✅ Manual control

📋 Quick Reference

|Scenario                |Command
| :---                   | :--- 
|Normal test run	     |up --abort-on-container-exit
|Debugging	             |up (no flags)
|CI/CD	                 |up --abort-on-container-exit --remove-orphans
|With WordPress running	 |up --abort-on-container-exit (NO --remove-orphans)

### 🚀 What You Should Use Now

Since you want to use your local WordPress, use this:

    bash
    
    # Option 1: Use local WordPress (no Docker WordPress needed)
    docker compose -f docker-compose.matrix.yml \
      --profile customers \
      up --abort-on-container-exit

OR if you want to use Docker WordPress:

    `bash
    
    # Start WordPress first
    docker compose -f docker-compose.wp.yml up -d
    
    # Run tests (without --remove-orphans to keep WordPress running)
    docker compose -f docker-compose.matrix.yml \
      --profile customers \
      up --abort-on-container-exit`

TL;DR: Use --abort-on-container-exit ✅ but skip --remove-orphans ❌ when WordPress is running separately! 🎯




## 📋 Summary: What We Learned
The Problem:

* Docker WordPress (wc-wp) was running on port 8888
* It was uninstalled → redirecting all requests to /wp-admin/install.php
* Your local WordPress couldn't use port 8888 at the same time
* Tests were hitting the wrong WordPress (Docker, uninstalled) instead of your local one (installed)

The Solution:
Scenario	                What to Run	                                                         Port 8888 Used By
Local pytest tests	        pytest -v -m tcid333	                                             Your local WordPress (XAMPP/WAMP) ✅
Docker tests (local dev)	docker compose -f docker-compose.matrix.yml --profile customers up   Your local WordPress (use host.docker.internal) ✅
GitLab CI	                Docker Compose pipeline	                                             Docker WordPress (containerized) ✅

#### 🎯 Your Workflow Going Forward
For Local Development (pytest on Windows):

    bash
    
    # Make sure Docker WordPress is NOT running
    docker compose -f docker-compose.wp.yml down
    
    # Run tests locally
    pytest -v -m tcid333 -r s

→ Uses ENV=test → http://localhost:8888/kwakiweb/... ✅


For Docker Tests (testing containerization locally):

    bash
    
    # Stop Docker WordPress (if running)
    docker compose -f docker-compose.wp.yml down
    
    # Use ENV=dev to point to local WordPress
    docker compose -f docker-compose.matrix.yml --profile customers up --abort-on-container-exit

→ Uses ENV=dev → http://host.docker.internal:8888/kwakiweb/... ✅

For GitLab CI:
YAML

    # .gitlab-ci.yml
    script:
      - docker compose -f docker-compose.wp.yml up -d  # Start Docker WordPress
        - docker exec wc-wp wp core install ...          # Install WordPress
        - docker exec wc-wp wp plugin install woocommerce --activate --allow-root
        - docker compose -f docker-compose.matrix.yml --profile customers up --abort-on-container-exit

→ Uses ENV=docker → http://wordpress/... ✅



## 🚀 Running Docker Tests Locally
Step 1: Start WordPress Stack

    bash
    
    # Start WordPress + MySQL
    docker compose -f docker-compose.wp.yml up -d
    
    # Wait for services to be ready
    sleep 20
    
    # Verify containers are running
    docker ps

Step 2: Install WordPress + WooCommerce

    bash
    
    # Install WordPress
    docker exec wc-wp wp core install \
      --url="http://localhost:8888" \
      --title="Local Test Store" \
      --admin_user="admin" \
      --admin_password="admin" \
      --admin_email="admin@test.com" \
      --skip-email \
      --allow-root
    
    # Verify installation
    docker exec wc-wp wp core is-installed --allow-root
    
    # Install WooCommerce
    docker exec wc-wp wp plugin install woocommerce --activate --allow-root
    
    # Verify WooCommerce is active
    docker exec wc-wp wp plugin list --allow-root

Step 3: Run Tests in Docker

    bash
    
    # Run customer tests
    docker compose -f docker-compose.matrix.yml \
      --profile customers \
      up --abort-on-container-exit
    
    # Or run all tests
    docker compose -f docker-compose.matrix.yml \
      --profile customers \
      --profile orders \
      up --abort-on-container-exit
    
    Step 4: Cleanup (When Done)

    bash
    
    # Stop and remove all containers
    docker compose -f docker-compose.wp.yml down -v
    docker compose -f docker-compose.matrix.yml down -v

#### 🔧 Create a Helper Script (Recommended)

Create scripts/run-docker-tests.sh:

    bash
    
    #!/bin/bash
    set -e
    
    echo "🚀 Starting WordPress stack..."
    docker compose -f docker-compose.wp.yml up -d
    
    echo "⏳ Waiting for services to be ready..."
    sleep 30
    
    echo "📦 Installing WordPress..."
    docker exec wc-wp wp core install \
      --url="http://localhost:8888" \
      --title="Local Test" \
      --admin_user="admin" \
      --admin_password="admin" \
      --admin_email="admin@test.com" \
      --skip-email \
      --allow-root
    
    echo "🛒 Installing WooCommerce..."
    docker exec wc-wp wp plugin install woocommerce --activate --allow-root
    
    echo "✅ WordPress setup complete!"
    echo ""
    echo "🧪 Running tests..."
    
    # Run tests with specified profile (default: customers)
    PROFILE=${1:-customers}
    docker compose -f docker-compose.matrix.yml \
      --profile "$PROFILE" \
      up --abort-on-container-exit
    
    # Capture exit code
    EXIT_CODE=$?
    
    echo ""
    echo "🧹 Cleaning up..."
    docker compose -f docker-compose.wp.yml down -v
    docker compose -f docker-compose.matrix.yml down -v
    
    exit $EXIT_CODE

**Make it executable:**

bash

`chmod +x scripts/run-docker-tests.sh`

**Verify it exists**

bash

    # Check the file
    ls -la scripts/
    
    # Should show:
    # -rwxr-xr-x ... run-docker-tests.sh
    #  ^^^
    #  executable



**Run it - Usage:**

    bash
    
    # Run customer tests From project root (TestEcommerceAPI/)
    ./scripts/run-docker-tests.sh customers
    
    # Run order tests
    ./scripts/run-docker-tests.sh orders
    
    # Run product tests
    ./scripts/run-docker-tests.sh products

**🔍 If You Get "Permission Denied"**

bash

    # Make sure you're in the project root
    pwd  # Should show: /c/Users/kwaki/TestEcommerceAPI
    
    # Check if file exists
    ls -la scripts/run-docker-tests.sh
    
    # If it shows -rw-r--r-- (not executable), run:
    chmod +x scripts/run-docker-tests.sh
    
    # Now run:
    ./scripts/run-docker-tests.sh customers



**📋 Quick Reference**

Manual Commands:

    bash
    
    # 1. Start WordPress
    docker compose -f docker-compose.wp.yml up -d
    
    # 2. Setup (one-time)
    docker exec wc-wp wp core install --url="http://localhost:8888" --title="Test" --admin_user="admin" --admin_password="admin" --admin_email="test@test.com" --skip-email --allow-root
    docker exec wc-wp wp plugin install woocommerce --activate --allow-root
    
    # 3. Run tests
    docker compose -f docker-compose.matrix.yml --profile customers up --abort-on-container-exit
    
    # 4. Cleanup
    docker compose -f docker-compose.wp.yml down -v

Using Script:

bash

`./scripts/run-docker-tests.sh customers`

### 🎯 Local Development Workflow

Option 1: Use Local WordPress (Fast)

    bash
    
    # No Docker needed!
    pytest -v -m tcid333 -r s

    ✅ Fastest
    ✅ No container overhead
    ✅ Uses your existing WordPress
    ⚠️ Requires local WordPress running

Option 2: Use Docker (CI Simulation)
bash

    ./scripts/run-docker-tests.sh customers

* ✅ Exact same as GitLab CI
* ✅ Isolated environment
* ✅ Tests Docker networking
* ⚠️ Slower (container startup)

🔧 Update docker-compose.wp.yml for Local CLI

Make sure you're using the CLI image:
YAML

    services:
      wordpress:
        image: wordpress:cli-php8.2  # ✅ Has wp command
        container_name: wc-wp
        # ... rest of config

📁 Project Structure
Code

`TestEcommerceAPI/
├── docker-compose.wp.yml          # WordPress stack
├── docker-compose.matrix.yml      # Test containers
├── scripts/
│   └── run-docker-tests.sh       # ✅ Helper script
├── .gitlab-ci.yml                 # CI pipeline
└── tests/
    ├── customers/
    ├── orders/
    └── products/`

🎯 Summary

Scenario	         Command	                             WordPress
Quick local test	 pytest -v -m tcid333	                 Your local WordPress
Docker test (CLI)	./scripts/run-docker-tests.sh customers	 Docker WordPress
GitLab CI	        (automatic)                              Docker WordPress

Create the script and try it! 🚀
    `bash
    
    # Create script
    mkdir -p scripts
    # Copy the script content above to scripts/run-docker-tests.sh
    chmod +x scripts/run-docker-tests.sh
    
    # Run it
    ./scripts/run-docker-tests.sh customers`
