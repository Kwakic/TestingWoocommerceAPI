# Using Allure with this project

This document explains, in simple steps, how to produce and view Allure test reports for this repository.

## TL;DR (Quick Start)

**Corrected Order of Operations**

1. Run the test:

    This clears old results but keeps your environment clean for the current run.
```powershell
pytest -m tcid03 -q -r s --clean-alluredir --alluredir=reports/allure-results

pytest -m tcid03 -q -r s --clean-alluredir --alluredir=reports/customers/test/allure-results
```

2. Copy the history (only after the test finishes, after a generating report):
    
   This injects previous history into your fresh results folder so the generator can see it.
```powershell
cp -r reports/allure-report/history reports/allure-results/
```

3. Generate the report:

   The Allure generator now combines the new results from Step 1 with the history from Step 2.
```powershell
allure generate reports/allure-results -o reports/allure-report --clean

allure generate reports/customers/test/allure-results -o reports/customers/test/allure-report --clean

```

4. Open Allure UI:

   Note: Use allure open if you already generated a static report in Step 3. Use allure serve if you want to 
   skip Step 3 and generate a temporary report in one go.
```powershell
allure open reports/allure-report 
# or 
allure serve reports/allure-results
```



**Why this is necessary:**

If you do not run this command before generating a new report:

Allure will treat every test run as a brand-new execution with no past.
The "Trend" graphs and "History" tabs in the UI will appear empty or only show the current run.
By copying the history folder into the new allure-results directory, the Allure generator can read those past data points and stitch them together with the new results to show progress over time.


## Summary
- `allure-pytest` (Python package) is the pytest adapter that writes raw Allure results (JSON + attachments) during test runs.  
- `allure` (Allure CLI / Allure2) is a separate Java-based command‑line tool that converts those raw results into an interactive HTML report.  
- Workflow:
  1. Run pytest with `--alluredir=...` → writes JSON result files.
  2. Run `allure generate` or `allure serve` → produces/serves HTML.

## Prerequisites
- Python 3.9+ (your virtualenv / project Python)  
  - Java JRE/JDK (8+).  **Java is required only to generate or serve HTML reports**, not to run pytest.
- Verify with:
  ```powershell
  java -version
  ```
- Allure Python adapter installed in your venv:
  - `allure-pytest` (installed via dev extras or direct pip)
- Allure CLI (Allure2) installed on your system PATH to produce HTML:
  ```powershell
  allure --version
  ```

## Install Allure Python adapter (in project venv)
- If you maintain dev extras in `pyproject.toml`, ensure `allure-pytest` is listed under:
  ```toml
  [project.optional-dependencies]
  dev = [
    "pytest>=8.3.5",
    "allure-pytest",
    ...
  ]
  ```
- Then, from project root:
  ```powershell
  python -m pip install --upgrade pip setuptools wheel
  python -m pip install -e ".[dev]"
  ```
  Or install adapter directly:
  ```powershell
  python -m pip install allure-pytest
  ```
- Verify adapter is installed (in the same venv used to run pytest):
  ```powershell
  python -m pip show allure-pytest
  pip list | Select-String allure    # PowerShell
  ```

## Install Allure CLI (Allure2)
Allure CLI is a Java tool and must be installed separately. Choose one method below.

### A) Manual download (no admin required) — recommended if Chocolatey/Scoop not available
1. Pick a release on GitHub: https://github.com/allure-framework/allure2/releases  
2. Download `allure-<version>.zip` and extract to e.g.:
   `C:\Users\<you>\tools\allure-<version>`  
3. Add `.../bin` to your PATH (User environment).  
4. Verify:
   ```powershell
   allure --version
   ```

### B) Chocolatey (requires admin)
```powershell
# Run in elevated PowerShell
choco install allure.commandline -y
allure --version
```

### C) Scoop (user-level)
```powershell
scoop install allure
allure --version
```

---

## Generate Allure results (pytest)
From project root (use your venv / activate `.venv`):

- (Optional) clear previous results:
  ```powershell
  Remove-Item .\allure-results\* -Recurse -Force
  ```
  
