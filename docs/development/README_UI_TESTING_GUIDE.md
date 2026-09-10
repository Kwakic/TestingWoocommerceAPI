# 🎭 UI Testing Guide — TestEcommerceAPI

*How Playwright UI tests are structured, executed, and extended in this framework.*

> **Status:** Active development
> **Scope:** Playwright UI testing with pytest
> **Current UI coverage:** Guest storefront flows
> **Browser coverage:** Chromium, Firefox, WebKit
> **Last updated:** 2026-09-10

This document is the canonical guide for the browser-based UI test layer.

It explains where UI tests, Page Objects, components, fixtures, data, and
browser configuration belong, and how local and CI execution are expected to
work.

For the API test architecture, see
`README_TEST_DEVELOPMENT_GUIDE.md` and `README_ARCHITECTURE.md`.

---

## 📋 Contents

1. [Purpose and Scope](#1--purpose-and-scope)
2. [UI Architecture](#2--ui-architecture)
3. [Repository Structure](#3--repository-structure)
4. [Fixture Architecture](#4--fixture-architecture)
5. [Page Objects](#5--page-objects)
6. [Components](#6--components)
7. [Test Organization](#7--test-organization)
8. [Roles](#8--roles)
9. [UI Test Data](#9--ui-test-data)
10. [Browser Selection](#10--browser-selection)
11. [Local Execution](#11--local-execution)
12. [CI Execution](#12--ci-execution)
13. [Authentication](#13--authentication)
14. [API + UI E2E Strategy](#14--api--ui-e2e-strategy)
15. [Stability and Cross-Browser Rules](#15--stability-and-cross-browser-rules)
16. [Current Coverage](#16--current-coverage)
17. [Development Roadmap](#17--development-roadmap)
18. [Golden Rules](#18--golden-rules)

---

# 1. 🎯 Purpose and Scope

The UI layer validates the application from a real browser rather than through
the REST or GraphQL APIs.

The framework uses:

- **Playwright** for browser automation
- **pytest** as the test runner
- **Page Objects** for page-level UI interactions
- **pytest fixtures** for browser/context/page lifecycle and role setup
- **pytest markers** to select UI tests
- **Allure** for test reporting
- **Dockerized WooCommerce** as the local and CI application environment

The UI layer is intentionally kept separate from the API entity matrix.

The API suite answers questions such as:

> Did the REST or GraphQL API behave correctly?

The UI suite answers questions such as:

> Can a user complete the expected browser-based business flow?

---

# 2. 🏗️ UI Architecture

The current browser lifecycle is:

```text
pytest
  │
  ▼
pytest-playwright browser fixture
  │
  ▼
Browser
  │
  ▼
BrowserContext
  │
  ▼
Page
  │
  ├── guest_page
  │
  ├── customer_page       (future)
  │
  └── admin_page          (future)
       │
       ▼
   Page Object
       │
       ▼
   Components
       │
       ▼
   WooCommerce UI
```

The key isolation boundary is the `BrowserContext`.

Each test receives a fresh context and therefore an isolated browser session.
The page is then created inside that context.

The UI `conftest.py` does not launch a hard-coded browser. The browser itself
is provided by `pytest-playwright`, allowing the selected browser to come from
the pytest command line.

---

# 3. 📁 Repository Structure

The UI layer follows a dedicated structure:

```text
tests/ui/
│
├── config/
│   └── config_ui.py
│
├── pages/
│   ├── home_page.py
│   ├── shop_page.py
│   ├── product_page.py
│   └── ...
│
├── components/
│   └── ...
│
├── data/
│   ├── images/
│   │   ├── ui-seed-album.jpg
│   │   ├── ui-seed-beanie.jpg
│   │   └── ui-seed-hoodie.jpg
│   └── ...
│
├── tests/
│   ├── home/
│   │   └── test_home_page.py
│   ├── products/
│   │   ├── test_product_discovery.py
│   │   └── test_product_review.py
│   └── cart/
│       ├── test_add_product_to_cart.py
│       ├── test_remove_product_from_cart.py
│       ├── test_update_product_quantity.py
│       ├── test_apply_coupon.py
│       └── test_cart_contents.py
│
└── conftest.py
```

Tests are organized by **business domain**, not by the Page Object they happen
to use.

For example, a test that validates adding a product to the cart belongs under
`cart/`, even though it may use both `ShopPage` and `ProductPage`.

---

# 4. 🧩 Fixture Architecture

`tests/ui/conftest.py` owns test-session browser resources and role-oriented
fixtures.

The current lifecycle is:

```text
pytest-playwright
      │
      ▼
    browser
      │
      ▼
    context
      │
      ▼
     page
      │
      ▼
  guest_page
      │
      ▼
  ui_role_page
```

### Browser

The `browser` fixture is supplied by `pytest-playwright`.

The framework does not manually call `sync_playwright()` or hard-code
Chromium in the UI fixture layer.

### Browser Context

The framework creates a new `BrowserContext` for every test.

```python
@pytest.fixture
def context(browser: Browser) -> Generator[BrowserContext, None, None]:
    context = browser.new_context()

    try:
        yield context
    finally:
        context.close()
```

This provides isolation for cookies, local storage, session state, and future
authentication state.

### Page

Each test receives a fresh page created from its isolated context.

### Role fixtures

Role fixtures provide the business identity of the browser session.

Current role:

```text
guest
```

Future roles:

```text
customer
admin
```

Tests should use the role abstraction rather than managing authentication
themselves.

---

# 5. 📄 Page Objects

Page Objects own page-level UI interaction.

A Page Object should contain:

- locators
- page-level actions
- page-level verification
- navigation between pages where appropriate

A Page Object should not contain:

- test-specific business scenarios
- pytest fixture lifecycle
- credentials
- unrelated domain workflows
- large amounts of reusable cross-page logic

Example:

```python
class ProductPage:
    def __init__(self, page: Page):
        self.page = page

    def add_to_cart(self) -> None:
        self.add_to_cart_button.click()
```

The test should describe the business scenario:

```python
def test_add_product_to_cart(ui_role_page):
    product_page = ProductPage(ui_role_page)

    # business scenario
    ...
```

Keep Page Objects focused enough that their behavior remains understandable
when the UI grows.

---

# 6. 🧱 Components

Components are intended for **real, reusable UI regions** that appear on more
than one page.

Examples may include:

```text
Header
NavigationMenu
CartItem
ProductCard
Pagination
```

A component is more specific than a generic utility/helper.

For example, a `CartItem` component can encapsulate the controls and
locators for one product row in the cart:

```python
class CartItem:
    def __init__(self, page: Page, product_name: str):
        self.page = page
        self.product_name = product_name
```

A Page Object can then expose the component when the UI actually requires it:

```python
class CartPage:
    def item(self, product_name: str) -> CartItem:
        return CartItem(self.page, product_name)
```

Do not create components speculatively.

A component should exist because a UI region is genuinely reused or complex
enough to justify its own abstraction.

---

# 7. 🧪 Test Organization

UI tests are grouped by the **business behavior under test**.

Current intended organization:

```text
tests/ui/tests/
├── home/
│   └── test_home_page.py
│
├── products/
│   ├── test_product_discovery.py
│   └── test_product_review.py
│
└── cart/
    ├── test_add_product_to_cart.py
    ├── test_remove_product_from_cart.py
    ├── test_update_product_quantity.py
    ├── test_apply_coupon.py
    └── test_cart_contents.py
```

Avoid creating folders based purely on implementation details such as:

```text
pages/
components/
buttons/
links/
```

Those belong in the implementation layer, not in the test organization.

---

# 8. 👥 Roles

The UI framework is designed around three application roles:

```text
Guest
Customer
Admin
```

### Guest

Unauthenticated storefront user.

This is the currently implemented role.

### Customer

Authenticated WooCommerce customer.

The intended flow is:

```text
customer_page
     │
     ▼
Customer Login Page
     │
     ▼
WooCommerce My Account
```

### Admin

Authenticated WordPress/WooCommerce administrator.

The intended flow is:

```text
admin_page
     │
     ▼
WordPress Login
     │
     ▼
WordPress / WooCommerce Admin
```

Tests should use pytest parametrization where the same business behavior is
valid for multiple roles instead of duplicating the entire test:

```text
test_add_product_to_cart[guest]
test_add_product_to_cart[customer]
```

Role-specific authentication belongs in the role fixtures, not in individual
tests.

---

# 9. 🌱 UI Test Data

UI/E2E tests use deterministic baseline WooCommerce products.

Current baseline products:

```text
UI Seed - Album
UI Seed - Beanie
UI Seed - Hoodie
```

These are provisioned by:

```text
scripts/seed_test_products.sh
```

The seed operation is idempotent.

It:

- creates missing baseline products
- reuses existing products
- restores missing featured images
- avoids duplicate baseline products

## 🖼️ Local image fixtures

The baseline product images are committed to the repository:

```text
tests/ui/data/images/
├── ui-seed-album.jpg
├── ui-seed-beanie.jpg
└── ui-seed-hoodie.jpg
```

The seed script imports these local files into WordPress through WP-CLI.

This deliberately avoids external image URLs and makes clean local and CI
bootstrap reproducible.

A clean environment can therefore be rebuilt with:

```bash
make clean
make run
```

---

# 10. 🌐 Browser Selection

The supported Playwright browsers are:

```text
Chromium
Firefox
WebKit
```

Browser selection is explicit.

Local examples:

```bash
pytest -m ui --browser chromium
pytest -m ui --browser firefox
pytest -m ui --browser webkit
```

For interactive debugging:

```bash
pytest -m ui --browser chromium --headed
```

Without `--headed`, Playwright runs headlessly.

Browser selection is part of execution configuration, not test logic.

Tests should not contain browser-specific branching such as:

```python
if browser == "webkit":
    ...
```

unless a genuine browser-specific platform issue has been demonstrated and
the workaround is kept at the appropriate Page Object or infrastructure
boundary.

---

# 11. 💻 Local Execution

The recommended local bootstrap remains:

```bash
make run
```

This prepares the Dockerized WooCommerce environment, installs the framework
dependencies and Playwright browser binaries, seeds the deterministic UI/E2E
data, and runs pytest.

After the environment is prepared, browser-specific UI runs can be executed
directly:

```bash
pytest -m ui --browser chromium
pytest -m ui --browser firefox
pytest -m ui --browser webkit
```

For debugging:

```bash
pytest -m ui --browser chromium --headed
```

A developer can therefore choose the browser and headed/headless mode locally
without changing framework code.

---

# 12. 🤖 CI Execution

UI tests run through:

```text
.github/workflows/ui.yml
        │
        ▼
reusable-test-runner.yml
        │
        ▼
pytest-playwright
        │
        ▼
Selected browser
```

The reusable runner exposes the browser explicitly and passes it to pytest:

```text
--browser <browser>
```

The CI job installs the selected Playwright browser before execution:

```bash
python -m playwright install --with-deps "${{ inputs.browser }}"
```

## Browser execution policy

The current CI policy is:

| Execution | Browser | Mode | Purpose |
|---|---|---|---|
| Pull request | Chromium | Headless | Fast feedback |
| Push to `main` | Chromium + Firefox + WebKit | Headless | Cross-browser coverage |
| Manual `workflow_dispatch` | Chromium + Firefox + WebKit | Headless | Full UI validation |
| Local debugging | Developer choice | Headed or headless | Debugging |

The pull-request workflow intentionally does not run the complete browser
matrix. This keeps normal feedback faster and reduces unnecessary CI cost.

CI does not pass `--headed`; headless execution is therefore the default.

The UI workflow is intentionally separate from the API entity matrix.

---

# 13. 🔐 Authentication

Authentication is part of the **role fixture architecture**.

Tests must not contain:

```python
page.fill("username", ...)
page.fill("password", ...)
```

for shared test credentials.

Instead:

```text
Test
  ↓
Role fixture
  ↓
Login Page Object
  ↓
Authenticated BrowserContext
  ↓
Test
```

Current implementation:

```text
guest
```

Planned implementations:

```text
customer
admin
```

Customer authentication will use the WooCommerce My Account flow.

Admin authentication will use the WordPress login flow.

Credentials belong in environment configuration and CI secrets, not source
control.

The authentication implementation should be added only when authenticated UI
coverage is introduced.

---

# 14. 🔄 API + UI E2E Strategy

The UI layer is also designed to participate in meaningful cross-layer E2E
tests.

The preferred pattern is:

```text
API
 │
 ├── create/prepare state
 │
 ▼
UI
 │
 ├── exercise user-facing workflow
 │
 ▼
API
 │
 └── verify resulting backend state
```

For example:

```text
API creates Product
        ↓
Admin UI verifies Product
        ↓
Storefront Customer interacts with Product
        ↓
API verifies resulting state
```

This approach avoids forcing the UI to perform expensive setup steps that the
API can perform more reliably.

Not every test should become an E2E test.

Use E2E coverage for important business flows where validating the complete
cross-layer behavior provides additional confidence.

---

# 15. 🛡️ Stability and Cross-Browser Rules

UI tests must be written so that the same business scenario can run across
supported browsers.

Prefer:

- stable user-facing locators
- deterministic test data
- explicit waits based on observable UI state
- Page Object abstractions for interaction
- isolated BrowserContexts
- business-focused assertions

Avoid:

- arbitrary `sleep()` calls
- brittle CSS/XPath selectors when better locators exist
- test ordering dependencies
- shared browser state
- browser-specific code without evidence of a genuine platform difference
- large generic utility abstractions created before reuse exists

## Browser-specific exceptions

A browser-specific workaround is acceptable when:

1. the behavior has been reproduced;
2. the application behavior is understood;
3. the workaround is kept at the narrowest appropriate boundary.

For example, the current WordPress product-review form performs a native POST
followed by a 302 redirect. WebKit can hang while waiting for the native
navigation to complete automatically.

The current `ProductPage.submit_review()` implementation therefore validates
the POST/302 response and explicitly navigates to the redirect URL.

This workaround belongs in `ProductPage` because it is specific to that UI
interaction. It is not a generic browser-navigation helper.

---

# 16. 📊 Current Coverage

The current UI suite includes browser-tested coverage for:

- Home page loading and navigation
- Product discovery
- Adding a product to the cart
- Removing a product from the cart
- Product review submission

The current role coverage is:

```text
Guest      ✅
Customer   ⏳
Admin      ⏳
```

The current browser coverage is:

```text
Chromium   ✅
Firefox    ✅
WebKit     ✅
```

The UI test suite currently uses pytest parametrization for the role abstraction
where applicable, with the guest role implemented first.

---

# 17. 🛣️ Development Roadmap

The UI layer is being expanded incrementally.

Planned sequence:

```text
Current
  │
  ├── Guest storefront coverage
  ├── Page Objects
  ├── Browser matrix
  └── Deterministic UI seed data
       │
       ▼
Customer authentication
       │
       ▼
Admin authentication
       │
       ▼
Authenticated role matrix
       │
       ▼
Cart / checkout expansion
       │
       ▼
Meaningful API + UI E2E flows
       │
       ▼
Additional reusable components
```

The framework should not introduce abstractions merely because they may be
needed later.

Add Page Objects, components and fixtures when real test coverage provides a
clear reason for them.

---

# 18. 🎯 Golden Rules

1. **Tests describe business behavior.**
2. **Page Objects own page-level UI interaction.**
3. **Components represent genuinely reusable UI regions.**
4. **Fixtures own browser lifecycle, isolation and authentication.**
5. **Tests do not manage browser lifecycle.**
6. **Tests do not contain shared credentials.**
7. **UI tests are organized by business domain.**
8. **Browser selection belongs to execution configuration.**
9. **Local developers choose the browser and headed/headless mode explicitly.**
10. **CI keeps PR execution fast and uses the full browser matrix after changes
    reach `main`.**
11. **UI/E2E baseline data must be deterministic and reproducible.**
12. **Do not create generic abstractions until real reuse exists.**
13. **Use API + UI E2E coverage selectively for important cross-layer business
    flows.**
14. **Keep browser-specific workarounds narrow, evidence-based and local to the
    affected interaction.**

---

## 📚 Related Documentation

### Framework architecture

- `docs/project-structure/README_project_navigation.md`
- `docs/development/README_TEST_DEVELOPMENT_GUIDE.md`
- `docs/development/README_ARCHITECTURE.md`
- `docs/development/README_ARCHITECTURE_QUICK_START.md`

### API testing

- `docs/development/README_GRAPHQL_TESTING_GUIDE.md`
- `docs/framework/README_ENVIRONMENT_CONFIG_GUIDE.md`

### CI and infrastructure

- `docs/ci/README_CI_ARCHITECTURE.md`
- `docs/ci/README_ENV_AND_CI.md`
- `docs/ci/README_DOCKER_INFRASTRUCTURE.md`
- `docs/ci/README_ALLURE.md`

### UI implementation

```text
tests/ui/
```

This document should evolve together with the UI layer as authenticated roles,
additional business flows, components and E2E scenarios are implemented.
