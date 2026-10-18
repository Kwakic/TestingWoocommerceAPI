# 🔐 Playwright Authentication & Page Object Architecture

This document explains how authentication, pytest fixtures, Playwright, and Page Objects are separated in the UI automation architecture.

The main design principle is:

> **Fixtures manage shared test infrastructure and predefined session setup. Page Objects encapsulate UI interactions. Tests orchestrate business workflows, including explicit authentication when it is part of the scenario.**

---

## 🏗️ Architecture Overview

Our Playwright architecture separates responsibilities into distinct layers. The diagram below shows the standard `customer_page` fixture path; authentication-focused tests may use an explicit login flow instead.

```text
STANDARD CUSTOMER-FIXTURE PATH

TEST
 │ requests customer_page
 ▼
PYTEST FIXTURE
 │ gets configured credentials
 │ creates CustomerLoginPage
 │ performs and verifies login
 ▼
CUSTOMER LOGIN PAGE
 │ Playwright interacts with UI
 ▼
WOOCOMMERCE
 │ authenticates customer
 │ establishes session/cookies
 ▼
AUTHENTICATED PAGE
 │
 ▼
TEST

AUTHENTICATION-FOCUSED PATH

TEST → dynamic_customer credentials → login helper / CustomerLoginPage
    → real WooCommerce login → assertions about login or session behavior
```

This separation keeps shared setup reusable without forcing every authentication scenario through the same fixture.

---

## 👥 Choosing a Customer Test Setup and Resource Owner

The UI suite supports predefined customer personas and dynamically provisioned customers. Choose the setup based on the behavior under test rather than automatically logging in for every test involving a customer.

### Predefined customer personas

Use `customer_page` when a test needs a standard authenticated customer session. Use a specialized seeded persona when its initial state is part of the scenario—for example, a customer without a saved address or a separate customer account whose profile can be modified independently.

### Dynamically provisioned customers

Use `dynamic_customer` when a test needs a disposable customer with unique credentials or a controlled starting point, but does not depend on a predefined persona. The fixture provisions the customer through the API and exposes the customer data and credentials to the test. API resource ownership remains responsible for cleanup.

A test may need an existing customer identity without needing to authenticate as that customer. For example, a duplicate-registration security test can submit an API-provisioned customer's existing email to the registration form without logging in.

### Customers created through the UI

When registration itself is the behavior under test, generate unique registration data and create the customer through the UI. Resolve the created customer resource and register it with `ui_resources` so UI cleanup removes it.

**Ownership rule:** each resource should have one cleanup owner. Do not register the same customer with both API and UI resource ownership.

### Authentication and provisioning are separate concerns

Provisioning answers, “Where did this customer come from, and who cleans it up?” Authentication answers, “Does this test need to be logged in, and how?” Choose each independently to match the scenario.

---

# 🔑 1. Customer Authentication Fixture

The `customer_page` fixture is responsible for providing an **authenticated browser page** using the configured customer credentials. It is the standard path for tests that need an authenticated customer session, but it is not the only supported authentication flow.

Conceptually:

```python
@pytest.fixture
def customer_page() -> Page:
    username = os.getenv("UI_CUSTOMER_USERNAME")
    password = os.getenv("UI_CUSTOMER_PASSWORD")

    if not username or not password:
        raise pytest.UsageError(
            "UI customer credentials are not configured."
        )

    login_page = CustomerLoginPage(page)

    login_page.login(username, password)

    return page
```

The fixture performs the following lifecycle:

```text
Get credentials
      ↓
Create CustomerLoginPage
      ↓
Call login()
      ↓
Return authenticated Page
      ↓
Test receives customer_page
```

### 🎯 Architectural responsibility

The fixture owns the **predefined authenticated-page setup** for tests that request `customer_page`. Tests that specifically exercise login behavior, Remember Me, or session persistence may orchestrate their own authentication flow and browser contexts.

The test should not need to know:

- where credentials come from
- how the login form works
- which locators are used
- how the login request behaves
- how redirects are handled
- how authentication is verified

It simply asks pytest for:

```python
customer_page
```

and receives an authenticated browser session.

---

# 🎭 2. `CustomerLoginPage` — Playwright Authentication

The `CustomerLoginPage` Page Object contains the actual login-form interactions. The standard `login_customer()` helper reuses the shared login flow, while scenarios such as Remember Me can call a specific Page Object method such as `login_with_remember_me()`. Tests may orchestrate these flows directly when authentication behavior is what they are testing.

For example, it defines Playwright locators:

```python
self.username_input = page.get_by_label(
    "Username or email address"
)

self.password_input = page.get_by_label(
    "Password"
)

self.login_button = page.get_by_role(
    "button",
    name="Log in",
    exact=True,
)
```

The `login()` method then uses Playwright:

```python
self.username_input.fill(username)
self.password_input.fill(password)
self.login_button.click(no_wait_after=True)
```