- Optional cleanup:
  ```powershell
   pytest --clean-alluredir --alluredir=reports/allure-results
  ```

- Run pytest and write results:
  ```powershell
  pytest --alluredir=reports/allure-results

  ```
  You can add markers, test selection and other flags (e.g. `-m tcid03`).

What gets written into `allure-results`:
- JSON files (e.g. `<uuid>-result.json`), `container.json`, `environment.properties` (optional), and attachments (txt/png). These are the inputs for the Allure CLI; pytest itself does NOT produce HTML.

---

## How Allure CLI reads results
Allure CLI will read the contents of the directory you point it at and build the report from the result files it finds there.

A few important details in simple terms:

- What it reads
  - Allure looks for Allure result files in the directory: result JSONs (e.g. `*-result.json`), `container.json`, `executor.json`, `environment.properties`, attachments (txt/png/etc.), `categories.json`, and optionally a `history/` folder.
  - It will ignore unrelated files that are not valid Allure result files.

- Where those files normally come from
  - `pytest` + `allure-pytest` produce those files when you run:
    ```powershell
    pytest --alluredir=<path>
    ```

- Path behaviour
  - You can give any path (it doesn’t have to be named `allure-results`).
  - Allure will read files inside that directory (and attachments in subfolders). If you give multiple result directories (e.g. `allure serve dir1 dir2 ...`), Allure will merge them into the report.

- What the command does
  - `allure serve` reads the result files, generates a temporary HTML report, starts a local web server and opens the report in your browser. It does not modify your original result files.
  - If there are no valid result files, it will report “No results found”.

- Useful extras
  - If you want a permanent site instead of a temporary server, use:
    ```powershell
    allure generate .\allure-results -o .\allure-report --clean
    start .\allure-report\index.html
    ```
  - If you want trend/history charts across runs, preserve and restore the `history` folder between runs (put it into `allure-results/history` before `generate`).

---

## View the report (two simple options)

1) Quick preview (one-step)
```powershell
allure serve .\allure-results
# or in my case:
allure serve reports\allure-results
```
- Behavior: generates a temporary HTML report, starts a local web server, and opens a browser. Use this for quick interactive view. The command blocks while the server runs (Ctrl+C to stop).

2) Generate static HTML (CI-friendly, shareable)
```powershell
allure generate reports/allure-results -o reports/allure-html --clean
start .\allure-report\index.html
```
- The `.\allure-report` folder is a static site you can upload or archive.


### ⚠️ One CRITICAL thing you must always do!
You must clean results between runs.
Otherwise Allure silently reuses cached widgets.

Always run:
```powershell
pytest --clean-alluredir --alluredir=reports/allure-results
```
and then:
```powershell
allure generate reports/allure-results -o reports/allure-report --clean
```

Without this, UI changes appear “ignored”.

---
## If index.html opens empty (file:// problem) — short explanation and fixes
Problem
- If you open `index.html` via `file:///.../allure-report/index.html`, the page may show only "loading" and never show suites. This happens because browsers block the report's JS from fetching JSON over `file://`.

Quick fixes (pick one)

A) Best for quick checks:
```powershell
allure serve .\allure-results
```
- Allure serves the report over HTTP — this avoids file:// restrictions.

B) Serve the already-generated static site locally:
```powershell
cd .\allure-report
python -m http.server 8000
Start-Process "http://localhost:8000"
```
Then Open http://localhost:8000 in the browser. This serves files over HTTP so the report will load correctly.
C) (Not recommended) Run Chrome with relaxed local file restrictions (temporary only):
```powershell
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --allow-file-access-from-files "file:///$PWD\allure-report\index.html"
```
- This weakens security; prefer serving over HTTP.

D) Share permanently (preferred for collaboration):
- Publish `allure-report` to a static host (GitHub Pages, Netlify, S3). These hosts serve files over HTTP and the report works.

---



## Useful extras

- Rename result folder (if you created it with a typo):
  ```powershell
  Rename-Item .\allure-resutls .\allure-results
  ```

- Add environment information to the report:
  - Create `allure-results/environment.properties` with lines like:
    ```
    ENV=staging
    BUILD=1234
    GIT_COMMIT=abcdef
    ```

