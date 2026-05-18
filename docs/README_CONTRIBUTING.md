# Contributing — TestEcommerceAPI

Thanks for contributing! This page covers the minimal workflow for running tests locally, making small changes, and submitting a PR.

Quick workflow
1. Fork the repo and create a branch for your change:
   ```bash
   git checkout -b fix/some-descriptive-name
   ```
2. Follow the developer setup in `DEV_SETUP.md` to run tests locally.
3. Make the change and run tests relevant to your change:
   ```bash
   # run the single test file you touched
   pytest path/to/that/test_file.py -q -vv
   ```
4. Commit with a descriptive message and push:
   ```bash
   git add .
   git commit -m "Fix: short description of change"
   git push origin fix/some-descriptive-name
   ```
5. Open a Pull Request against the `main` (or `develop`) branch. Include:
   - What you changed and why
   - How to reproduce/test locally
   - Any impact on CI or Docker images

Testing & CI specifics
- The repo uses a repo-level pytest config at `pyproject.toml`. Run pytest from repo root so config and paths are consistent.
- Install the framework editor-style before running tests:
    ```bash
    # From repo root (recommended)
    # Activate local virtual environment
    source .venv/Scripts/activate

    # Upgrade packaging tooling
    python -m pip install --upgrade pip setuptools wheel

    # Install framework + dev dependencies
    python -m pip install -e "./EcommerceAPI[dev]"
    ```
- Use `pytest --collect-only -q` if you suspect tests aren’t being discovered.

Style & PR checklist
- Keep commits small and focused.
- Add/adjust tests for any functional change.
- Run `pytest` and ensure the tests you touched pass locally.
- If you modify Dockerfile/CI scripts, describe how to test them locally (e.g., docker build + compose up commands).

Reporting issues and questions
- Open an issue if you find flaky tests or CI failures. Include:
  - Steps to reproduce
  - Your environment (OS, Python, pytest version)
  - Any logs or pytest outputs (use `pytest -vv` to capture details)
- For onboarding questions, open a short PR with a proposed doc or fix — it’s the fastest way to iterate.

**Framework architecture rules (read before coding)**

This repository is a **shared, installable test framework**, not an application.

**Please respect these boundaries:**

---

## 📁 Repository Structure

### `plugins/`

- pytest plugins, hooks, fixtures
- session-level behavior only
- **may not contain business logic**

### `src/configs/`

- static, reusable, non-runtime configuration (maps, constants)
- **must not read environment variables**

### `src/utilities/`

- generic helpers (logging, parsing, formatting)
- **must be framework-agnostic**

### `src/helpers/`

- service-specific helpers (customers, orders, etc.)
- **no pytest imports here**

> ⚠️ **If you're unsure where something belongs, ask before merging.**

---

## ⚙️ Configuration Rules (Critical)

Configuration in this framework follows a **single-source-of-truth contract**.

### Hard rules

| ❌ **Do NOT** |
|---------------|
| Call `os.getenv()` outside `plugins/_config.py` |
| Parse booleans, ints, or defaults in plugins or helpers |
| Introduce new config flags outside `_config.py` |
| Add "convenience" config loaders |

### ✅ Correct pattern

All environment variables are:

- ✅ Read **once**
- ✅ Parsed **once**
- ✅ Frozen at **session start**

**Plugins** import resolved constants directly from `_config.py`
**Tests** rely on fixtures and plugin behavior

### If your change adds a new behavior flag:

1. Add it to `_config.py`
2. Add it to the startup banner
3. Document it in `CONFIG_CONTRACT.md`
4. Update `.env.example` if applicable

---

## 📝 Logging & Runtime Context Rules

The framework distinguishes between **configuration** and **runtime context**.

### Configuration:
- 🔒 Static
- 🌍 Env-driven
- 📂 Defined in `_config.py`

### Runtime context:
- Session id
- Test node id
- Correlation id
- CI / git metadata

### Rules for runtime context:

| ✅ **Must** | ❌ **Must NOT** |
|-------------|-----------------|
| Use `contextvars` (`log_context.py`) | Read from env in plugins |
| Be dynamic and session-scoped | Live in `_config.py` |

> ⚠️ **Do not refactor logging paths, record factories, or formatters casually** — these affect every test and CI run.

---

## 📚 When Documentation Must Be Updated

You **must** update documentation if your PR:

- ✅ Adds or removes a config flag
- ✅ Changes config precedence or defaults
- ✅ Moves config or runtime metadata
- ��� Changes logging output or startup banners
- ✅ Changes plugin responsibilities

### Relevant docs:

- `CONFIG_CONTRACT.md` (authoritative)
- `ENVIRONMENT_CONFIG_GUIDE.md` (practical)
- `.env.example` (developer-facing)

> **Docs are not optional for framework changes.**

---

## 🚨 What Not to Refactor Casually

Please **do not "clean up"** or refactor these unless the PR is explicitly about them:

| 🔒 **Do Not Touch** |
|---------------------|
| Configuration resolution |
| Logging bootstrap |
| pytest session hooks |
| Allure integration |
| Runtime metadata generation |

> These systems are **tightly coupled** and changes ripple across CI, logs, and reports.

**If something feels wrong, open an issue first.**

---

## 🎯 Final Note

This framework prioritizes:

- ✅ **Determinism** over convenience
- ✅ **Explicit contracts** over flexibility
- ✅ **Boring code** over clever code

### If in doubt:

> **Make the smallest change that respects the existing contracts.**

---

## 🤝 What's Next?

If you want, I can help with:

- ✅ Aligning `CONTRIBUTING.md` terminology exactly with `CONFIG_CONTRACT.md`
- ✅ Adding a PR template that enforces these rules automatically
- ✅ Adding a "safe refactor checklist" for maintainers only

---

✨ **Thank you for respecting the framework boundaries!**

Thanks — we appreciate your contributions! If you want a PR template or a developer Makefile, I can add them.
