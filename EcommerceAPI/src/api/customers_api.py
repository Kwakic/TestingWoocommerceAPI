"""
CustomersApi
============

Customers API client (happy-path, thin wrapper).

This module is a thin HTTP wrapper around RequestUtility.
It is intentionally dumb.

Responsibilities:
-----------------
✔ Build correct endpoints
✔ Call RequestUtility with expected success statuses
✔ Return parsed response data

Non-responsibilities:
---------------------
✘ No assertions
✘ No schema validation
✘ No business rules
✘ No DB access
✘ No fixtures
✘ No retries / auth logic (delegated to RequestUtility)

Any unexpected HTTP status is handled by RequestUtility,
which raises UnexpectedStatusCodeError / SchemaValidationError.

Design notes:
-------------
- This client is used by domain helpers (CustomersHelper), NOT by tests.
- Negative / raw testing must bypass this layer and use RequestUtility directly.

!!!!my notes: CustomersHelper no longer calls request_utility.post("/customers", …) directly
It delegates HTTP calls to CustomersApi
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# from typing import TYPE_CHECKING
# if TYPE_CHECKING:
#     # IDE-only: point to the test-level fixture so PyCharm can navigate to it. Do NOT import conftest at runtime!
#     # TYPE_CHECKING imports are ignored at runtime, so they’re safe to add into framework code.
#     from EcommerceAPI.plugins.entities import RequestUtility
#


class CustomersApi:
    """
    Positive-path Customers API client.

    This class assumes that calls are expected to succeed.
    If an unexpected HTTP status is returned, RequestUtility will raise an exception (UnexpectedStatusCodeError).
    """
    ENDPOINT = "customers"

    def __init__(self, request_utility):
        """
        Raises:
            ValueError: If request_utility is None.
            TypeError: If request_utility is not an instance of RequestUtility.

        Parameters
        ----------
        request_utility : RequestUtility
            Preconfigured HTTP client injected by plugin/fixture.
        """
        if request_utility is None:
            raise ValueError(
                "Customers_api.py requires a RequestUtility instance managed by fixture ...x...."
            )
        if not isinstance(request_utility):
            raise TypeError("request_utility must be an instance of RequestUtility")

        self.request_utility = request_utility

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------
    def create_customer(self, payload: Dict[str, Any], *, expected_status_code: int = 201) -> Dict[str, Any]:
        """
        Create a customer via POST /customers.

        Expected behavior:
        - HTTP 201 Created
        - Returns parsed customer object

        Parameters
        ----------
        payload : dict
            Valid customer payload.

        Returns
        -------
        dict
            Created a customer object.
        """
        response = self.request_utility.post(
            self.ENDPOINT,
            json=payload,
            expected_status=201,
        )
        return response.json()

    # ------------------------------------------------------------------
    # READ
    # ------------------------------------------------------------------
    def get_customer_by_id(self, customer_id: int) -> Dict[str, Any]:
        """
        Fetch a customer by ID via GET /customers/{id}.

        Expected behavior:
        - HTTP 200 OK
        """
        response = self.request_utility.get(
            path=f"/customers/{customer_id}",
            expected_status=200,
        )
        return response.json()

    def list_customers(
        self,
        email: Optional[str] = None,
        per_page: int = 100,
        page: int = 1,
    ) -> List[Dict[str, Any]]:
        """
        List customers via GET /customers.

        Supports basic filtering (email) and pagination.

        Parameters
        ----------
        email : str, optional
            Filter customers by email.
        per_page : int
            Number of items per page.
        page : int
            Page number.

        Returns
        -------
        list[dict]
            List of customer objects.
        """
        params: Dict[str, Any] = {
            "per_page": per_page,
            "page": page,
        }
        if email:
            params["email"] = email

        response = self.request_utility.get(
            path="/customers",
            params=params,
            expected_status=200,
        )
        return response.json()

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------
    def delete_customer(self, customer_id: int, force: bool = True) -> Dict[str, Any]:
        """
        Delete a customer via DELETE /customers/{id}.

        Parameters
        ----------
        customer_id : int
            Customer ID.
        force : bool
            Whether to force deletion.

        Returns
        -------
        dict
            API response payload.
        """
        response = self.request_utility.delete(
            path=f"/customers/{customer_id}",
            params={"force": force},
            expected_status=200,
        )
        return response.json()