- Preserve trend history across CI runs:
  - Archive `allure-report/history` after generating a report.
  - Before a new run, restore it into `allure-results/history` so the new generated report includes trends.

- Attachments in tests:
  ```python
  import allure
  allure.attach("text here", name="debug.log", attachment_type=allure.attachment_type.TEXT)
  allure.attach.file("path/to/screenshot.png", name="screenshot", attachment_type=allure.attachment_type.PNG)
  ```

---

## Quick verification checklist
1. Adapter installed in venv:
   ```powershell
   python -m pip show allure-pytest
   ```
2. Results were written by pytest:
   ```powershell
   dir .\allure-results\*.json
   dir .\allure-results
   ```
3. Allure CLI available:
   ```powershell
   allure --version
   ```
4. Generate / serve:
   ```powershell
   allure generate .\allure-results -o .\allure-report --clean
   start .\allure-report\index.html
   # or
   allure serve .\allure-results
   ```


## Easy permanent publish (GitHub Pages)
Use GitHub Actions to run tests, generate the static site, and push `allure-report` to the `gh-pages` branch. Then GitHub Pages serves it over HTTP.

Create `.github/workflows/allure-ghpages.yml` with this workflow:

```yaml
name: CI — tests + Allure → GitHub Pages

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  test-and-deploy:
    runs-on: ubuntu-latest
    permissions:
      contents: write

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install project & dev deps
        run: |
          python -m pip install --upgrade pip setuptools wheel
          python -m pip install -e ".[dev]"

      - name: Run pytest (collect Allure results)
        run: |
          mkdir -p ./allure-results
          pytest --alluredir=./allure-results

      - name: Set up Java (needed by Allure CLI)
        uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: '17'

      - name: Download Allure CLI
        run: |
          VERSION=2.20.1
          curl -L -o /tmp/allure.zip "https://github.com/allure-framework/allure2/releases/download/${VERSION}/allure-${VERSION}.zip"
          unzip -q /tmp/allure.zip -d /tmp
          echo "/tmp/allure-${VERSION}/bin" >> $GITHUB_PATH
          allure --version

      - name: Generate Allure static site
        run: |
          allure generate ./allure-results -o ./allure-report --clean

      - name: Publish to GitHub Pages (gh-pages branch)
        uses: peaceiris/actions-gh-pages@v3
        with:
          publish_dir: ./allure-report
          publish_branch: gh-pages
```

After the workflow runs, enable Pages (if needed) in repository Settings → Pages and set the source to the `gh-pages` branch (root). The report will be available at:
```
https://<your-username>.github.io/<repo-name>
```

---

## Quick checks (copy/paste)

- Confirm result files exist:
  ```powershell
  (Get-ChildItem .\allure-results\*.json -ErrorAction SilentlyContinue | Measure-Object).Count
  Get-ChildItem .\allure-results | Select-Object Name,Length
  ```

- Generate static site:
  ```powershell
  allure generate .\allure-results -o .\allure-report --clean
  ```

- Serve locally (test static site):
  ```powershell
  cd .\allure-report
  python -m http.server 8000
  Start-Process "http://localhost:8000"
  ```

- Quick dev preview:
  ```powershell
  allure serve .\allure-results
  ```

---

## Troubleshooting (simple)
- "No results found":
  - Make sure JSON files exist in the folder you passed to `allure generate`.
  - Make sure pytest used the same `--alluredir` path.

- `allure` not recognized:
  - Add Allure `bin` folder to PATH or run the full path:
    ```powershell
    "C:\Users\<you>\tools\allure-<version>\bin\allure.bat" serve .\allure-results
    ```

- Report shows "loading" or 404s when using `file://`:
  - Serve the folder over HTTP (use `allure serve` or `python -m http.server`) or publish to a static host.

- Preserve history across runs (optional):
  - Save `allure-report/history` after generation and restore it into `allure-results/history` before the next `allure generate` so trend charts persist.

---

If you want, I can:
- Add history-preservation to the GitHub Actions workflow.
- Create a small local script that regenerates results, rebuilds the report, and serves it.