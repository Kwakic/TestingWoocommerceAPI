# README — pyproject.toml (how we use them in this repo) 🧭

This project uses two `pyproject.toml` files on purpose:

- Root-level: `./pyproject.toml` — tool configuration for the whole repo (pytest options, linting settings, etc.).  
- Package-level: `./EcommerceAPI/pyproject.toml` — packaging metadata for the installable framework (name, version, dependencies, extras).

Short answer: keep them separate. That’s the recommended layout for a repo that contains a shared, installable package plus a top-level test/CI suite.

Why two files? (simple)
- Package metadata (distribution name, version, dependencies, setuptools settings) belongs inside the package directory so `pip install -e ./EcommerceAPI` and building wheels find the right files.
- Tooling and test discovery (pytest, black, isort, CI options) are repository concerns and belong at the repo root so CI, editors, and developers all share the same config.

If you prefer a single file, you can merge—but be careful:
- A single root `pyproject.toml` can hold both packaging metadata and tool config, but that makes the repo root the package root. It’s okay for single-package repos, but with the current layout (a `EcommerceAPI/` package folder) keeping package metadata inside `EcommerceAPI/` is clearer and less error-prone.

Quick reference / commands ✅
- Install the framework in editable (recommended):
  ```bash
  # run from the repo root
  pip install -e './EcommerceAPI[dev]'
  ```
  - Uses the `dev` extras declared in `EcommerceAPI/pyproject.toml`.
  - Make sure CI/docker scripts use the same extra name (`dev`) — keep extras consistent.

- Run tests (repo root):
  ```bash
  pytest                 # uses repo-level pytest settings in root pyproject
  pytest tests/customers # run a single service
  pytest tests/foo -k "name" -m smoke
  ```

- See which pytest config is used:
  ```bash
  pytest -o log_cli=false --trace-config
  ```

- Inspect test discovery:
  ```bash
  pytest --collect-only -q tests/
  ```

Recommended repo-level pytest config (already in your root pyproject)
- Keep the `[tool.pytest.ini_options]` block at repo root. It’s the single source of truth for testpaths, patterns, `addopts`, markers, and logging.
- Remove `pythonpath` if you use editable installs. Example: comment out `pythonpath = ["EcommerceAPI/src"]` and use `pip install -e './EcommerceAPI[dev]'` instead.

Why editable installs > pythonpath hacks
- Editable installs (PEP 660) make imports behave like a real install but point to live source — this prevents surprises between dev and CI.
- `pythonpath` silently hides packaging/import problems and can produce different behavior in CI.

Packaging notes (EcommerceAPI/pyproject.toml)
- Keep package name lowercased in metadata (e.g. `ecommerceapi`) — consistent with PyPI convention.
- Ensure `tool.setuptools.packages.find.where` matches your layout:
  - If code lives in `EcommerceAPI/src/...` use:
    ```toml
    [tool.setuptools.packages.find]
    where = ["src"]
    include = ["EcommerceAPI*"]

    [tool.setuptools.package-dir]
    "" = "src"
    ```
  - If code is directly under `EcommerceAPI/` (package-in-place), use:
    ```toml
    [tool.setuptools.packages.find]
    where = ["."]
    include = ["EcommerceAPI*"]
    ```

Make extras consistent
- Your package declares `dev` extras. Make sure CI, Dockerfile and any `pip install` commands use `.[dev]`. Either:
  - Change `pip install -e '.[test]'` → `pip install -e '.[dev]'` everywhere; or
  - Add a `test` extras alias in package pyproject (less preferred).

Docker / CI notes
- Dockerfile must COPY package sources before running `pip install -e '.[dev]'` in builder stage (so editable install works during image build).
- Keep the repo root pytest block — CI and docker runs will pick it up when tests are executed from repo root.
- GitHub Actions matrix: discovery must emit a valid JSON array of quoted service names (e.g. `["customers","orders"]`) to use `fromJson()` correctly.
- GitLab dynamic pipelines: the discover job generates a `matrix.yml` artifact at runtime — that artifact is referenced in `artifacts: paths: - matrix.yml`.

Troubleshooting — “0 tests collected” checklist 🧰
1. Don’t use filters while debugging (avoid `-m`, `-k`, `-q`).  
   Run:
   ```bash
   pytest --collect-only -q tests/
   ```
2. Confirm pytest config used:
   ```bash
   pytest -o log_cli=false --trace-config
   ```
   (some logging plugins print early; disabling `log_cli` shows pytest’s config trace clearly)
3. Ensure your package is importable (editable install recommended):
   ```bash
   python -c "import EcommerceAPI; print(getattr(EcommerceAPI,'__file__','NOT IMPORTABLE'))"
   ```
   If it prints `NOT IMPORTABLE`, run:
   ```bash
   pip install -e './EcommerceAPI[dev]'
   ```
4. Check for `-m` or `PYTEST_ADDOPTS` filtering:
   - Avoid `-m` unless you know tests exist with that marker.
   - Check `echo $PYTEST_ADDOPTS` or `echo $env:PYTEST_ADDOPTS` (PowerShell).
5. Search for code that modifies collection:
   ```bash
   # grep/PowerShell: find hooks like pytest_collection_modifyitems, collect_ignore, deselect
   ```
6. If a plugin is interfering, disable it when collecting:
   ```bash
   pytest --collect-only -q tests/ -p no:allure_pytest -p no:faker -p no:pytest_metadata
   ```

Suggested small edits you may want to make (quick list)
- Standardize extras name: use `dev` everywhere.  
- Keep root pytest block; remove any duplicate pytest sections in `EcommerceAPI/pyproject.toml` (only if you want repo-level tests to control discovery). If you need a different pytest config inside `EcommerceAPI/` (rare), keep it but be explicit when running tests from that folder.
- Add a `.dockerignore` to speed builds:
  ```
  .venv/
  __pycache__/
  .pytest_cache/
  reports/
  build/
  dist/
  .git
  ```
- Make Dockerfile copy package before `pip install -e '.[dev]'`.

Where to merge vs keep separate (decision guide)
- Keep separate if:
  - You want `EcommerceAPI/` to be installable independently (recommended).
  - You want repo-level tooling config (tests, formatters) independent of packaging.
- Merge into a single `pyproject.toml` only if:
  - This repo is a single-package project and you prefer one-file config.
  - You’re comfortable moving packaging metadata to repo root and adjusting paths.

