# 🎭 UI Testing Guide — TestEcommerceAPI

*How Playwright UI tests are structured, executed, and extended in this framework.*

> **Status:** Active development
> **Scope:** Playwright UI testing with pytest
> **Current UI coverage:** Guest storefront + authenticated customer flows + admin authentication
> **Browser coverage:** Chromium, Firefox, WebKit
> **Last updated:** 2026-09-22

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
              │      └── customer role + customer profiles
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

The framework distinguishes **access roles** from **customer profiles**.
They answer different questions and must not be mixed.

**Access role:**

```text
guest
customer
admin
```

An access role describes what kind of application actor the browser represents.
The role router maps these roles to role fixtures.

**Customer profile:**

```text
checkout_customer_page
no_address_customer_page
profile_customer_page
```

A customer profile is a dedicated test account used for a particular scenario.
It is test data, not an additional application role.

This separation prevents tests from hiding a concrete customer identity behind
a generic fixture name. For example, `customer_page` represents the `customer`
access role, while `checkout_customer_page` explicitly identifies the customer
profile used for checkout scenarios.

### Fixture responsibilities

| Fixture module | Responsibility |
|---|---|
| `browser.py` | Browser context and page lifecycle |
| `authentication.py` | Shared authentication implementation |
| `customers.py` | Customer access role and dedicated customer profiles |
| `admin.py` | Administrator authentication |

Authentication credentials are supplied through environment variables and are
never embedded in individual tests.

### Scenario state

Profile fixtures authenticate accounts; they do not seed or modify application
data. When a test requires a particular state, the test should establish that
state through the appropriate UI flow when the scenario itself is what is being
validated. This keeps tests independent from hidden setup performed by another
test.

### Persistent customer-data isolation

The three customer profiles exist because a fresh `BrowserContext` does not
isolate persistent WooCommerce data.

```text
Customer A
  → stable checkout customer
  → used by checkout E2E scenarios
  → must not be mutated by unrelated account-management tests

Customer B
  → dedicated address-management customer
  → used for shipping-address entry/edit scenarios

Customer C
  → mutable account/profile customer
  → used by profile/account-edit scenarios
```

Account-edit tests must use `profile_customer_page` rather than the stable
checkout profile. Authenticated checkout tests use `checkout_customer_page`; the checkout test enters its billing details.

This separation prevents persisted changes in one business scenario from
changing the starting state of another scenario.

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

# 8. 👥 Roles and Customer Profiles

The UI framework distinguishes **application access roles** from **test
customer profiles**.

### Access roles

```text
Guest
Customer
Admin
```

| Access role | Fixture | Meaning |
|---|---|---|
| Guest | `guest_page` | Unauthenticated storefront user |
| Customer | `customer_page` | Authenticated WooCommerce customer role |
| Admin | `admin_page` | Authenticated WordPress/WooCommerce administrator |

`customer_page` is a thin role-level fixture. It represents the generic
`customer` access role and delegates to the default checkout customer profile.
Tests that require a specific profile should request that profile directly.

### 🪪 Customer profiles

Customer profiles are three separate WooCommerce customer accounts. They are
not different application roles. All three fixtures do the same technical job:
they log in as a specific customer and return an authenticated Playwright page.

The reason for having three accounts is **test-data isolation**. Different UI
scenarios can change persistent customer data, so unrelated tests should not
share the same WooCommerce account.

| Profile | Fixture | What it is used for | What the test does |
|---|---|---|---|
| **Customer A** | `checkout_customer_page` | Checkout E2E scenarios | Enters **billing details on the Checkout page**, selects a payment method, places an order, and completes the checkout journey |
| **Customer B** | `no_address_customer_page` | Account address-management scenarios | Enters or changes the customer's **shipping address** through My Account → Addresses |
| **Customer C** | `profile_customer_page` | Account/profile-management scenarios | Changes customer account/profile information through My Account → Account Details |

---

#### 🔹 Customer A — `checkout_customer_page`

