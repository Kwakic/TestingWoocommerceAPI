import logging
from typing import Any, Dict, Optional

from EcommerceAPI.src.clients.api_client import APIClient
from EcommerceAPI.src.core.http_response import HttpResponse

logger = logging.getLogger(__name__)


class OrdersApi:
    """
    Orders API client (happy-path, thin wrapper).

    This class is the source of truth for order endpoint paths and HTTP verbs.
    It delegates requests to ``APIClient`` and returns the complete
    ``HttpResponse`` without parsing or validating the response body.

    Responsibilities:
        - Define order endpoint paths and HTTP methods.
        - Delegate HTTP requests to the configured ``APIClient``.
        - Return ``HttpResponse`` objects to callers.

    This class does not validate schemas, apply business rules, access the
    database, manage fixtures, or orchestrate test data. Those responsibilities
    belong to validators, helpers, and pytest fixtures.
    """

    ENDPOINT = "/orders"

    def __init__(self, api_client: APIClient):
        """
        Store the pre-configured HTTP client used for order requests.

        Args:
            api_client: Client configured and provided by the test framework.
        """
        self.api_client = api_client

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------
    def create_order(self, payload: Dict[str, Any]) -> HttpResponse:
        """Send ``POST /orders`` with the supplied order payload."""
        logger.debug(
            "POST %s payload_keys=%s",
            self.ENDPOINT,
            list(payload.keys()),
        )

        return self.api_client.post(
            self.ENDPOINT,
            payload=payload,
        )

    # ------------------------------------------------------------------
    # READ (single, by ID)
    # ------------------------------------------------------------------
    def get_order(self, order_id: Any) -> HttpResponse:
        """Send ``GET /orders/{id}`` to retrieve one order."""
        endpoint = f"{self.ENDPOINT}/{order_id}"
        logger.debug("GET %s", endpoint)

        return self.api_client.get(endpoint)

    # ------------------------------------------------------------------
    # READ (list)
    # ------------------------------------------------------------------
    def list_orders(
        self,
        *,
        params: Optional[Dict[str, Any]] = None,
    ) -> HttpResponse:
        """Send ``GET /orders`` with optional pagination or filter parameters."""
        logger.debug("GET %s params=%s", self.ENDPOINT, params)

        return self.api_client.get(
            self.ENDPOINT,
            params=params,
        )

    # ------------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------------
    def update_order(
        self,
        order_id: Any,
        payload: Dict[str, Any],
    ) -> HttpResponse:
        """Send ``PUT /orders/{id}`` with fields to update."""
        endpoint = f"{self.ENDPOINT}/{order_id}"
        logger.debug(
            "PUT %s payload_keys=%s",
            endpoint,
            list(payload.keys()),
        )

        return self.api_client.put(
            endpoint,
            payload=payload,
        )

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------
    def delete_order(
        self,
        order_id: Any,
        force: bool = True,
    ) -> HttpResponse:
        """Send ``DELETE /orders/{id}`` with WooCommerce's force option."""
        endpoint = f"{self.ENDPOINT}/{order_id}"
        logger.debug("DELETE %s force=%s", endpoint, force)

        return self.api_client.delete(
            endpoint,
            params={"force": force},
        )
