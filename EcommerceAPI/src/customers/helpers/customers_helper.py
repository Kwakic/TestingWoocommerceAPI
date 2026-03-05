# CUSTOMER HELPER - (TO CREATE PAYLOAD API CALL)

from __future__ import annotations

import logging
from typing import Optional, List, Dict, Any

from EcommerceAPI.src.utilities.pagination_utils import paginate_all_results
from EcommerceAPI.src.utilities.genericUtilities import generate_random_email_and_password
from EcommerceAPI.src.utilities.exceptions import UnexpectedStatusCodeError, SchemaValidationError
from EcommerceAPI.src.utilities.date_timestamp_utils import safe_parse_utc_datetime
from EcommerceAPI.src.core.http_response import HttpResponse
from EcommerceAPI.src.customers.api.customers_api import CustomersApi


logger = logging.getLogger(__name__)


class CustomersHelper(object):
    """
    Domain-level orchestration layer for Customers (workflow).

    Responsibilities
    ---------------
    ✔ Build request payloads (including auto-generation)
    ✔ Delegate HTTP calls to CustomersApi (no direct HTTP usage)
    ✔ Handle happy-path and expected negative flows
    ✔ Delegate validation to validator layer

    Return Behavior
    ---------------
    Helper methods support two return modes:

    1. Default mode (return_http_response=False):
       → Returns parsed JSON (dict or list)
       → Used for most tests (clean, simple, business-focused)

    2. Response mode (return_http_response=True):
       → Returns HttpResponse object
       → Used when access to transport data is required:
           - status_code
           - headers
           - elapsed time
           - request/response debugging

    Design Principles
    ----------------
    ✔ Helper abstracts transport layer for most tests
    ✔ Keeps tests readable and business-focused
    ✔ Allows opt-in access to full HTTP response when needed
    ✔ Supports both positive and negative scenarios

    - Helper knows only about transport
    - Helper only orchestrates

    Non-Responsibilities
    --------------------
    ✘ No raw HTTP calls (handled by APIClient)
    ✘ No schema validation logic (delegated to validators)
    ✘ No business validators
    ✘ No database access
    ✘ No pytest fixtures


    Testing Guidelines
    -----------------
    - Positive tests:
        → Prefer fixtures (e.g. create_valid_customer)


    - Advanced validation (status, headers, debugging):
        → Use helper(return_http_response=True)

    - Negative tests / invalid inputs:
        → Use raw_customer_api (returns HttpResponse)
    """

    ENDPOINT = "customers"

    def __init__(self, customers_api: CustomersApi):  # dependency injection flow
        """
        Args:
            customers_api: Domain API client (wraps APIClient)

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
            auto_generate: bool = True,
            return_http_response: bool = False,
            **kwargs,
    ) -> Dict[str, Any] | HttpResponse:
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
            auto_generate: Auto-generate credentials for positive tests
            return_http_response:  - False (default) → returns parsed JSON (dict)
                              - True → returns HttpResponse (status_code, headers, elapsed, etc.)
            **kwargs: Additional payload fields

        Returns:
            Dict[str, Any] | HttpResponse:
                - dict → default mode (parsed JSON)
                - HttpResponse → if return_http_response=True

        Raises:
            UnexpectedStatusCodeError, SchemaValidationError: Re-raised if no parsed error body is available.
            On expected failures (4xx/5xx) this helper will attempt to return the parsed error JSON
            attached by APIClient so tests can assert on error payloads.

        Note:
            - APIClient handles response parsing and attaches:
                - response_json (parsed body)
                - response (the raw requests.Response) when it raises UnexpectedStatusCodeError / SchemaValidationError.
            - Catching those exceptions and returning response_json is the cleanest way for helper methods to expose
            error bodies to tests (useful for negative validators).
            - request_raw (or return_raw=True) is still useful when you need the raw Response object (headers, exact
            body bytes, status) or to bypass the exception-raising behavior entirely. Use api_client.request_raw from
            tests for advanced debugging; use the helper's exception-handling for common negative validators.

            - Use api_client.request_raw (or APIClient.raw_post/raw_get) from tests when you need:
                - Access to response.headers, response.status_code, response.content in raw form, exact body bytes etc.
                - To avoid _handle_response raising (you want to inspect whatever the server returned regardless of
                expected_status_code).
            - Use return_raw=True on APIClient.post(...) only when you expect the response status to match
            expected_status_code but still want the raw Response or to bypass the exception-raising behavior entirely.
            - Use api_client.request_raw from tests for advanced debugging; use the helper's exception-handling for
            common negative validators.

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

        try:
            http_response = self.customers_api.create_customer(payload=payload)

            if return_http_response:
                return http_response

            return http_response.json
        except (UnexpectedStatusCodeError, SchemaValidationError) as e:
            # Log a short warning so the failure is visible in the structured logs (CustomFormatter will redact
            # sensitive info/fields).
            logger.warning("⚠️ Customer creation raised %s: %s", type(e).__name__, e)

            # Preferred: APIClient attaches parsed JSON to 'response_json' on the exception
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

            response = getattr(e, "response", None)

            if return_http_response and response is not None:
                return response

            if response_json is not None:
                return response_json

            # Nothing parseable attached — re-raise so caller/test sees the original exception
            raise

    def update_customer(
            self,
            customer_id: int,
            payload: Optional[Dict[str, Any]] = None,
            return_http_response: bool = False,
            **kwargs,
    ) -> Dict[str, Any] | HttpResponse:
        """
        Update customer fields.
        - Accepts full payload (same as API)
        - Does NOT modify payload
        - It supports positive + negative flows (This allows: update_customer(customer_id, first_name=None))

        Supports:
        - payload: for full/complex updates
        - return_http_response:  - False (default) → returns parsed JSON (dict)
                            - True → returns HttpResponse (status_code, headers, elapsed, etc.)
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
            http_response = self.customers_api.update_customer(customer_id=customer_id, payload=final_payload)

            if return_http_response:
                return http_response

            return http_response.json

        except (UnexpectedStatusCodeError, SchemaValidationError) as e:
            logger.warning("⚠️ Customer update raised %s: %s", type(e).__name__, e)

            response_json = getattr(e, "response_json", None)
            response = getattr(e, "response", None)

            if return_http_response and response is not None:
                return response

            if response_json is not None:
                return response_json

            raise

    def get_customer_by_id(
            self,
            customer_id: int,
            return_http_response: bool = False
    ) -> Dict[str, Any] | HttpResponse:
        """
         Retrieve a customer by their ID.

         Args:
             customer_id (int): Customer ID.
             return_http_response:  - False (default) → returns parsed JSON (dict)
                                    - True → returns HttpResponse (status_code, headers, elapsed, etc.)

         Returns:
             dict: Parsed customer JSON response + HTTP response
         """
        # logger.debug(f"🟢 Calling 'Get Customer' for ID {customer_id}.")
        logger.debug("🟢 Calling 'Get Customer' for ID %s.", customer_id)

        http_response = self.customers_api.get_customer(customer_id)

        if return_http_response:
            return http_response

        return http_response.json

    def get_customer_by_email(
            self,
            email: str,
            return_http_response: bool = False
    ) -> Dict[str, Any] | HttpResponse:
        """
        Retrieve a customer by email.

        Returns:
            dict: First matching customer extracted from HttpResponse.json

        Notes:
            - API layer returns HttpResponse
            - Helper extracts `.json` (list)
            - WooCommerce returns a list → helper returns first item

        Raises:
            AssertionError if no customer found.
        """
        logger.debug("🟢 Calling 'Get Customer by Email' for %s.", email)

        http_response = self.customers_api.get_customer_by_email(email=email)

        if return_http_response:
            return http_response

        customers = http_response.json

        if not customers:
            raise AssertionError(f"❌ No customer found for email={email}")

        return customers[0]

    def delete_customer(
            self,
            customer_id: int,
            return_http_response: bool = False
    ) -> Dict[str, Any] | HttpResponse:
        """
        Delete (hard delete) a customer by ID using force=true.

        Args:
            customer_id (int): Customer ID.
            return_http_response:  - False (default) → returns parsed JSON (dict)
                              - True → returns HttpResponse (status_code, headers, elapsed, etc.)

        Returns:
            dict: Parsed JSON response from delete
        """
        # Including into DELETE API the force=true query parameter otherwise it will be soft deleted and an error
        # triggered
        # logger.debug(f"🟢 Calling 'Delete Customer' for ID {customer_id}.")
        logger.debug("🟢 Calling 'Delete Customer' for ID %s.", customer_id)

        http_response = self.customers_api.delete_customer(customer_id, force=True)

        if return_http_response:
            return http_response

        return http_response.json

    # ------------------------
    # Listing / Pagination
    # ------------------------
    def list_customers_paginated(
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
        - Delegates HTTP to CustomersApi layer
        - Applies post-fetch filtering
        - Does NOT perform schema validation here

        Notes:
            - paginate_all_results takes care of the page loop and returns a flat list.
            - This method applies post-fetch date filtering using safe_parse_utc_datetime.

        No HTTP required:
            - Uses paginate_all_results
            - Returns aggregated list
            - Not a single response
            - No single HttpResponse to return
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
        # Use injected API client
        all_customers = paginate_all_results(
            api_client=self.customers_api.api_client,
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


# # NOTE!! Keep this main block for local debugging only. Remove or guard it before committing if you prefer to avoid
# # leaving ad-hoc debug code in the main branch.
# if __name__ == "__main__":
#     # This block only runs when executing this file directly
#     from dotenv import load_dotenv
#     load_dotenv()  # <-- loads .env for manual debugging
#
#     from EcommerceAPI.src.clients.api_client import APIClient
#     ru = APIClient()
#     helper = CustomersHelper(api_client=ru)
#     items = helper.list_customers_paginated()
#     breakpoint()  # Execution will pause here and drop into the debugger (pdb by default)
#     print(len(items))
#
