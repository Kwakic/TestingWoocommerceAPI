import logging
from typing import Any, Dict, Optional

from EcommerceAPI.src.core.http_response import HttpResponse

logger = logging.getLogger(__name__)


class CustomersApi:
    """
    Customers API client (happy-path, thin wrapper).
    Source of truth for endpoints.

    This layer is intentionally dumb.

    Responsibilities:
    -----------------
    ✔ Know endpoint paths
    ✔ Know HTTP verbs
    ✔ Delegate calls to RequestUtility
    ✔ Return HttpResponse (NEVER parsed JSON)
    ✔ It keeps tests clean and consistent

    Non-responsibilities:
    ---------------------
    ✘ No assertions
    ✘ No schema validation
    ✘ No fixtures
    ✘ No database access
    ✘ No business rules
    ✘ No test ergonomics (auto-generation, retries, etc.)
    ✘ No return .json

    👉 API layer MUST:
        - ✅ return HttpResponse

    Any unexpected HTTP status is handled by RequestUtility,
    which raises UnexpectedStatusCodeError / SchemaValidationError.
    """

    ENDPOINT = "/customers"

    def __init__(self, request_utility):
        """
        Parameters
        ----------
        request_utility : RequestUtility
            Pre-configured HTTP client injected by fixture/plugin.
        """
        self.request_utility = request_utility

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------
    def create_customer(self, payload: Dict[str, Any]) -> HttpResponse:
        """
        POST /customers

        Create a new customer.

        Args:
            payload (dict):
                Fully prepared request body.

        Returns:
            HttpResponse: Full response object (status, headers, JSON, text, etc.)

        Raises:
            UnexpectedStatusCodeError
            SchemaValidationError
        """
        logger.debug("📡 POST %s payload_keys=%s", self.ENDPOINT, list(payload.keys()))

        return self.request_utility.post(self.ENDPOINT, payload=payload)

    # ------------------------------------------------------------------
    # READ (single, by ID - filtered list shortcut))
    # ------------------------------------------------------------------
    def get_customer(self, customer_id: Any) -> HttpResponse:
        """
        GET /customers/{id}

        Fetch a single customer by ID.
        """
        endpoint = f"{self.ENDPOINT}/{customer_id}"
        logger.debug("📡 GET %s", endpoint)

        return self.request_utility.get(endpoint)

    # ------------------------------------------------------------------
    # READ (by email - filtered list shortcut)
    # ------------------------------------------------------------------
    def get_customer_by_email(self, email: str,) -> HttpResponse:
        """
        GET /customers?email={email}

        Fetch customer(s) filtered by email.

        Note:
            WooCommerce returns a list. This method returns a raw list response.
        """
        params = {"email": email.lower()}

        logger.debug("📡 GET %s params=%s", self.ENDPOINT, params)

        return self.request_utility.get(self.ENDPOINT, params=params)

    # ------------------------------------------------------------------
    # READ (list)
    # ------------------------------------------------------------------
    def list_customers(self, *, params: Optional[Dict[str, Any]] = None) -> HttpResponse:
        """
        GET /customers

        List customers with optional query parameters
        (pagination, filters, etc.).
        """
        logger.debug("📡 GET %s params=%s", self.ENDPOINT, params)

        return self.request_utility.get(self.ENDPOINT, params=params)

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------
    def delete_customer(self, customer_id: Any, force: bool = True) -> HttpResponse:
        """
        DELETE /customers/{id}

        Delete a customer.

        Args:
            customer_id:
                ID of the customer to delete.
            force (bool):
                Whether to force deletion (API-specific).
        """
        endpoint = f"{self.ENDPOINT}/{customer_id}"
        logger.debug("📡 DELETE %s force=%s", endpoint, force)

        return self.request_utility.delete(endpoint, params={"force": force})

    def update_customer(self, customer_id: Any, payload: Dict[str, Any],) -> HttpResponse:
        """
        PUT /customers/{id}
        """
        endpoint = f"{self.ENDPOINT}/{customer_id}"
        logger.debug("📡 PUT %s payload_keys=%s", endpoint, list(payload.keys()))

        return self.request_utility.put(endpoint, payload=payload)
