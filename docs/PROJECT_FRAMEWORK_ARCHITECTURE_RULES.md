## 🔐 Golden Rules (NOT violate these)

1. Plugins must not import from tests/ at runtime
(TYPE_CHECKING hack is OK — you already do this correctly)
2. Fixtures own lifecycle & path (happy vs raw)
3. Helpers do NOT manage fixtures
4. Tests do NOT import helpers
5. Rollback must be trivial (git revert one file)


### 🧱 Design contract (locked)

    Tests
      ↓
    Create_valid_customer fixture
      ↓
    CustomersHelper (customers_api=CustomersApi)
      ↓
    validators (schema + asserts)
      ↓
    CustomersApi.create_customer()
      ↓
    RequestUtility


### 🧱 Target internal structure (after refactor)

      CustomersHelper
       ├── owns CustomersApi
       ├── calls api.create_customer(...)
       ├── calls api.list_customers(...)
       ├── asserts schema + business rules
       └── compares API ↔ DB

CustomersApi:
* HTTP only
* expected_status logic delegated to RequestUtility
* no assertions


Note: CustomersHelper no longer calls request_utility.post("/customers", …) directly
It delegates HTTP calls to CustomersApi

### The actual chain (before AND after)
    CustomersHelper
      → CustomersApi
          → RequestUtility.post()
              → _handle_response()
                  → response.json()
                  → return dict

### 🔁 Final responsibility map (clear + clean)

| Concern                  | Owner                             |
| ------------------------ | --------------------------------- |
| auto_generate            | **CustomersHelper**               |
| payload assembly         | **CustomersHelper**               |
| expected_status_code     | **Helper → API → RequestUtility** |
| HTTP                     | **CustomersApi**                  |
| retries / auth / logging | **RequestUtility**                |
| JSON parsing             | **RequestUtility**                |
| schema validation        | **RequestUtility**                |
| error JSON extraction    | **CustomersHelper**               |
| test ergonomics          | **CustomersHelper**               |


fdd