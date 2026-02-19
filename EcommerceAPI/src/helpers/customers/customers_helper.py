# CUSTOMER HELPER - (TO CREATE PAYLOAD API CALL)

from __future__ import annotations

import logging
from typing import Optional, List, Dict, Any

from EcommerceAPI.src.api.customers.customers_api import CustomersApi
from EcommerceAPI.src.utilities.pagination_utils import paginate_all_results
from EcommerceAPI.src.utilities.genericUtilities import generate_random_email_and_password
from EcommerceAPI.src.utilities.exceptions import UnexpectedStatusCodeError, SchemaValidationError
from EcommerceAPI.src.utilities.date_timestamp_utils import safe_parse_utc_datetime

from EcommerceAPI.src.validators.customers.customer_schema_validator import validate_customer_response_schema

from EcommerceAPI.src.validators.customers.customer_assertions import (
    assert_valid_customer_in_api,
    assert_valid_customer_matches_db,
    assert_single_customer_by_email,
)

logger = logging.getLogger(__name__)


# The shared logging level and handlers are configured by the project's logging bootstrap (custom_logger).


class CustomersHelper(object):
    """
    Domain-level orchestration layer for Customers.

    Responsibilities:
    -----------------
    ✔ Build payloads (including auto-generation ergonomics)
    ✔ Delegate HTTP calls to CustomersApi (NO raw HTTP here)
    ✔ Handle positive + expected-negative flows
    ✔ Delegate validation to validators layer
    ✔ Return parsed JSON (success OR error body)

    Non-responsibilities:
    ---------------------
    ✘ No raw HTTP calls
    ✘ No schema logic (delegated to validators)
    ✘ No business assertions inside this file
    ✘ No fixtures
    ✘ No DB access
    """

    ENDPOINT = "customers"

    def __init__(self, customers_api: CustomersApi):
        """
        Args:
            customers_api: Positive-path API client (wraps RequestUtility)

        """
        # Use the injected client
        self.customers_api = customers_api

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
        Create a customer via CustomersApi.

        Behavior:
        - Auto-generate email/password for positive tests
        - Supports negative testing via expected_status_code
        - On success → return parsed JSON dict
        - On expected failure:
            - return parsed error JSON (if available)
            - otherwise re-raise original exception

        Args:
            email: Optional email
            password: Optional password
            expected_status_code: Expected HTTP status
            auto_generate: Auto-generate credentials for positive tests
            **kwargs: Additional payload fields

        Returns:
            dict: Parsed API response (success or error JSON)

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
        # --------------------------------------------------------------
        # Auto-generate credentials (POSITIVE FLOW ERGONOMICS)
        # --------------------------------------------------------------
        if auto_generate:
            if not email:
                ep = generate_random_email_and_password()
                email = ep['email']
            if not password:
                password = 'Password1'

        # --------------------------------------------------------------
        # Build payload (skip None values)
        # --------------------------------------------------------------
        # Skip auto-generation if explicitly turned off (e.g., for negative test cases where you don't need these)

        # payload = {k: v for k, v in {'email': email, 'password': password, **kwargs}.items() if v is not None} # or:
        payload: Dict[str, Any] = {}
        if email is not None:
            payload['email'] = email
        if password is not None:
            payload['password'] = password
        # payload.update(kwargs) adds all those extra key-value pairs to the payload
        payload.update(kwargs)

        # logger.debug(f"🟢 Creating customer with payload: {payload}")
        logger.debug("⚙️ Creating customer with payload keys: %r", list(payload.keys()))

        # --------------------------------------------------------------
        # Call API + preserve negative-path behavior
        # --------------------------------------------------------------
        # RequestUtility._handle_response will:
        # - attach parsed JSON to exception.response_json when it raises UnexpectedStatusCodeError/SchemaValidationError
        # - attach the raw requests.Response as exception.response

        # The exception logic is:
        #  - Tries to extract response_json from exception
        #  - Falls back gracefully if parsing fails
        #  - Re-raises only when truly necessary
        #  - One responsibility: return response OR fail loudly

        try:
            return self.customers_api.create_customer(payload=payload, expected_status_code=expected_status_code)
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

    def update_customer(
            self,
            customer_id: int,
            payload: Optional[Dict[str, Any]] = None,
            expected_status_code: int = 200,
            **kwargs,
    ) -> Dict[str, Any]:
        """
        Update customer fields.
        - Accepts full payload (same as API)
        - Does NOT modify payload
        - It supports positive + negative flows (This allows: update_customer(customer_id, first_name=None))

        Supports:
        - payload: for full/complex updates
        - kwargs: for simple updates
        """
        final_payload: Dict[str, Any] = {}

        # ✅ Start with payload if provided
        if payload:
            final_payload.update(payload)

        # ✅ Then merge kwargs (same behavior as create_customer)
        final_payload.update(kwargs)

        logger.debug("🟢 Updating customer %s with payload keys: %r", customer_id, list(final_payload.keys()))

        try:
            return self.customers_api.update_customer(
                customer_id=customer_id,
                payload=final_payload,
                expected_status_code=expected_status_code,
            )

        except (UnexpectedStatusCodeError, SchemaValidationError) as e:
            logger.warning("⚠️ Customer update raised %s: %s", type(e).__name__, e)

            response_json = getattr(e, "response_json", None)

            if response_json is None:
                resp = getattr(e, "response", None)
                if resp is not None:
                    response_json = resp.json()

            if response_json is not None:
                return response_json

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
        return self.customers_api.get_customer(customer_id, expected_status_code=expected_status_code)

    def call_get_customer_by_email(
            self,
            email: str,
            *,
            expected_status_code: int = 200,
    ) -> Dict[str, Any]:
        """
        Retrieve a customer by email.

        Returns:
            dict: First matching customer (assumes email uniqueness)

        Raises:
            AssertionError if no customer found.
        """
        logger.debug("🟢 Calling 'Get Customer by Email' for %s.", email)

        result = self.customers_api.get_customer_by_email(
            email=email,
            expected_status_code=expected_status_code,
        )

        return result[0]  # Woo returns list → we take first

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
        return self.customers_api.delete_customer(
            customer_id,
            force=True,
            expected_status_code=expected_status_code
        )

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

        Responsibilities:
        - Delegates HTTP to CustomersApi layer (via request_utility)
        - Applies post-fetch filtering
        - Does NOT perform schema validation here

        Notes:
            - paginate_all_results takes care of the page loop and returns a flat list.
            - This method applies post-fetch date filtering using safe_parse_utc_datetime.

        """

        logger.debug("⚙️ Calling 'List All Customers' via pagination utility")

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
        # Use injected API client's request utility
        all_customers = paginate_all_results(
            request_utility=self.customers_api.request_utility,
            endpoint=self.customers_api.ENDPOINT,
            params=params,
            max_pages=max_pages,
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
                logger.warning(
                    "⚠️ Could not parse 'date_created_gmt' for customer ID %s: %s",
                    customer.get("id"),
                    e,
                )
                continue

        # 🔁 Shortcut: If filtering by email, return only first match
        if email and filtered_customers:
            # Return only the first match for email (assumes uniqueness)
            return [filtered_customers[0]]  # Assumes email is unique

        # ✅ Return all valid customers that passed date filter
        return filtered_customers

    def validate_customer_exists_and_matches_api(self, email: str, dao) -> None:
        """
        Checks that customer exists in GET /customers, validates schema, and matches DB record.
        - fast API call - API returns result for this query
        - minimal overhead
        - Blind trust in API
        - Cannot detect duplicates
        - API filter → 1 result → OK

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
        logger.debug("⚙️ Validating existence of customer by email: %s", email)

        # 🔍 Call API to get customers
        result = self.call_list_all_customers_paginated(email=email)

        # ✅ API validation
        customer = assert_valid_customer_in_api(result, email)
        logger.info("✅ Assertion passed: Customer found calling API GET all customers paginated")

        # ✅ Schema validation - Validates API response schema using existing method GET /customers response.
        validate_customer_response_schema(customer=customer)

        # ✅ DB validation
        db_customer = dao.get_customer_by_email(email)
        assert_valid_customer_matches_db(customer, db_customer)

        logger.info("✅ Assertion passed: Customer record validated in DB for ID=%s", db_customer["ID"])

    # 🔍 Why both validations are needed?
    # Even though the schema is the same, you're validating:
    #    - That the create endpoint returns a well-formed customer
    #    - That the list/retrieve endpoint also returns that customer correctly
    # It’s entirely possible for one to pass and the other to fail if there's a bug in the API's data handling
    # logic (e.g., bad serialization in GET, missing fields in POST).

    def validate_customer_uniqueness_and_consistency(self, email: str, dao) -> None:
        """
        Validates that:
        - Exactly ONE customer exists with given email (full dataset scan)
        - API response is valid (schema)
        - DB record matches API data
        - Detects duplicates
        - Independent of API correctness (filter in Python)

        You are testing the SYSTEM, not the endpoint:
        - Is my system data correct regardless of API behavior?

        When to use it:
        Deep method (10% of tests)
        🧠 Deep → System correctness
            ✔ duplicate detection
            ✔ regression
            ✔ data integrity
            ✔ Migration / cleanup tests
                - import data
                - restore DB
                - run cleanup jobs
        """

        logger.debug("🟢 Validating uniqueness of customer by email: %s", email)

        # 🔍 FULL DATASET SCAN (no API filtering) Scan the whole dataset, and stop trusting API filtering.
        all_customers = self.call_list_all_customers_paginated()

        # ✅ Uniqueness validation
        customer = assert_single_customer_by_email(all_customers, email)

        logger.info("✅ Assertion passed: Exactly one customer found in full dataset scan")

        # ✅ Schema validation
        validate_customer_response_schema(customer=customer)

        # ✅ DB validation
        db_customer = dao.get_customer_by_email(email)
        assert_valid_customer_matches_db(customer, db_customer)

        logger.info("✅ Assertion passed: Customer record validated in DB for ID=%s", db_customer["ID"])

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
