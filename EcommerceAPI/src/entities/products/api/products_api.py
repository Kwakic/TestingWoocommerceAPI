import logging
from typing import Any, Dict, Optional

from EcommerceAPI.src.clients.api_client import APIClient
from EcommerceAPI.src.core.http_response import HttpResponse

logger = logging.getLogger(__name__)


class ProductsApi:
    """
    Products API client (happy-path, thin wrapper).
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

    ENDPOINT = "/products"

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
    def create_product(self, payload: Dict[str, Any]) -> HttpResponse:
        """
        POST /products


        Create a new product.

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
    def get_product(self, product_id: Any) -> HttpResponse:
        """
        GET /products/{id}

        Fetch a single product by ID.
        """
        endpoint = f"{self.ENDPOINT}/{product_id}"
        logger.debug("📡 GET %s", endpoint)

        return self.api_client.get(endpoint)

    # ------------------------------------------------------------------
    # READ (by SKU - filtered list shortcut)
    # ------------------------------------------------------------------
    def get_product_by_sku(self, sku: str) -> HttpResponse:
        """
        GET /products?sku={sku}

        Fetch product(s) filtered by SKU.

        Note:
            WooCommerce returns a list. This method returns a raw list response.
        """
        params = {"sku": sku}

        logger.debug("📡 GET %s params=%s", self.ENDPOINT, params)

        return self.api_client.get(self.ENDPOINT, params=params)

    # ------------------------------------------------------------------
    # READ (by category - filtered list)
    # ------------------------------------------------------------------
    def get_products_by_category(self, category: str) -> HttpResponse:
        """
        GET /products?category={category}

        Fetch product(s) filtered by category.

        Note:
            WooCommerce may expect a category ID depending on configuration.
            This method returns a raw list response.
        """
        params = {"category": category}

        logger.debug("📡 GET %s params=%s", self.ENDPOINT, params)

        return self.api_client.get(self.ENDPOINT, params=params)

    # ------------------------------------------------------------------
    # READ (list)
    # ------------------------------------------------------------------
    def list_products(self, *, params: Optional[Dict[str, Any]] = None) -> HttpResponse:
        """
        GET /products

        List products with optional query parameters
        (pagination, filters, etc.).
        """
        logger.debug("📡 GET %s params=%s", self.ENDPOINT, params)

        return self.api_client.get(self.ENDPOINT, params=params)

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------
    def delete_product(self, product_id: Any, force: bool = True) -> HttpResponse:
        """
        DELETE /products/{id}

        Delete a product.

        Args:
            product_id:
                ID of the products to delete.
            force (bool):
                Whether to force deletion (API-specific).
        """
        endpoint = f"{self.ENDPOINT}/{product_id}"
        logger.debug("📡 DELETE %s force=%s", endpoint, force)

        return self.api_client.delete(endpoint, params={"force": force})

    def update_product(
        self,
        product_id: Any,
        payload: Dict[str, Any],
    ) -> HttpResponse:
        """
        PUT /products/{id}
        """
        endpoint = f"{self.ENDPOINT}/{product_id}"
        logger.debug("📡 PUT %s payload_keys=%s", endpoint, list(payload.keys()))

        return self.api_client.put(endpoint, payload=payload)
