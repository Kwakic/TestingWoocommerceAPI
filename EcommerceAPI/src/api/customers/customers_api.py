import logging
from typing import Any, Dict, List, Optional

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
    ✔ Return parsed JSON on success
    ✔ It keeps tests clean and consistent

    Non-responsibilities:
    ---------------------
    ✘ No assertions
    ✘ No schema validation
    ✘ No fixtures
    ✘ No database access
    ✘ No business rules
    ✘ No test ergonomics (auto-generation, retries, etc.)

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
    def create_customer(
        self,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        POST /customers

        Create a new customer.

        Args:
            payload (dict):
                Fully prepared request body.

        Returns:
            dict: Parsed JSON response.

        Raises:
            UnexpectedStatusCodeError
            SchemaValidationError
        """
        logger.debug("📡 POST %s payload_keys=%s", self.ENDPOINT, list(payload.keys()))

        response = self.request_utility.post(
            self.ENDPOINT,
            payload=payload,
        )

        return response.json

    # ------------------------------------------------------------------
    # READ (single, by ID - filtered list shortcut))
    # ------------------------------------------------------------------
    def get_customer(
        self,
        customer_id: Any
    ) -> Dict[str, Any]:
        """
        GET /customers/{id}

        Fetch a single customer by ID.
        """
        endpoint = f"{self.ENDPOINT}/{customer_id}"
        logger.debug("📡 GET %s", endpoint)

        response = self.request_utility.get(endpoint)

        return response.json

    # ------------------------------------------------------------------
    # READ (by email - filtered list shortcut)
    # ------------------------------------------------------------------
    def get_customer_by_email(
            self,
            email: str,
    ) -> List[Dict[str, Any]]:
        """
        GET /customers?email={email}

        Fetch customer(s) filtered by email.

        Note:
            WooCommerce returns a list. This method returns a raw list response.
        """
        params = {"email": email.lower()}

        logger.debug("📡 GET %s params=%s", self.ENDPOINT, params)

        response = self.request_utility.get(self.ENDPOINT, params=params)

        return response.json

    # ------------------------------------------------------------------
    # READ (list)
    # ------------------------------------------------------------------
    def list_customers(
        self,
        *,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        GET /customers

        List customers with optional query parameters
        (pagination, filters, etc.).
        """
        logger.debug("📡 GET %s params=%s", self.ENDPOINT, params)

        response = self.request_utility.get(
            self.ENDPOINT,
            params=params
        )

        return response.json

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------
    def delete_customer(self, customer_id: Any, force: bool = True) -> Dict[str, Any]:
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

        response = self.request_utility.delete(endpoint, params={"force": force})

        return response.json

    def update_customer(
        self,
        customer_id: Any,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        PUT /customers/{id}
        """
        endpoint = f"{self.ENDPOINT}/{customer_id}"
        logger.debug("📡 PUT %s payload_keys=%s", endpoint, list(payload.keys()))

        response = self.request_utility.put(endpoint, payload=payload)

        return response.json