`checkout_customer_page` logs in as Customer A.

Customer A is the stable customer account reserved for **checkout E2E scenarios**. The
checkout test owns the billing state because entering billing details is part of the
checkout journey being tested.

For example:

```text
Customer A
    ↓
Login
    ↓
Shop → Product → Cart
    ↓
Checkout
    ↓
Enter billing details
    ↓
Select Cash on Delivery
    ↓
Place order
    ↓
Order confirmation
```

The fixture does **not** create a billing address. The test establishes the billing
details through the Checkout UI as part of the E2E flow.

> **Important:** Customer A could technically also manage an address through My Account.
> The profile is kept dedicated to checkout so that address-management tests do not
> mutate the persistent customer state used by checkout scenarios.

---

#### 🔹 Customer B — `no_address_customer_page`

`no_address_customer_page` logs in as Customer B.

Customer B is a dedicated customer account for **account address-management scenarios**.
The current coverage uses this account to create and modify a **shipping address**
through **My Account → Addresses**.

For example:

```text
Customer B
    ↓
Login
    ↓
My Account
    ↓
Addresses
    ↓
Enter / edit shipping address
    ↓
Save
    ↓
Verify the shipping address
    ↓
Verify persistence
```

The fixture itself does not remove, create, or verify an address. The test owns the
shipping-address operation and establishes the state it needs through the UI.

This account is kept separate from Customer A so that address-management tests do not
modify the persistent customer account used by checkout E2E scenarios.

> **Important:** Customer B is not a different WooCommerce role or capability.
> It is simply a dedicated test account whose persistent data is isolated for
> address-management scenarios.

---

#### 🔹 Customer C — `profile_customer_page`

`profile_customer_page` logs in as Customer C.

Customer C is a dedicated customer account for **account/profile-management scenarios**,
such as editing customer information through **My Account → Account Details**.

For example:

```text
Customer C
    ↓
Login
    ↓
My Account
    ↓
Account Details
    ↓
Change profile information
    ↓
Save
    ↓
Verify the updated information
```

Customer C is separate because these tests are expected to mutate persistent customer
profile information.

---

### 🤔 What the profile fixtures actually do

All three customer-profile fixtures follow the same pattern:

```text
fixture
   ↓
read that customer's credentials from environment variables
   ↓
open the customer login page
   ↓
log in
   ↓
return authenticated Page
```

They do **not**:

- create or delete users
- create billing or shipping addresses
- create products
- create orders
- reset customer data
- prepare scenario-specific application state

The test is responsible for performing the business operation it is intended
to validate.

This gives us a simple rule:

> **The fixture chooses the customer account. The test performs the business
> scenario.**

### Role router

The role router supports only access roles:

```python
UI_ROLE_FIXTURES = {
    "guest": "guest_page",
    "customer": "customer_page",
    "admin": "admin_page",
}
```

Customer profiles deliberately do not appear in this mapping. They are selected
explicitly by tests according to the state and business scenario being tested.


Building a permission/capability matrix and test meaningful combinations.

| Action | Guest | Customer | Admin |
| :--- | :---: | :---: | :---: |
| **View storefront** | ✓ | ✓ | ? |
| **View product** | ✓ | ✓ | ? |
| **Add to cart** | ✓ | ✓ | ? |
| **Checkout** | ? | ✓ | ? |
| **View own orders** | ✗ | ✓ | ✗ |
| **Edit own account** | ✗ | ✓ | ✗ |
| **Manage products** | ✗ | ✗ | ✓ |
| **Manage orders** | ✗ | ✗ | ✓ |


---

# 9. 🌱 UI Test Data

UI/E2E tests use deterministic baseline WooCommerce products and dedicated
persistent customer accounts.

The framework separates **environment prerequisites** from **test data**:

- `scripts/setup.sh` configures the WooCommerce application and required
  environment capabilities, including Cash on Delivery for checkout.
