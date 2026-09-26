# CUSTOMER HELPER - DOMAIN API ORCHESTRATION

from __future__ import annotations

import logging
from typing import Optional, List, Dict, Any

from EcommerceAPI.src.utils.pagination_utils import paginate_all_results
from EcommerceAPI.src.utils.exceptions import (
    UnexpectedStatusCodeError,
    SchemaValidationError,
)
from EcommerceAPI.src.utils.date_timestamp_utils import safe_parse_utc_datetime
from EcommerceAPI.src.core.http_response import HttpResponse
from EcommerceAPI.src.customers.api.customers_api import CustomersApi

logger = logging.getLogger(__name__)


class CustomersHelper(object):
    """
    Domain-level orchestration layer for Customers.

    Responsibilities
    ---------------
    ✔ Receive already-prepared customer data
    ✔ Delegate customer API operations to CustomersApi
    ✔ Expose parsed JSON by default
    ✔ Optionally expose the framework HttpResponse
    ✔ Handle expected API exceptions and expose structured error bodies

    Test-data generation is intentionally NOT a Helper responsibility.
    Valid customer data is created by the test-data layer:

        CustomerFactory
              ↓
        CustomerBuilder
              ↓
        CustomerProvisioner
              ↓
        CustomersHelper
              ↓
        CustomersApi
              ↓
        WooCommerce

    The Helper therefore never generates email addresses, passwords, usernames,
    names, or other test data.

    Return Behavior
    ---------------
    Helper methods support two return modes:

    1. Default mode (return_http_response=False):
        → Returns parsed JSON (dict or list)
        → Used when tests need the business-level response data.

    2. Response mode (return_http_response=True):
        → Returns HttpResponse
        → Used when the caller needs transport-level information such as:
            - status_code
            - headers
            - elapsed time
            - response text
            - request/response debugging

    Design Principles
    ----------------
    ✔ Test-data generation belongs to Factory/Builder.
    ✔ Provisioning belongs to CustomerProvisioner.
    ✔ API orchestration belongs to CustomersHelper.
    ✔ HTTP transport belongs to CustomersApi/APIClient.
    ✔ Response/schema validation belongs to the appropriate validator layer.
    ✔ Cleanup and ownership belong to the test-data/fixture lifecycle.

    Non-Responsibilities
    --------------------
    ✘ No test-data generation
    ✘ No raw HTTP calls (handled by APIClient)
    ✘ No schema validation logic
    ✘ No business assertions
    ✘ No database access
    ✘ No pytest fixtures

    Testing Guidelines
    ------------------
    - Positive setup:
        → Prefer create_valid_customer.

    - Operations requiring transport-level assertions:
        → Use helper(return_http_response=True).

    - Negative tests / intentionally invalid payloads:
        → Prefer customer_api_raw when the test needs direct API control.
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
        payload: Optional[Dict[str, Any]] = None,
        return_http_response: bool = False,
        **kwargs,
    ) -> Dict[str, Any] | HttpResponse:
        """
        Create a customer through CustomersApi.

        The Helper receives customer creation data that has already been
        prepared by the caller. It does not generate test data.

        Args:
            payload:
                Optional complete customer creation payload.

            return_http_response:
                - False (default) → return parsed JSON.
                - True → return HttpResponse.

            **kwargs:
                Additional customer creation fields. These are merged into
                ``payload`` and override matching keys.

        Returns:
            Dict[str, Any] | HttpResponse:
                Parsed customer JSON by default, or HttpResponse when
                ``return_http_response=True``.

        Raises:
            UnexpectedStatusCodeError, SchemaValidationError:
                Re-raised when no structured error response is available.

        Notes:
            - Test-data generation belongs to CustomerFactory.
            - Scenario customization belongs to CustomerBuilder.
            - System provisioning belongs to CustomerProvisioner.
            - This method only prepares the final API payload and delegates
              the operation to CustomersApi.
            - For expected API failures, the helper exposes the parsed error
              body when the underlying exception provides one.
        """
        final_payload: Dict[str, Any] = {}

        # Accept either a complete payload or individual fields.
        if payload:
            final_payload.update(payload)

        # Explicit keyword arguments take precedence over payload values.
        final_payload.update(kwargs)

        logger.debug(
            "⚙️ Creating customer with payload keys: %r",
            list(final_payload.keys()),
        )

        try:
            http_response = self.customers_api.create_customer(payload=final_payload)

            if return_http_response:
                return http_response

            return http_response.json

        except (UnexpectedStatusCodeError, SchemaValidationError) as e:
            # Preserve the existing structured-error behavior so negative
            # tests can inspect parsed WooCommerce error responses.
            logger.warning(
                "⚠️ Customer creation raised %s: %s",
                type(e).__name__,
                e,
            )

            # Preferred: APIClient attaches parsed JSON to 'response_json' on the exception
            response_json = getattr(e, "response_json", None)

            # Fallback: parse the raw response if the exception did not
            # already provide structured JSON.
            if response_json is None:
                resp = getattr(e, "response", None)

                if resp is not None:
                    try:
                        response_json = resp.json()
                    except Exception as parse_err:
                        logger.exception(
                            "🚫 Failed to parse error response JSON from "
                            "create_customer: %s",
                            parse_err,
                        )
                        # Re-raise the original exception since we cannot provide structured error body
                        raise

            response = getattr(e, "response", None)

            if return_http_response and response is not None:
                return response

            if response_json is not None:
                return response_json

            # Nothing parseable was attached to the exception, so preserve
            # the original failure for the caller.
            raise

    def update_customer(
        self,
        customer_id: int,
        payload: Optional[Dict[str, Any]] = None,
        return_http_response: bool = False,
        **kwargs,
    ) -> Dict[str, Any] | HttpResponse:
        """
        Update customers fields.
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

        logger.debug(
            "🟢 Updating customers %s with payload keys: %r",
            customer_id,
            list(final_payload.keys()),
        )

        try:
            http_response = self.customers_api.update_customer(
                customer_id=customer_id, payload=final_payload
            )

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
        self, customer_id: int, return_http_response: bool = False
    ) -> Dict[str, Any] | HttpResponse:
        """
        Retrieve a customers by their ID.

        Args:
            customer_id (int): Customer ID.
            return_http_response:  - False (default) → returns parsed JSON (dict)
                                   - True → returns HttpResponse (status_code, headers, elapsed, etc.)

        Returns:
            dict: Parsed customers JSON response + HTTP response
        """
        # logger.debug(f"🟢 Calling 'Get Customer' for ID {customer_id}.")
        logger.debug("🟢 Calling 'Get Customer' for ID %s.", customer_id)

        http_response = self.customers_api.get_customer(customer_id)

        if return_http_response:
            return http_response

        return http_response.json

    def get_customer_by_email(
        self, email: str, return_http_response: bool = False
    ) -> Dict[str, Any] | HttpResponse:
        """
        Retrieve a customers by email.

        Returns:
            dict: First matching customers extracted from HttpResponse.json

        Notes:
            - API layer returns HttpResponse
            - Helper extracts `.json` (list)
            - WooCommerce returns a list → helper returns first item

        Raises:
            AssertionError if no customers found.
        """
        logger.debug("🟢 Calling 'Get Customer by Email' for %s.", email)

        http_response = self.customers_api.get_customer_by_email(email=email)

        if return_http_response:
            return http_response

        customers = http_response.json

        if not customers:
            raise AssertionError(f"❌ No customers found for email={email}")

        return customers[0]

    def delete_customer(
        self, customer_id: int, return_http_response: bool = False
    ) -> Dict[str, Any] | HttpResponse:
        """
        Delete (hard delete) a customers by ID using force=true.

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
            params["email"] = email.lower()

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
                # ✅ Parse customers date as offset-aware datetime in UTC
                created_date = parse_dt(created_gmt) if created_gmt else None
                if created_date:
                    # ❌ Skip customers if it was created *after* the allowed upper bound
                    if cutoff_before and created_date >= cutoff_before:
                        continue
                    # ❌ Skip customers if it was created *before* the allowed lower bound
                    if cutoff_after and created_date <= cutoff_after:
                        continue
                # ✅ Keep customers — passed all time filters
                filtered_customers.append(customer)
            except Exception as e:
                logger.warning(
                    "⚠️ Could not parse 'date_created_gmt' for customers ID %s: %s",
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

    def list_customers_for_test(
        self,
        test_run_id: str,
        per_page: int = 10,
        max_pages: int = 100,
        extra_params: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Test-focused helper for fetching ONLY customers created within a test run.

        WHY:
        ----
        - Avoids global DB dependency
        - Guarantees deterministic dataset
        - Reusable across all list tests
        - Keeps tests clean (no manual params building)

        Args:
            test_run_id (str):
                Unique identifier used in test data (email pattern)

            per_page (int):
                Pagination size

            max_pages (int):
                Safety cap to avoid infinite loops

            extra_params (dict):
                Optional additional filters (future-proof)

        Returns:
            List[dict]: Filtered customers belonging ONLY to this test run
        """

        logger.debug(
            "🧪 Fetching test customers (run_id=%s, per_page=%s, max_pages=%s)",
            test_run_id,
            per_page,
            max_pages,
        )

        params = {
            "per_page": per_page,
            "search": test_run_id,
        }

        # Allow optional extension (future-proof for filters)
        if extra_params:
            params.update(extra_params)

        return self.list_customers_paginated(
            params=params,
            max_pages=max_pages,
        )


# # NOTE!! Keep this main block for local debugging only. Remove or guard it before committing if you prefer to avoid
# # leaving ad-hoc debug code in the main branch.
# if __name__ == "__main__":
#     # This block only runs when executing this file directly
#     from dotenv import load_dotenv
#     load_dotenv()  # <-- loads .env for manual debugging
#
#     from EcommerceAPI.src.clients.api_client import APIClient
#     ru = APIClient()
#     helper = CustomersHelper(customers_api=ru)
#     items = helper.list_customers_paginated()
#     breakpoint()  # Execution will pause here and drop into the debugger (pdb by default)
#     print(len(items))
#