So Playwright is interacting with the **real WooCommerce UI**.

From a user's perspective, the process is:

```text
🌐 Open My Account
       ↓
⌨️ Enter username
       ↓
🔒 Enter password
       ↓
🖱️ Click Log in
       ↓
🛒 WooCommerce authenticates
       ↓
➡️ Redirect to My Account
```

There is no mocked authentication here.

We are exercising the real customer login flow.

---

# 🌐 3. Observing the HTTP Login Response

The login implementation also explicitly observes the HTTP response generated by the login action.

Instead of simply doing:

```python
self.login_button.click()
```

we tell Playwright to monitor the expected login request:

```python
with self.page.expect_response(
    lambda response: (
        response.request.method == "POST"
        and response.url.rstrip("/").endswith("/my-account")
    )
) as response_info:

    self.login_button.click(no_wait_after=True)
```

This allows the test framework to verify that the actual authentication request succeeded.

We then inspect the response:

```python
response = response_info.value

if response.status not in (200, 302):
    raise AssertionError(
        f"Customer login request failed with HTTP {response.status}."
    )
```

### 🔄 Redirect handling

If WooCommerce returns a redirect:

```python
redirect_url = response.headers.get("location")
```

we resolve it against the current page:

```python
absolute_redirect_url = urljoin(
    self.page.url,
    redirect_url,
)
```

and navigate to it:

```python
self.page.goto(
    absolute_redirect_url,
    wait_until="domcontentloaded",
)
```

This gives us explicit control over the authentication flow and avoids relying entirely on browser navigation timing.

---

# ✅ 4. Authentication Verification

After the login request and any redirect handling, the Page Object verifies that authentication actually succeeded:

```python
self.should_be_authenticated()
```

This is important.

A successful click does **not necessarily mean** a successful login.

The architecture therefore validates the complete flow:

```text
🖱️ Click Login
      ↓
📡 POST /my-account
      ↓
📊 Check HTTP response
      ↓
↪️ Handle redirect if required
      ↓
🔍 Verify authenticated state
      ↓
✅ Return authenticated Page
```

Only after these steps does the fixture return:

```python
customer_page
```

Therefore, when the test receives `customer_page`, it can assume that the customer authentication setup has already completed successfully.

---

# 🧩 5. Complete Responsibility Model

The architecture can be viewed as five distinct responsibilities:

| Layer | Responsibility |
|---|---|
| 🧪 **Test** | Defines the business scenario |
| 🔧 **Pytest Fixture** | Manages authentication/session setup |
| 📄 **CustomerLoginPage** | Encapsulates login UI interaction |
| 🎭 **Playwright** | Automates the browser and observes HTTP events |
| 🛒 **WooCommerce** | Performs the real authentication |

This separation is intentional.

---

# 🚫 6. Why Authentication Should Not Be Inside the Test

We could write a test like this:

```python
def test_customer_can_access_my_account(page):
    page.goto(...)

    page.get_by_label("Username").fill(...)
    page.get_by_label("Password").fill(...)

    page.get_by_role(
        "button",
        name="Log in"
    ).click()
```

But this makes the test responsible for authentication mechanics.

Every customer test would then need to know:

- the login URL
- username locator
- password locator
- login button locator
- login request behavior
- redirects
- authentication verification

That's unnecessary duplication.

Instead, we write:

```python
def test_customer_can_access_my_account(customer_page):
    ...
```

The meaning is much clearer:

> 🗣️ **"Give me a browser where a customer is already authenticated."**

The test can then concentrate on the actual business scenario.

---

# 📄 7. Page Objects Are Created by the Test

An important architectural distinction is that **authentication setup** and **page-object usage** are different concerns.

The fixture provides:

```python
customer_page
```

The test then creates the Page Object it actually needs:

```python
account_page = CustomerAccountPage(customer_page)
```

This is good Page Object Model practice for our architecture.

The flow becomes:

```text
🔐 customer_page
       │
       │ authenticated browser
       ▼
🧪 TEST
       │
       │ decides what it needs to test
       ▼
📄 CustomerAccountPage
```

The test is effectively saying:

> "I already have an authenticated customer browser. Now I want to test the My Account functionality."

That is a **business-level decision**, so the test is the appropriate place to instantiate the Page Object.

---

# 🚫 8. Why We Don't Create Every Page Object as a Fixture

We could create fixtures such as:

```python
@pytest.fixture
def customer_account_page(customer_page):
    return CustomerAccountPage(customer_page)
```

Then tests could use:

```python
def test_customer_can_access_my_account(
    customer_account_page,
):
    ...
```

However, as the UI suite grows, this can lead to a large `conftest.py`:

```text
conftest.py
 ├── customer_page
 ├── customer_account_page
 ├── shop_page
 ├── product_page
 ├── cart_page
 ├── checkout_page
 └── ...
```

This is not desirable.

### 🎯 `conftest.py` should primarily manage infrastructure

For example:

