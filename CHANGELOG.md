# Changelog

All notable changes to this project will be documented in this file.
This project follows [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

### Added

- Automatic creation of the `wp-data` directory during local environment setup.
- One-command onboarding for fresh clones using `make run`, including Docker startup, WordPress provisioning, WooCommerce installation, and automatic REST API credential generation.

### Changed

- Updated the local bootstrap workflow to always start the Docker infrastructure before executing the WordPress/WooCommerce bootstrap process.
- Improved the reliability of the local development environment by ensuring the bootstrap process runs against a freshly started Docker stack.

### Fixed

- Fixed `make run` failing on fresh repository clones due to the Docker infrastructure not being started before the bootstrap process.
- Fixed the local WooCommerce bootstrap sequence so WordPress installation, WooCommerce installation, and REST API credential generation complete successfully on a clean checkout.
- Removed an unintended stray character from `scripts/setup.sh` that could interrupt the bootstrap process.
- Fixed the developer onboarding experience so a fresh clone can be fully provisioned with a single command (`make run`).

### Removed

-
-

---

## [1.0.0] – YYYY-MM-DD

### Added
- Initial release of TestEcommerceAPI
- Shared framework (`EcommerceAPI`) with:
  - Logging plugin
  - Reporting plugin
  - Cleanup plugin
  - Utilities package
  - Schema engine
- Customers, Orders, Coupons, Products test suites
- Preflight + performance shared tests
- GitHub/GitLab CI pipelines
- Docker runtime

---

## Versioning Rules

- **MAJOR** – Breaking change in shared framework or global helper.
- **MINOR** – New features, plugins, schemas, or utilities.
- **PATCH** – Bugfixes in existing logic.
