import logging
from typing import Any, Dict, Optional

from EcommerceAPI.src.clients.api_client import APIClient
from EcommerceAPI.src.core.http_response import HttpResponse


logger = logging.getLogger(__name__)


class CouponsApi:
    """
    Coupons API client (happy-path, thin wrapper).
    Source of truth for coupon endpoints.

    This layer is intentionally dumb.

    Responsibilities:
    -----------------
    ✔ Know endpoint paths
    ✔ Know HTTP verbs
    ✔ Delegate calls to APIClient
    ✔ Return HttpResponse (NEVER parsed JSON)

    Non-responsibilities:
    ---------------------
    ✘ No validators
    ✘ No schema validation
    ✘ No fixtures
    ✘ No database access
    ✘ No business rules
    ✘ No test ergonomics
    ✘ No return .json

    👉 API layer MUST:
        - ✅ return HttpResponse

    Any unexpected HTTP status is handled by APIClient,
    which raises UnexpectedStatusCodeError / SchemaValidationError.
    """

    ENDPOINT = "/coupons"

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
    def create_coupon(self, payload: Dict[str, Any]) -> HttpResponse:
        """
        POST /coupons

        Create a new coupon.

        Args:
            payload:
                Fully prepared request body.

        Returns:
            HttpResponse: Full response object.
        """
        logger.debug(
            "📡 POST %s payload_keys=%s",
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
    def get_coupon(self, coupon_id: Any) -> HttpResponse:
        """
        GET /coupons/{id}

        Fetch a single coupon by ID.
        """
        endpoint = f"{self.ENDPOINT}/{coupon_id}"

        logger.debug("📡 GET %s", endpoint)

        return self.api_client.get(endpoint)

    # ------------------------------------------------------------------
    # READ (list)
    # ------------------------------------------------------------------
    def list_coupons(
        self,
        *,
        params: Optional[Dict[str, Any]] = None,
    ) -> HttpResponse:
        """
        GET /coupons

        List coupons with optional query parameters
        (pagination, filters, etc.).
        """
        logger.debug(
            "📡 GET %s params=%s",
            self.ENDPOINT,
            params,
        )

        return self.api_client.get(
            self.ENDPOINT,
            params=params,
        )

    # ------------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------------
    def update_coupon(
        self,
        coupon_id: Any,
        payload: Dict[str, Any],
    ) -> HttpResponse:
        """
        PUT /coupons/{id}

        Update an existing coupon.
        """
        endpoint = f"{self.ENDPOINT}/{coupon_id}"

        logger.debug(
            "📡 PUT %s payload_keys=%s",
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
    def delete_coupon(
        self,
        coupon_id: Any,
        force: bool = True,
    ) -> HttpResponse:
        """
        DELETE /coupons/{id}

        Delete a coupon.

        Args:
            coupon_id:
                ID of the coupon to delete.

            force:
                Whether to force deletion.
        """
        endpoint = f"{self.ENDPOINT}/{coupon_id}"

        logger.debug(
            "📡 DELETE %s force=%s",
            endpoint,
            force,
        )

        return self.api_client.delete(
            endpoint,
            params={"force": force},
        )
