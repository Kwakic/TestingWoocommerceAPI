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
  pip install -e './EcommerceAPI[dev]'
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

Thanks — we appreciate your contributions! If you want a PR template or a developer Makefile, I can add them.