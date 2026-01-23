# CUSTOMER HELPER - (TO CREATE PAYLOAD API CALL)

"""
RECOMMENDED DESIGN
✔ Helper: API logic only  --> Helper = talks to the API and DAO = talks to the database
✔ Tests: pass DAO dependencies through fixture
✔ No importing DAO inside helper!!! # dao must be provided by caller (fixture or mock)"
✔ No instantiating DAO inside helper
This is the enterprise-standard architecture.

HELPER METHODS SHOULD NOT SWALLOW DB ERRORS!
- When you're writing a test helper, your goal is: if something goes wrong → fail FAST and LOUD
- If the DAO throws:
    - connection errors
    - SQL syntax errors
    - logic errors
    - unexpected DB issues
You want the exception to propagate, because:
✔ It points directly to the failing line
✔ Pytest shows full traceback
✔ You don't hide root causes
✔ CI logs are cleaner
"""

from __future__ import annotations

import logging
from typing import Optional, List, Dict, Any

from jsonschema import validate

from tests.customers.schemas.customer import customer_schema, error_schema
from EcommerceAPI.src.utilities.pagination_utils import paginate_all_results
from EcommerceAPI.src.utilities.genericUtilities import generate_random_email_and_password
from EcommerceAPI.src.utilities.requestsUtility import RequestUtility
from EcommerceAPI.src.utilities.exceptions import UnexpectedStatusCodeError, SchemaValidationError
from EcommerceAPI.src.utilities.date_timestamp_utils import safe_parse_utc_datetime

logger = logging.getLogger(__name__)


# The global logging level and handlers are configured by the project's logging bootstrap (custom_logger).


