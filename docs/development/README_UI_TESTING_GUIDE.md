# 🎭 UI Testing Guide — TestEcommerceAPI

*How Playwright UI tests are structured, executed, and extended in this framework.*

> **Status:** Active development
> **Scope:** Playwright UI testing with pytest
> **Current UI coverage:** Guest storefront + authenticated customer flows + admin authentication
> **Browser coverage:** Chromium, Firefox, WebKit
> **Last updated:** 2026-10-17

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
8. [Roles and Fixture Selection](#8--roles-and-fixture-selection)
9. [UI Test Data and Resource Ownership](#9--ui-test-data-and-resource-ownership)
10. [Browser Selection](#10--browser-selection)
11. [Local Execution](#11--local-execution)
12. [CI Execution](#12--ci-execution)
13. [Allure Reporting](#13--allure-reporting)
14. [Authentication](#14--authentication)
15. [API + UI E2E Strategy](#15--api--ui-e2e-strategy)
16. [Stability and Cross-Browser Rules](#16--stability-and-cross-browser-rules)
17. [Current Coverage](#17--current-coverage)
18. [Test Review and Maintenance](#18--test-review-and-maintenance)
19. [Development Roadmap](#19--development-roadmap)
20. [Golden Rules](#20--golden-rules)

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
  ├── customer_page
  │
  └── admin_page
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
├── fixtures/
│   ├── browser.py
│   ├── authentication.py
│   ├── customers.py
│   ├── resources.py
│   ├── admin.py
│   └── __init__.py
│
├── pages/
│   ├── authentication/
│   │   ├── customer_login_page.py
│   │   ├── customer_password_recovery_page.py
│   │   └── customer_registration_page.py
│   │
│   ├── account/
│   │   ├── customer_account_page.py
│   │   ├── customer_account_details_page.py
│   │   └── customer_address_page.py
│   │
│   ├── catalog/
│   │   ├── shop_page.py
│   │   └── product_page.py
│   │
│   ├── shopping/
│   │   ├── cart_page.py
│   │   ├── checkout_page.py
│   │   ├── guest_checkout_page.py
│   │   └── order_confirmation_page.py
│   │
│   ├── admin/
│   │   ├── admin_login_page.py
│   │   └── admin_dashboard_page.py
│   │
│   └── common/
│       └── home_page.py
│
├── components/
│   └── site_header.py
│
├── data/
│   └── images/
│       ├── ui-seed-album.jpg
│       ├── ui-seed-beanie.jpg
│       └── ui-seed-hoodie.jpg
│
├── tests/
│   ├── authentication/
│   │   ├── test_customer_login.py
│   │   ├── test_customer_login_security.py
│   │   ├── test_customer_password_recovery.py
│   │   ├── test_customer_registration.py
│   │   ├── test_customer_registration_security.py
│   │   └── test_customer_session_security.py
│   │
│   ├── account/
│   │   ├── test_customer_account.py
│   │   ├── test_customer_account_details.py
│   │   └── test_customer_address.py
│   │
│   ├── catalog/
│   │   ├── test_product_discovery.py
│   │   └── test_product_review.py
│   │
│   ├── shopping/
│   │   ├── cart/
│   │   │   ├── test_add_product_to_cart.py
│   │   │   ├── test_apply_coupon.py
│   │   │   ├── test_cart_contents.py
│   │   │   ├── test_remove_product_from_cart.py
│   │   │   └── test_update_cart_quantity.py
│   │   │
│   │   └── checkout/
│   │       ├── test_customer_checkout.py
│   │       ├── test_guest_can_checkout.py
│   │       └── test_order_confirmation.py
│   │
│   ├── admin/
│   │   └── test_admin_authentication.py
│   │
│   └── home/
│       └── test_home_page.py
│
└── conftest.py
```

Tests are organized by **business domain**, not by the Page Object they happen
to use.

For example, a test that validates adding a product to the cart belongs under
`cart/`, even though it may use both `ShopPage` and `ProductPage`.

---

# 4. 🧩 Fixture Architecture

The UI fixture implementation is split by responsibility rather than keeping
all fixtures in one large `conftest.py`.

The repository root `conftest.py` is the single pytest plugin composition
point. It loads both the framework/API plugins and the UI fixture modules.

UI fixture implementation is organized under `tests/ui/fixtures/`.

```text
root conftest.py
       │
       ├── EcommerceAPI/plugins/
       │      └── API/framework plugins
       │
       └── tests/ui/fixtures/
              │
              ├── browser.py
              │      └── browser context + page lifecycle
              │
              ├── authentication.py
              │      └── shared authentication implementation
              │
              ├── customers.py
              │      └── customer authentication + dynamic_customer
              │
              ├── resources.py
              │      └── cleanup registration for UI-created resources
              │
              └── admin.py
                     └── administrator authentication
```

### Browser lifecycle

The `browser` fixture is supplied by `pytest-playwright`. The UI fixture layer
creates a fresh `BrowserContext` and `Page` for every test.

```text
pytest-playwright
      │
      ▼
   browser
      │
      ▼
   context       ← fresh per test
      │
      ▼
    page         ← fresh per test
```

The `BrowserContext` is the primary isolation boundary for cookies, local
storage, session state, and authentication state.

### Authentication and access roles

The framework distinguishes an application access role from the customer data
used by a scenario.

**Access roles:**

```text
guest
customer
admin
```

The role router maps the role to its authentication fixture. For most customer
UI tests, use `dynamic_customer` to create a disposable customer through the API
and `login_customer` to authenticate it. The older `customer_page` and named
customer-profile fixtures remain available for scenarios that explicitly
require a configured persistent account; they are not the default for tests
where an API-created customer is sufficient.

### Fixture responsibilities

| Fixture module | Responsibility |
|---|---|
| `browser.py` | Browser context and page lifecycle |
| `authentication.py` | Shared authentication implementation |
| `customers.py` | Customer authentication helpers and API-created `dynamic_customer` fixture |
| `resources.py` | Function-scoped cleanup for resources created through the UI |
| `admin.py` | Administrator authentication |

Administrator and explicitly configured persistent-profile credentials are
supplied through environment variables and are never embedded in individual
tests. Credentials for `dynamic_customer` are generated by the test-data
architecture and passed to `login_customer` for that test.

### Scenario state

Authentication fixtures establish browser identity; they should not hide
scenario-specific application setup. Use API fixtures to create prerequisite
customers or products, and use the UI for the business behavior under test.
This keeps setup explicit and avoids dependencies on another test or shared
mutable data.

### Test-data lifecycle and parallel execution

A fresh `BrowserContext` isolates browser state, but it does **not** isolate
persistent WooCommerce data. Tests must therefore own the application resources
they create and must not depend on another test having run first.

For customer-based UI tests, use `dynamic_customer` by default when an existing
customer is a prerequisite rather than the behavior under test:

```text
Test invocation
    ↓
dynamic_customer (function-scoped)
    ↓
CustomerBuilder → CustomerFactory → CustomerProvisioner
    ↓
WooCommerce API creates a unique customer
    ↓
shared_api_resources registers API ownership
    ↓
Test logs in and exercises the UI
    ↓
API lifecycle deletes the customer during teardown
```

Each test invocation—including each parametrized case—gets its own customer.
Do not also register this customer with `ui_resources`: API-created resources
must have one cleanup owner.

When customer creation itself is the behavior under test, the UI must create the
customer and `ui_resources` owns cleanup. See [UI Test Data and Resource
Ownership](#9--ui-test-data-and-resource-ownership).

The same principle applies to products: use `create_valid_product` to create a
product through the API for the current test, instead of selecting a shared
seeded product. API-created products are registered with the API cleanup
lifecycle. Tests should use unique resources and avoid shared mutable application
state so they can run independently and in parallel.

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
├── authentication/
├── account/
├── catalog/
├── shopping/
│   ├── cart/
│   └── checkout/
├── admin/
└── home/
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

# 8. 👥 Roles and Fixture Selection

The UI framework distinguishes an application's access role from the test data
used by a scenario.

### Access roles

```text
Guest
Customer
Admin
```

| Access role | Typical setup | Meaning |
|---|---|---|
| Guest | `guest_page` | Unauthenticated storefront user |
| Customer | `dynamic_customer` + `login_customer` | A unique API-created customer authenticated for this test |
| Admin | `admin_page` | Authenticated WordPress/WooCommerce administrator |

`customer_page` and the named customer-profile fixtures remain available for
scenarios that explicitly need a configured persistent profile. They should not
be the default for ordinary customer UI tests when the required customer can be
created through the API.

### Choosing the right customer setup

Use `dynamic_customer` when the test needs an existing customer to exercise a
different behavior—for example, login, account navigation, editing account
details, or saving a shipping address.

```python
def test_customer_can_open_account(
    page,
    ui_base_url,
    dynamic_customer,
):
    login_customer(
        page,
        ui_base_url,
        dynamic_customer.username,
        dynamic_customer.password,
    )
    # Exercise and assert the account behavior.
```

This fixture creates a customer through the established API test-data
architecture, retains the generated credentials for login, validates the
creation response, and registers the customer with API cleanup. The test must
not register that same customer with `ui_resources`.

Use `ui_resources` when the UI creates the resource because creation through
the UI is the behavior being tested—for example, customer registration.

```text
Registration test
    ↓
UI creates customer
    ↓
Resolve customer ID via API using the unique email
    ↓
ui_resources registers ("customers", customer_id)
    ↓
UI resource teardown deletes the customer
```

The registration test should generate a unique email, create the account through
the registration Page Object, resolve the newly created customer ID with
`customer_resource_helper`, and register that ID using `ui_resources`.

### Resource ownership rule

**One resource, one creation path, one cleanup owner.**

- API-created customer or product → API lifecycle registration and cleanup.
- UI-created customer → `ui_resources` registration and cleanup.
- Never register the same resource with both cleanup systems.
- Never delete shared/seeded data through test cleanup.
- A test must create the resources it needs; it must not rely on test order or
  another test's setup.

---

# 9. 🌱 UI Test Data and Resource Ownership

The default pattern for UI tests is **per-test resource creation through the
API for prerequisites**, with the UI reserved for the behavior being tested.
This makes the suite more deterministic and suitable for parallel execution.

## Customers: `dynamic_customer`

Use `dynamic_customer` when a test needs a customer but is not testing customer
creation. The function-scoped fixture:

1. Builds valid customer data with `CustomerBuilder` and its factory defaults.
2. Creates the customer through `CustomerProvisioner` and the API helper.
3. Validates the HTTP status and returned customer data.
4. Retains the generated password and returned username for browser login.
5. Registers the customer with `shared_api_resources` for API lifecycle cleanup.
6. Returns a `DynamicCustomer` object containing the customer data and login
   credentials.

Each test invocation gets its own disposable customer. For a parametrized test,
each case should receive its own fixture instance. Use the centralized
`login_customer(page, ui_base_url, username, password)` helper to authenticate
that customer.

Do not use `dynamic_customer` for a registration test: that would mean the
customer already exists before the registration form is submitted.

## Products: `create_valid_product`

Use `create_valid_product` whenever a UI test needs a product as a prerequisite,
including product discovery and product-review scenarios. The fixture uses the
existing product architecture:

```text
Test
    ↓
create_valid_product(...)
    ↓
ProductBuilder → ProductFactory
    ↓
ProductProvisioner → ProductsHelper → Products API
    ↓
Validate HTTP 201 and product response
    ↓
Register product with shared API cleanup
    ↓
Return validated product dictionary
    ↓
UI test opens the created product
    ↓
API lifecycle deletes the product during teardown
```

The fixture is function-scoped and accepts scenario-specific product fields.
Supply explicit fields when the test asserts them—for example, a product name,
SKU, or price. Let the factory provide valid defaults for fields that are not
important to the scenario.

Example:

```python
def test_product_is_visible_in_catalog(create_valid_product, page, ui_base_url):
    product = create_valid_product(
        name="UI discovery product",
        regular_price="19.99",
    )

    # Navigate to the created product using the existing Page Objects.
    # Assert the product details that are part of this scenario.
```

This is a usage pattern; adapt the fields and navigation to the existing
builders and Page Objects. Do not hard-code a seeded product name, SKU, or ID
as the prerequisite for a test when the product can be created through this
fixture.

## UI-created resources: `ui_resources`

`ui_resources` is separate from the API resource lifecycle. It is a
function-scoped registrar for resources that a UI test itself creates. During
teardown it deletes only explicitly registered IDs, using the framework's
entity cleanup implementation.

The registration flow is:

```text
Registration test
    ↓
Generate a unique email
    ↓
UI creates customer
    ↓
customer_resource_helper resolves customer ID via API
    ↓
ui_resources("customers", customer_id)
    ↓
Function teardown deletes the UI-created customer
```

`customer_resource_helper` only resolves a UI-created customer; it does not
create the customer or own cleanup. The `ui_resources` fixture owns the
registration and teardown.

## Seeded data and environment prerequisites

Seed scripts can remain useful for bootstrapping an environment, manual
exploration, or explicitly documented environment-level prerequisites. However,
ordinary UI tests must not rely on a shared seeded customer or product when the
same prerequisite can be created through the API.

In particular:

- Product discovery and product-review tests should create their own product
  through `create_valid_product`, not depend on a shared seeded album.
- Customer login and account tests should use `dynamic_customer` when they need
  a customer created for that test.
- Registration tests create the customer through the UI and register it with
  `ui_resources`.
- Shared seeded resources are not registered for deletion and must not be
  mutated as a side effect of unrelated tests.

Creating a product per test does not automatically clean up other resource
types created by that test. For example, if a UI review creates a review record,
the test suite must account for review cleanup separately; deleting the product
alone should not be assumed to remove every related record.

## Parallel-execution rules

- Use function-scoped test data for mutable prerequisites.
- Generate unique business identifiers (email, SKU, names, review text) where
  collisions are possible.
- Give each test its own customer and product when those resources can be
  created through the API.
- Keep browser sessions isolated with a fresh `BrowserContext` per test.
- Avoid shared mutable resources, fixed test identities, and test-order
  dependencies.
- Give each resource exactly one cleanup owner.
- Verify parallel behavior by running the relevant suite with pytest-xdist;
  syntax checks alone do not establish parallel safety. For example:

  ```bash
  pytest -m ui --browser chromium -n 2
  ```

## Bootstrap and application configuration

`scripts/setup.sh` configures WooCommerce capabilities required by the
environment, such as Cash on Delivery for checkout. Seed scripts may provision
baseline data for other explicitly documented purposes, but they are not a
substitute for per-test resource setup.

The repository-local image fixtures under `tests/ui/data/images/` may still be
used by seed/bootstrap tooling. Tests that create products through the API
should not require those seeded products to exist.

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
dependencies and Playwright browser binaries, provisions the required UI/E2E
environment and baseline data, installs the repository pre-commit Git hook, and
runs pytest.

The WooCommerce bootstrap also enables Cash on Delivery so checkout tests have
a deterministic payment method available. The Git hook is a local developer
tool; CI does not depend on `.git/hooks` and runs its checks directly.

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

# 13. 📊 Allure Reporting

All UI tests are integrated with the framework's existing Allure reporting
architecture.

Local UI execution writes raw results to:

```text
reports/allure-results/
```

A local HTML report can be previewed with:

```bash
allure serve reports/allure-results
```

### CI reporting

The UI workflow is a separate reporting domain from the API entity matrix.

On `main` and manual runs, the browser matrix produces:

```text
Chromium ──► ui-chromium-allure-results
Firefox  ──► ui-firefox-allure-results
WebKit   ──► ui-webkit-allure-results
```

The reusable Allure workflow merges the available browser result sets and
generates one standalone UI report:

```text
report-ui
    ↓
/ui/
```

The public QA Portal therefore exposes:

```text
🎭 UI / Playwright    TIER: CRITICAL
    └── Allure Report
```

### CI artifacts

Each browser execution also produces browser-specific diagnostic artifacts:

```text
ui-<browser>-structured-logs
ui-<browser>-junit-results
```

This keeps browser failures traceable to the exact CI execution while still
providing one combined Allure view for the UI suite.

### Browser coverage

The CI policy remains:

| Execution | Browser | Mode |
|---|---|---|
| Pull request | Chromium | Headless |
| Push to `main` | Chromium + Firefox + WebKit | Headless |
| Manual `workflow_dispatch` | Chromium + Firefox + WebKit | Headless |

The UI suite remains intentionally separate from the API entity matrix. A UI
test can carry a `smoke` marker for classification, but it is executed by
`ui.yml` rather than duplicated into the API Smoke workflow.

# 14. 🔐 Authentication

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

Current implementations:

```text
guest
customer
admin
```

Customer authentication uses the WooCommerce My Account flow.
Admin authentication uses the WordPress login flow.

Authentication-specific mechanics belong in role fixtures and dedicated Login
Page Objects. Credentials belong in environment configuration and CI secrets,
not source control.

Role fixtures keep authentication out of business-focused tests.

---

# 15. 🔄 API + UI E2E Strategy

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
Test creates a unique Product through the API
        ↓
Storefront UI opens that Product
        ↓
User performs the behavior under test
        ↓
API verifies resulting state when useful
        ↓
API lifecycle cleans up the Product
```

Use `create_valid_product` for product prerequisites in UI tests. The test
should use the returned product data to navigate to the resource it created,
not look up a shared seeded product by a fixed name or ID.

This approach avoids forcing the UI to perform expensive setup steps that the
API can perform more reliably.

Not every test should become an E2E test.

Use E2E coverage for important business flows where validating the complete
cross-layer behavior provides additional confidence.

---

# 16. 🛡️ Stability and Cross-Browser Rules

UI tests must be written so that the same business scenario can run across
supported browsers.

Prefer:

- stable user-facing locators
- deterministic, per-test test data
- unique identifiers for resources created during a test
- explicit waits based on observable UI state
- Page Object abstractions for interaction
- isolated BrowserContexts
- one cleanup owner for every created resource
- business-focused assertions

Avoid:

- arbitrary `sleep()` calls
- brittle CSS/XPath selectors when better locators exist
- test ordering dependencies
- shared mutable customer/product data when a per-test resource can be created
- duplicate cleanup registration for the same resource
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

# 17. 📊 Current Coverage

The current UI suite includes browser-tested coverage for:

- Home page loading and navigation
- Product discovery
- Adding a product to the cart
- Removing a product from the cart
- Updating cart quantity
- Applying a coupon
- Cart contents
- Product review submission
- Customer authentication
- Customer account navigation
- Customer shipping-address save and modification
- Customer Account details update
- Customer Account details required-field validation
- Guest checkout
- Authenticated customer checkout with explicitly established checkout state
- Order confirmation
- Admin authentication

The current role coverage is:

```text
Guest      ✅
Customer   ✅
Admin      ✅
```

The current browser coverage is:

```text
Chromium   ✅
Firefox    ✅
WebKit     ✅
```

The UI test suite uses role-oriented fixtures and pytest parametrization where
the same business behavior is valid for multiple roles. Guest, customer and
admin are implemented. Customer tests should create their own customer through
`dynamic_customer` whenever a persistent seeded identity is not specifically
required by the scenario.

---

# 18. 🔍 Test Review and Maintenance

The UI suite is maintained incrementally. Existing tests are reviewed one at a
time before new scenarios or abstractions are added.

For each test, verify:

1. **Business purpose** — the test clearly describes the behavior being validated.
2. **Location** — the test is under the correct business-domain directory.
3. **Name** — the test name describes the expected user-visible behavior.
4. **Role** — the test uses the correct access role (`guest`, `customer`, or
   `admin`).
5. **Test data** — use `dynamic_customer` for API-created customer prerequisites
   and `create_valid_product` for API-created product prerequisites; avoid
   shared seeded resources when a per-test resource is feasible.
6. **Markers** — the test carries the markers needed for suite classification and
   execution.
7. **Comments** — comments explain non-obvious intent or constraints rather than
   repeating the code.
8. **Scenario state** — required state is established explicitly rather than
   relying on another test to run first.
9. **Resource ownership** — each created resource has exactly one cleanup owner;
   API-created resources use API cleanup and UI-created resources use `ui_resources`.
10. **Parallel safety** — the test uses unique data and does not depend on
    execution order or shared mutable resources.
11. **Assertions** — assertions verify meaningful business outcomes.
12. **Cross-browser behavior** — the test does not contain unnecessary
    browser-specific branching.

The goal is not to maximize the number of UI tests. The goal is a small,
maintainable set of reliable tests that clearly communicate business behavior.

---

# 19. 🛣️ Development Roadmap

The UI layer is being expanded incrementally for learning value and meaningful
business coverage rather than maximum test count.

Planned sequence:

```text
Current
  │
  ├── Guest storefront coverage
  ├── Customer authentication + account flows
  ├── Admin authentication
  ├── Feature-based Page Objects
  ├── Browser matrix
  ├── Per-test API-created customers and products
  └── Explicit resource ownership and parallel-safe cleanup
       │
       ▼
Current stabilization work
       ├── Review each existing test
       │     ├── correct business-domain location
       │     ├── explicit test name
       │     ├── appropriate pytest markers
       │     ├── useful comments
       │     ├── correct role/profile fixture
       │     └── explicit scenario state
       │
       ▼
Customer checkout stabilization
       ├── environment payment prerequisites
       ├── billing-address entry
       └── cross-browser checkout validation
       │
       ▼
Per-test product creation for catalog/review tests
       │
       ▼
Review-resource cleanup and parallel validation
       │
       ▼
CartItem component
       │
       ▼
API + UI cross-layer E2E
       │
       ▼
Targeted Playwright concepts
       ├── network interception / mocking
       ├── APIRequestContext
       └── tracing and debugging
```

The roadmap intentionally favors a small number of meaningful scenarios over a
large UI regression suite.

For example, the checkout flow should validate a complete business journey such
as:

```text
Product
   ↓
Cart
   ↓
Checkout
   ↓
Place order
   ↓
Order confirmation
```

Cross-layer E2E can then extend that journey with API or backend verification.

Components should be introduced only when a real repeated UI element justifies
them. `CartItem` is the first planned component because a cart naturally
contains multiple instances of the same product-row structure.

The framework should not introduce abstractions merely because they may be
needed later.

Add Page Objects, components and fixtures when real test coverage provides a
clear reason for them.

# 20. 🎯 Golden Rules

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
11. **Create customer and product prerequisites per test through the API when creation is not the behavior under test.**
12. **Use `dynamic_customer` for API-created customer prerequisites and `create_valid_product` for API-created product prerequisites.**
13. **Use `ui_resources` only for resources created through the UI; never register one resource with both cleanup systems.**
14. **Use unique resources and identifiers so tests can run independently and in parallel.**
15. **Tests establish scenario-specific state explicitly when that state is part of the behavior under test.**
16. **Do not create generic abstractions until real reuse exists.**
17. **Use API + UI E2E coverage selectively for important cross-layer business
    flows.**
18. **Keep browser-specific workarounds narrow, evidence-based and local to the
    affected interaction.**
19. **Keep application environment prerequisites in bootstrap/setup, not in UI
    tests or Page Objects.**
20. **Keep environment prerequisites in bootstrap scripts; do not use shared seeded
    customers or products when a per-test API-created resource can satisfy the test.**
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

This document should evolve with the UI layer as business flows, resource
ownership, parallel execution, components and E2E scenarios are implemented.
