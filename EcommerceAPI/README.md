# EcommerceAPI

`EcommerceAPI` is the reusable framework package for the TestEcommerceAPI
WooCommerce quality engineering project. It contains the API clients,
configuration, authentication, test data, and supporting utilities used by the
repository's REST, GraphQL, and UI test suites.

The package requires Python 3.13 or newer.

## One-command setup

Make sure **Docker Desktop is running**, then clone the repository and start
the full setup:

```bash
git clone https://github.com/Kwakic/TestingWoocommerceAPI.git
cd TestingWoocommerceAPI
make run
```

`make run` bootstraps the local environment, installs the framework and
Playwright, starts Docker, provisions WordPress and WooCommerce, generates REST
credentials, configures the test environment, seeds deterministic UI data,
and runs the test suite.

The command is designed to be **idempotent**: it reuses valid local state where
possible and avoids duplicate setup work. You do not need to activate `.venv`
manually; the Makefile invokes the project-local environment directly.

After bootstrap, run the suite again with:

```bash
make test
```

## Direct framework setup

For framework development from an existing checkout, install the framework
and its development dependencies with:

```bash
python -m pip install -e "./EcommerceAPI[dev]"
```

The `dev` extra includes pytest, pytest-xdist, Playwright, and the other tools
needed to develop and run the project's test suites. Run the tests from the
repository root so the project-level pytest configuration and fixtures are
available:

```bash
python -m pytest -n auto -v
```