class CustomersHelper(object):
    """
    CustomersHelper — helper for working with WooCommerce customer endpoints.

    This helper is intended to be used from tests and higher-level fixtures. It expects a configured RequestUtility
    instance to be injected (via the session-scoped pytest fixture `request_utility` defined in conftest). The helper
    provides convenience methods for creating, retrieving, deleting and listing customers, plus schema validation and
    DB-backed verification.

    Design notes / goals
    - Dependency injection: the helper does NOT create its own RequestUtility. A single shared, configured client
    should be created in conftest and passed in. This avoids duplicate config/auth and makes monkeypatching simpler.
    - Positive vs negative flows:
      - For positive flows use the helper methods (they assert expected status codes and return parsed JSON).
      - For negative flows (inspecting raw responses, headers, or unexpected codes), use RequestUtility.request_raw
        or RequestUtility.post(..., return_raw=True) from tests or the raw_api fixture.
    - Error handling: when RequestUtility raises UnexpectedStatusCodeError or SchemaValidationError the helper will
    attempt to extract and return the parsed JSON error body (response_json). This makes it easy for tests to assert
    on error payloads without parsing raw text from logs.
    - DB verification: helper can validate API results against the DB using CustomersDao.

    Usage example (positive flow):
        helper = CustomersHelper(request_utility=request_utility)
        customer = helper.create_customer(email="alice@example.com")
        assert customer["email"] == "alice@example.com"

    Usage example (negative flow):
        # In tests where you expect a 400 you can:
        err = helper.create_customer(email="", expected_status_code=400)
        assert err["code"] == "some_error_code"

    Note: adjust the DAO class name import if your repo uses a different class name (CustomersDao vs CustomersDAO).

    Some other features are:
        - Parameterizes test input: flexible for both positive and negative tests.
        - Schema validation: leverages jsonschema to ensure contract compliance.
        - Centralized assertions: domain assertions are not duplicated in tests.
        - Integration with utilities: uses pagination, random email/password, etc.
        - Logging: leverages logger for traceability.
    """

    ENDPOINT = "customers"

    def __init__(self, request_utility: RequestUtility):  # The type hint: RequestUtility suggests that this argument
        # should be an instance of a class named RequestUtility
        """
        Require an injected RequestUtility for consistent configuration and testability.
        Enforces injection (raises if None) and uses `self.request_utility` as the canonical attribute.

        Rationale:
          - Ensures helpers use the single, session-scoped RequestUtility from conftest
            (so auth/base_url/retries/monkeypatching behave consistently).

        Args:
            request_utility: A configured RequestUtility instance (session-scoped fixture).

        Raises:
            ValueError: If request_utility is None.
            TypeError: If request_utility is not an instance of RequestUtility.
        """
        if request_utility is None:
            raise ValueError(
                "CustomersHelper requires a RequestUtility instance. Pass `request_utility` from conftest."
            )
        if not isinstance(request_utility, RequestUtility):
            raise TypeError("request_utility must be an instance of RequestUtility")

        # Use the injected client
        self.request_utility = request_utility

    # ------------------------
    # Create / CRUD helpers
    # ------------------------
    def create_customer(
            self,
            email: Optional[str] = None,
            password: Optional[str] = None,
            expected_status_code: int = 201,
            auto_generate: bool = True,
            **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new customer via POST /customers.

        Behavior:
        - If auto_generate=True and email/password are not provided, a random email is generated, and a default
          password is used. This is convenient for positive tests that need unique customers.
        - On success (status == expected_status_code) returns parsed JSON (dict).
        - On failure where RequestUtility raises UnexpectedStatusCodeError or SchemaValidationError the helper
          will attempt to return the parsed error JSON (attached as `response_json` on the exception). If parsing
          fails or no JSON was attached, the original exception is re-raised.

        Args:
            email: Optional email to create the customer with.
            password: Optional password.
            expected_status_code: Expected HTTP status code for the positive flow (default 201).
            auto_generate: If true, auto-generate missing email/password for positive tests.
            **kwargs: Additional fields to include in the payload (billing, shipping, metadata, etc).

        Returns:
            dict: Parsed JSON response (success or error body).

        Raises:
            UnexpectedStatusCodeError, SchemaValidationError: Re-raised if no parsed error body is available.
            On expected failures (4xx/5xx) this helper will attempt to return the parsed error JSON
            attached by RequestUtility so tests can assert on error payloads.
        Note:
            - RequestUtility._handle_response already parses the response and attaches:
                - response_json (parsed body)
                - response (the raw requests.Response) when it raises UnexpectedStatusCodeError / SchemaValidationError.
            - Catching those exceptions and returning response_json is the cleanest way for helper methods to expose
            error bodies to tests (useful for negative assertions).
            - request_raw (or return_raw=True) is still useful when you need the raw Response object (headers, exact
            body bytes, status) or to bypass the exception-raising behavior entirely. Use request_raw from tests for
            advanced debugging; use the helper's exception-handling for common negative assertions.

            - Use request_raw (or RequestUtility.raw_post/raw_get) from tests when you need:
                - Access to response.headers, response.status_code, response.content in raw form, exact body bytes etc.
                - To avoid _handle_response raising (you want to inspect whatever the server returned regardless of
                expected_status_code).
            - Use return_raw=True on RequestUtility.post(...) only when you expect the response status to match
            expected_status_code but still want the raw Response or to bypass the exception-raising behavior entirely.
            - Use request_raw from tests for advanced debugging; use the helper's exception-handling for common
            negative assertions.

        """

        # Auto-generate credentials for convenience in positive flows. Skip auto-generation if explicitly turned
        # off (e.g., for negative test cases)
        if auto_generate:
            if not email:
                ep = generate_random_email_and_password()
                email = ep['email']
            if not password:
                password = 'Password1'

        # Build payload — skip adding None values
        # payload = {k: v for k, v in {'email': email, 'password': password, **kwargs}.items() if v is not None} # or:
        payload: Dict[str, Any] = {}
        if email is not None:
            payload['email'] = email
        if password is not None:
            payload['password'] = password
        # payload.update(kwargs) adds all those extra key-value pairs to the payload
        payload.update(kwargs)

        logger.debug(f"🟢 Creating customer with payload: {payload}")
        # logger.debug("🟢 Creating customer with payload keys: %s", list(payload.keys()))  # only keys no values

        # Make the request and handle expected failure shapes.
        # RequestUtility._handle_response will:
        # - attach parsed JSON to exception.response_json when it raises UnexpectedStatusCodeError/SchemaValidationError
        # - attach the raw requests.Response as exception.response
        try:
            return self.request_utility.post(self.ENDPOINT, payload=payload, expected_status_code=expected_status_code)
        except (UnexpectedStatusCodeError, SchemaValidationError) as e:
            # Log a short warning so the failure is visible in the structured logs (CustomFormatter will redact
            # sensitive info/fields).
            logger.warning("⚠️ Customer creation raised %s: %s", type(e).__name__, e)

            # Preferred: RequestUtility attaches parsed JSON to 'response_json' on the exception
            response_json = getattr(e, "response_json", None)

            # Fallback: if response_json not provided, try the raw response object and parse JSON
            if response_json is None:
                resp = getattr(e, "response", None)
                if resp is not None:
                    try:
                        response_json = resp.json()
                    except Exception as parse_err:
                        logger.exception(
                            "🚫 Failed to parse error response JSON from create_customer: %s", parse_err
                        )
                        # Re-raise the original exception since we cannot provide structured error body
                        raise

            # If we successfully retrieved parsed JSON, return it to the caller (useful for negative assertions)
            if response_json is not None:
                return response_json

            # Nothing parseable attached — re-raise so caller/test sees the original exception
            raise

    def call_get_customer_by_id(self, customer_id: int, expected_status_code: int = 200) -> Dict[str, Any]:
        """
         Retrieve a customer by their ID.

         Args:
             customer_id (int): Customer ID.
             expected_status_code (int): Expected HTTP status code.

         Returns:
             dict: Parsed customer JSON response.
         """
        # logger.debug(f"🟢 Calling 'Get Customer' for ID {customer_id}.")
        logger.debug("🟢 Calling 'Get Customer' for ID %s.", customer_id)
        return self.request_utility.get(f'{self.ENDPOINT}/{customer_id}', expected_status_code=expected_status_code)

    def call_delete_customer(self, customer_id: int, expected_status_code: int = 200) -> Dict[str, Any]:
        """
        Delete (hard delete_it.py) a customer by ID using force=true.

        Args:
            customer_id (int): Customer ID.
            expected_status_code (int): Expected HTTP status code.

        Returns:
            dict: Parsed JSON response from delete_it.py.
        """
        # Including into DELETE API the force=true query parameter otherwise it will be soft deleted and an error
        # triggered
        # logger.debug(f"🟢 Calling 'Delete Customer' for ID {customer_id}.")
        logger.debug("🟢 Calling 'Delete Customer' for ID %s.", customer_id)
        return self.request_utility.delete(f"{self.ENDPOINT}/{customer_id}", params={"force": True},
                                           expected_status_code=expected_status_code)

    # ------------------------
    # Listing / Pagination
    # ------------------------
    def call_list_all_customers_paginated(
            self,
            params: Optional[Dict[str, Any]] = None,
            max_pages: int = 1000,
            created_before: Optional[str] = None,
            created_after: Optional[str] = None,
            email: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch all customers using the shared paginate_all_results utility and optionally filter by creation
        dates (timestamps) and email.

        Args:
            params (Optional[dict]): Additional query parameters.
            max_pages (int): Max pages to fetch.
            created_before (Optional[str]): ISO 8601 timestamp to filter customers created before.
            created_after (Optional[str]): ISO 8601 timestamp to filter customers created after.
            email (Optional[str]): Exact email to filter by (case-insensitive).

        Returns:
            List[dict]: List of filtered customers.

        Notes:
            - paginate_all_results takes care of the page loop and returns a flat list.
            - This method applies post-fetch date filtering using safe_parse_utc_datetime.

        """

        logger.debug("🟢 Calling 'List All Customers' via pagination utility")

        # -------------------------------------------
        # 🔧 Prepare and sanitize query parameters
        # -------------------------------------------
        params = params.copy() if params else {}
        params.setdefault("per_page", 100)

        if email:
            params['email'] = email.lower()

        # -------------------------------------------
        # 🚀 Paginate through all pages using the utility
        # -------------------------------------------
        all_customers = paginate_all_results(
            request_utility=self.request_utility,
            endpoint=self.ENDPOINT,
            params=params,
            max_pages=max_pages
        )

        # -------------------------------------------
        # 🧹 Apply post-fetch filtering (date_created_gmt)
        # -------------------------------------------
        filtered_customers = []

        # Helper to convert ISO8601 string (with or without 'Z') into UTC-aware datetime with no microseconds
        parse_dt = safe_parse_utc_datetime

        # 🎯 Parse optional date filters using your util. These will hold our UTC-aware filter bounds Parse optional
        # date filters. # Properly validate ISO8601 format for date filters
        cutoff_before = cutoff_after = None

        # 🧪 Parse created_before as UTC-aware datetime (if provided)
        if created_before:
            try:
                cutoff_before = parse_dt(created_before)
            except ValueError:
                logger.warning("⚠️ Invalid 'created_before' format. Use ISO 8601.")
                return []

        # 🧪 Parse created_after as UTC-aware datetime (if provided)
        if created_after:
            try:
                cutoff_after = parse_dt(created_after)
            except ValueError:
                logger.warning("⚠️ Invalid 'created_after' format. Use ISO 8601.")
                return []

        # 🔍 Iterate through all fetched customers and apply time-based filters
        for customer in all_customers:
            created_gmt = customer.get("date_created_gmt")
            try:
                # ✅ Parse customer date as offset-aware datetime in UTC
                created_date = parse_dt(created_gmt) if created_gmt else None
                if created_date:
                    # ❌ Skip customer if it was created *after* the allowed upper bound
                    if cutoff_before and created_date >= cutoff_before:
                        continue
                    # ❌ Skip customer if it was created *before* the allowed lower bound
                    if cutoff_after and created_date <= cutoff_after:
                        continue
                # ✅ Keep customer — passed all time filters
                filtered_customers.append(customer)
            except Exception as e:
                logger.warning(f"⚠️ Could not parse 'date_created_gmt' for customer ID {customer.get('id')}: {e}")
                continue

        # 🔁 Shortcut: If filtering by email, return only first match
        if email and filtered_customers:
            # Return only the first match for email (assumes uniqueness)
            return [filtered_customers[0]]  # Assumes email is unique

        # ✅ Return all valid customers that passed date filter
        return filtered_customers

    # ------------------------
    # Schema Validation / Helpers
    # ------------------------
    @staticmethod
    def validate_customer_error_response_schema(response: dict) -> None:
        """
        📋 Validates the structure of a failed customer creation response using error schema.

        This static helper is useful in tests that assert on error payload structure.

        Args:
            response (dict): The JSON response from the API.

        Raises:
            AssertionError: If schema is invalid or required fields are missing.
        """
        # It uses: TypeError for incorrect types and AssertionError for missing fields. These are explicit and
        # semantically correct, which improves debugging and integrates better with pytest error reporting.
        # It avoids emojis, noisy messages and unnecessary verbosity.
        if not isinstance(response, dict):
            raise TypeError(f"Expected dict error response, got {type(response)}")
        if not response.get("code"):
            raise AssertionError(f"Missing 'code' in error response: {type(response)}")
        if not response.get("message"):
            raise AssertionError(f"Missing 'message' in error response: {type(response)}")
        validate(instance=response, schema=error_schema)
        # validate comes from the jsonschema Python library. It’s used to validate a JSON object against a predefined
        # schema.
        # instance: the actual JSON data you want to validate.
        # schema: the JSON Schema that defines the structure, required fields, types, and constraints.

    @staticmethod
    def validate_customer_response_schema(customer: dict) -> None:
        # It tells readers (and type checkers like mypy/pyright) that the function does not return anything.
        """
        Validates the structure of a single customer object against the customer JSON schema.
        Ensures your API returned valid data upon creation. Useful for unit test level.
        Immediately after customer creation, you're validating that the response structure from the creation endpoint
        is correct — i.e., all required fields (id, email, billing, shipping, etc.) are present and typed correctly.

         Args:
            customer (dict): Customer data to validate.

        Raises:
            jsonschema.ValidationError: If validation fails.
        """
        validate(instance=customer, schema=customer_schema)  # validate comes from the jsonschema Python library.
        # It’s used to validate a JSON object against a predefined schema.
        # instance: the actual JSON data you want to validate. In your code, customer is a Python dictionary
        # returned by the API.
        # schema: the JSON Schema that defines the structure, required fields, types, and constraints.
        # In your code, this is customer_schema.
        logger.info("📦 Customer response schema validated successfully")

    def assert_valid_customer_response(self, customer: dict) -> None:
        # It tells readers (and type checkers like mypy/pyright) that the function does not return anything.
        """
        ✅ Validates the structure and schema of a successful customer creation response (id, email, username present).
        Useful to centralize repeated checks across tests.

        - Raises AssertionError if invalid.
        - It ensures schema and domain rules are never forgotten or duplicated.
        - Centralizes your happy-path response validation in one place.
        - It reduces clutter in tests.
        - It honors separation of concerns (test ≠ validation logic).
        - It keeps your test code clean-no need to separately call the schema validator and then structural/assertion
        checks.

        Args:
            customer (dict): API response for created customer

        Raises:
            AssertionError or jsonschema.ValidationError on failure.
        """
        # ------------------------------------------------------------------
        # 📋 Schema Validation first (It checks that the POST response is valid)
        # ------------------------------------------------------------------
        self.validate_customer_response_schema(customer)

        if not isinstance(customer, dict):
            raise AssertionError(f"Response is not a dict. Got: {type(customer)}")

        if "id" not in customer or not isinstance(customer["id"], int):
            raise AssertionError(f"Invalid or missing customer ID. Got: {customer.get('id')}")
        if "email" not in customer or not isinstance(customer["email"], str):
            raise AssertionError(f"Invalid or missing email. Got: {customer.get('email')}")
        if "username" not in customer:
            raise AssertionError(f"Missing username. Got: {customer.get('username')}")

        logger.info("✅ Customer ID and email validated: %s, %s", customer["id"], customer["email"])

    def validate_customer_exists_and_matches(self, email: str, dao) -> None:
        """
        Checks that customer exists in GET /customers, validates schema, and matches DB record.

        After fetching data from the API with GET /customers you're validating that the customer returned by the GET
        API also conforms to the expected schema. Helps catch bugs where POST works fine, but GET returns malformed data
        Useful in integration and regression tests. What is result[0]? This refers to the first customer object
        returned from calling GET /customers, filtered by email.

        Args:
        email (str): Customer email to look up.
        dao: Data access object with get_customer_by_email(email) method.

        Raises:
            AssertionError: If validations fail.

        Note: dao must be provided by caller (fixture or mock)"
        """
        logger.debug("🟢 Validating existence of customer by email: %s", email)

        # 🔍 Call API to get customers
        result = self.call_list_all_customers_paginated(email=email)
        if not result:
            raise AssertionError(f"❌ Customer not found via API for email {email}")
        if result[0]["email"] != email:
            raise AssertionError(f"❌ Email mismatch for {email}")
        if "id" not in result[0] or not isinstance(result[0]["id"], int) or result[0]["id"] <= 0:
            raise AssertionError("❌ Invalid or missing customer ID")
        logger.info(f"✅ Assertion passed: Customer found calling API GET all customers paginated")

        # 📋 Validates API response schema using existing method GET /customers response (first result in search).
        self.validate_customer_response_schema(customer=result[0])

        # 🧠 Validate DB presence
        db_customer = dao.get_customer_by_email(email)
        if not db_customer:
            raise AssertionError(f"No DB record found for email {email}")
        if str(db_customer["ID"]) != str(result[0]["id"]):
            raise AssertionError("DB ID does not match API ID")
        if db_customer.get("user_email") != result[0]["email"]:
            raise AssertionError("DB email does not match API email")
        # logger.info(f"Assertion passed: Customer found in the DB and record validated for ID={db_customer['ID']}")
        logger.info("✅ Assertion passed: Customer record validated in DB for ID=%s", db_customer["ID"])

        # 🔍 Why both validations are needed?
        # Even though the schema is the same, you're validating:
        #    - That the create endpoint returns a well-formed customer
        #    - That the list/retrieve endpoint also returns that customer correctly
        # It’s entirely possible for one to pass and the other to fail if there's a bug in the API's data handling
        # logic (e.g., bad serialization in GET, missing fields in POST).


# # NOTE!! Keep this main block for local debugging only. Remove or guard it before committing if you prefer to avoid
# # leaving ad-hoc debug code in the main branch.
# if __name__ == "__main__":
#     # This block only runs when executing this file directly
#     from dotenv import load_dotenv
#     load_dotenv()  # <-- loads .env for manual debugging
#
#     from EcommerceAPI.src.utilities.requestsUtility import RequestUtility
#     ru = RequestUtility()
#     helper = CustomersHelper(request_utility=ru)
#     items = helper.call_list_all_customers_paginated()
#     breakpoint()  # Execution will pause here and drop into the debugger (pdb by default)
#     print(len(items))
#