- `scripts/seed_test_products.sh` provisions deterministic baseline products.
- `scripts/seed_test_users.sh` provisions the persistent UI customer accounts.
- Individual tests create or modify only the scenario-specific state they are
  responsible for validating.

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
- restores missing or broken featured images
- avoids duplicate baseline products

For featured images, the seed checks the physical attachment file as well as
the WordPress thumbnail metadata. If WordPress still has the attachment record
but the image file is missing, the repository-local fixture is imported again
and assigned to the product.

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

### Persistent customer profiles

The UI seed also provisions the dedicated customer accounts used by the fixture
architecture:

```text
Customer A → checkout_customer_page
Customer B → no_address_customer_page
Customer C → profile_customer_page
```

These accounts are environment-level test prerequisites. The seed script creates
missing users or reuses existing users and does not create billing addresses,
orders, products, or other scenario state.

A test establishes scenario-specific state through the UI when that state is
part of the behavior being validated. For example, the authenticated checkout
flow enters billing details during the checkout scenario rather than depending
on a pre-seeded billing address.

This deliberately avoids external image URLs and makes clean local and CI
bootstrap reproducible.

A clean environment can therefore be rebuilt with:

```bash
make clean
make run
```

### Environment prerequisites for UI checkout

Some UI scenarios depend on WooCommerce configuration rather than test data.
Cash on Delivery (COD) is enabled by `scripts/setup.sh` during WooCommerce
bootstrap so checkout tests have a deterministic payment method available.

The payment method is therefore an **environment prerequisite**, not something
configured by a Playwright test, fixture, or Page Object.

The baseline setup flow is:

```text
make run
  │
  ├── Docker / WooCommerce bootstrap
  │     ├── WordPress
  │     ├── WooCommerce
  │     ├── Cash on Delivery
  │     ├── customer registration
  │     └── REST / GraphQL configuration
  │
  ├── seed_test_products.sh
  ├── seed_test_users.sh
  ├── framework + Playwright installation
  ├── pre-commit Git hook installation
  └── pytest
```

The repository Git hook is installed automatically during the local installation
flow. Developers do not need to run `pre-commit install` manually after a fresh
clone.

The local Git hook and CI validation are separate concerns: the hook provides
fast developer feedback, while GitHub Actions executes the authoritative CI
checks directly.

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

# 16. 🛡️ Stability and Cross-Browser Rules

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
- Authenticated customer checkout with billing details entered during the flow
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
admin are implemented. Dedicated customer profiles are selected explicitly for
scenarios that require particular persisted account state.

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
5. **Customer profile** — when persistent customer state matters, the test uses
   the appropriate explicit profile.
6. **Markers** — the test carries the markers needed for suite classification and
   execution.
7. **Comments** — comments explain non-obvious intent or constraints rather than
   repeating the code.
8. **Scenario state** — required state is established explicitly rather than
   relying on another test to run first.
9. **Assertions** — assertions verify meaningful business outcomes.
10. **Cross-browser behavior** — the test does not contain unnecessary
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
  ├── Deterministic UI seed data
  └── Customer A/B/C profile isolation
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
Customer B address-management scenarios
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
11. **UI/E2E baseline data must be deterministic and reproducible.**
12. **Customer profiles isolate persistent account state between unrelated scenarios.**
13. **Tests establish scenario-specific state explicitly when that state is part of the behavior under test.**
14. **Do not create generic abstractions until real reuse exists.**
15. **Use API + UI E2E coverage selectively for important cross-layer business
    flows.**
16. **Keep browser-specific workarounds narrow, evidence-based and local to the
    affected interaction.**
17. **Keep application environment prerequisites in bootstrap/setup, not in UI
    tests or Page Objects.**
18. **Keep persistent baseline data in seed scripts and establish scenario-specific
    state inside the test when that state is part of the behavior under test.**

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

This document should evolve together with the UI layer as roles, customer
profiles, business flows, components and E2E scenarios are implemented.