- 🌐 Browser
- 🧩 Browser context
- 📄 Page
- 🔐 Authentication
- 👤 User roles
- ⚙️ Environment configuration
- 🗃️ Test data setup

The test should choose which **business Page Object** it needs.

---

# 🧠 9. The Key Architectural Distinction

Think of the three layers like this.

### 🔧 Fixture

```python
customer_page
```

Means:

> **"Give me a browser session authenticated as a customer."**

---

### 📄 Page Object

```python
CustomerAccountPage(customer_page)
```

Means:

> **"Give me an interface to the My Account page in this browser session."**

---

### 🧪 Test

```python
account_page.should_be_authenticated()
```

Means:

> **"Verify the business behavior I care about."**

This creates a clean separation between **test infrastructure**, **UI mechanics**, and **business behavior**.

---

# 👤 10. Role-Based Authentication

The framework also uses role-based fixtures for common browser states. The examples below show the guest and customer roles; include `admin_page` in this model wherever it is part of the active fixture setup.

```python
UI_ROLE_FIXTURES = {
    "guest": "guest_page",
    "customer": "customer_page",
}
```

Conceptually:

```text
                    👤 UI ROLES
                        │
          ┌─────────────┴─────────────┐
          ▼                           ▼
     👻 guest_page              🛒 customer_page
          │                           │
          ▼                           ▼
 Unauthenticated Page          Playwright login
                                      │
                                      ▼
                             Authenticated Page
```

This architecture can later be extended:

```text
guest_page
    ↓
normal unauthenticated Page

customer_page
    ↓
customer login
    ↓
authenticated customer Page

admin_page
    ↓
WordPress admin login
    ↓
authenticated admin Page
```

The important point is that authentication remains centralized in the role-specific fixture layer.

---

# 🚀 11. Future Authentication Optimization

We are **not using Playwright `storage_state` yet**.

Currently:

```text
customer_page
      ↓
Real UI login
      ↓
Authenticated session
```

Every test that requests `customer_page` currently performs the real UI login flow. Tests that explicitly exercise authentication behavior may manage their own login flow and browser contexts.

This is intentional at this stage.

### Why?

It gives us a genuine **customer authentication contract**.

We are actually verifying:

```text
Credentials
    ↓
Login UI
    ↓
Authentication request
    ↓
WooCommerce authentication
    ↓
Session establishment
    ↓
Authenticated customer
```

For tests that do not need to validate login itself, reusable authentication state may later reduce repeated UI logins. Authentication-focused tests should continue to exercise the real login flow.

Later we could introduce:

```text
storage_state
     ↓
Reuse authenticated session
     ↓
Avoid repeated UI login
     ↓
Faster test execution
```

That becomes an **optimization for tests that do not target authentication**, rather than hiding authentication problems in tests that need to validate the login contract.

---

# 🏆 12. Final Architecture

The resulting architecture is:

```text
                         🧪 TEST
                           │
                           │ requests
                           ▼
                    🔧 PYTEST FIXTURE
                           │
                           │ customer_page
                           ▼
                  🔐 CUSTOMER LOGIN
                           │
                           │ Playwright
                           ▼
                    🖥️ WOOCOMMERCE UI
                           │
                           │ POST /my-account
                           ▼
                    📡 HTTP RESPONSE
                           │
                           │ 200 / 302
                           ▼
                    ↪️ REDIRECT / SESSION
                           │
                           ▼
                  ✅ AUTHENTICATED PAGE
                           │
                           ▼
                         🧪 TEST
                           │
                           │ creates required
                           │ Page Objects
                           ▼
                 📄 CUSTOMER ACCOUNT PAGE
                           │
                           ▼
                    💼 BUSINESS FLOW
```

### 🎯 Core principles

**1. Fixtures own authentication**

```text
customer_page → authenticated browser
```

**2. Page Objects own UI mechanics**

```text
CustomerLoginPage → login interactions
CustomerAccountPage → My Account interactions
```

**3. Tests own business workflows**

```text
test → decides which Page Objects it needs
```

**4. Playwright owns browser automation**

```text
fill()
click()
goto()
expect_response()
```

**5. WooCommerce provides the real system under test**

```text
Real UI
Real authentication
Real HTTP request
Real session
```

**6. Authentication optimization comes later**

```text
Real UI authentication
        ↓
Stable authentication contract
        ↓
Optional storage_state optimization
```

---

## 🧭 The Simple Mental Model

When working on the framework, remember:

```text
🔧 FIXTURE
"Prepare my environment."

        ↓

🔐 AUTHENTICATION
"Give me the correct user role."

        ↓

🌐 PAGE
"Give me the authenticated browser."

        ↓

📄 PAGE OBJECT
"Give me an interface to this UI."

        ↓

🧪 TEST
"Execute and verify the business scenario."
```

> **The test should describe what the user does — not how authentication or browser mechanics work.**

That is the core principle behind the current Playwright architecture.
