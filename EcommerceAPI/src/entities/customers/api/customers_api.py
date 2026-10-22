import logging
from typing import Any, Dict, Optional

from EcommerceAPI.src.clients.api_client import APIClient
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
    ✔ Delegate calls to APIClient
    ✔ Return HttpResponse (NEVER parsed JSON)
    ✔ It keeps tests clean and consistent

    Non-responsibilities:
    ---------------------
    ✘ No validators
    ✘ No schema validation
    ✘ No fixtures
    ✘ No database access
    ✘ No business rules
    ✘ No test ergonomics (auto-generation, retries, etc.)
    ✘ No return .json

    👉 API layer MUST:
        - ✅ return HttpResponse

    Any unexpected HTTP status is handled by APIClient,
    which raises UnexpectedStatusCodeError / SchemaValidationError.
    """

    ENDPOINT = "/customers"

    def __init__(self, api_client: APIClient):
        """
        Parameters
        ----------
        api_client : APIClient
            Pre-configured HTTP client injected by fixture/plugin.
        """
        self.api_client = api_client

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------
    def create_customer(self, payload: Dict[str, Any]) -> HttpResponse:
        """
        POST /customers


        Create a new customers.

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

        return self.api_client.post(self.ENDPOINT, payload=payload)

    # ------------------------------------------------------------------
    # READ (single, by ID - filtered list shortcut))
    # ------------------------------------------------------------------
    def get_customer(self, customer_id: Any) -> HttpResponse:
        """
        GET /customers/{id}

        Fetch a single customers by ID.
        """
        endpoint = f"{self.ENDPOINT}/{customer_id}"
        logger.debug("📡 GET %s", endpoint)

        return self.api_client.get(endpoint)

    # ------------------------------------------------------------------
    # READ (by email - filtered list shortcut)
    # ------------------------------------------------------------------
    def get_customer_by_email(
        self,
        email: str,
    ) -> HttpResponse:
        """
        GET /customers?email={email}

        Fetch customers(s) filtered by email.

        Note:
            WooCommerce returns a list. This method returns a raw list response.
        """
        params = {"email": email.lower()}

        logger.debug("📡 GET %s params=%s", self.ENDPOINT, params)

        return self.api_client.get(self.ENDPOINT, params=params)

    # ------------------------------------------------------------------
    # READ (list)
    # ------------------------------------------------------------------
    def list_customers(
        self, *, params: Optional[Dict[str, Any]] = None
    ) -> HttpResponse:
        """
        GET /customers

        List customers with optional query parameters
        (pagination, filters, etc.).
        """
        logger.debug("📡 GET %s params=%s", self.ENDPOINT, params)

        return self.api_client.get(self.ENDPOINT, params=params)

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------
    def delete_customer(self, customer_id: Any, force: bool = True) -> HttpResponse:
        """
        DELETE /customers/{id}

        Delete a customers.

        Args:
            customer_id:
                ID of the customers to delete.
            force (bool):
                Whether to force deletion (API-specific).
        """
        endpoint = f"{self.ENDPOINT}/{customer_id}"
        logger.debug("📡 DELETE %s force=%s", endpoint, force)

        return self.api_client.delete(endpoint, params={"force": force})

    def update_customer(
        self,
        customer_id: Any,
        payload: Dict[str, Any],
    ) -> HttpResponse:
        """
        PUT /customers/{id}
        """
        endpoint = f"{self.ENDPOINT}/{customer_id}"
        logger.debug("📡 PUT %s payload_keys=%s", endpoint, list(payload.keys()))

        return self.api_client.put(endpoint, payload=payload)
