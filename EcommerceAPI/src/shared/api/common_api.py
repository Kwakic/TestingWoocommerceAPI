"""
Base API Layer

Provides generic HTTP methods for all entities.

🎯 Purpose:
- Centralize HTTP request logic
- Avoid duplication across CustomersApi, OrdersApi, etc.
"""

from typing import Dict, Any, Optional

from EcommerceAPI.src.clients.api_client import APIClient
from EcommerceAPI.src.core.http_response import HttpResponse


class CommonApi:
    def __init__(self, api_client: APIClient, endpoint: str):
        self.api_client = api_client
        self.endpoint = endpoint

    def _endpoint(self, suffix: str = "") -> str:
        """
        👉 Avoid repeating self.ENDPOINT
        Then self.api_client.get(self._endpoint(resource_id))
        """
        return f"{self.endpoint}/{suffix}" if suffix else self.endpoint

    # ------------------------
    # GENERIC: GET (list)
    # ------------------------
    def get_all(
            self,
            params: Optional[Dict[str, Any]] = None,
    ) -> HttpResponse:
        return self.api_client.get(
            self.endpoint,
            params=params,
        )

    # ------------------------
    # GENERIC: GET by ID
    # ------------------------
    def get_by_id(self, resource_id: int) -> HttpResponse:
        return self.api_client.get(f"{self.endpoint}/{resource_id}")

    # ------------------------
    # GENERIC: POST
    # ------------------------
    def create(self, payload: Dict[str, Any]) -> HttpResponse:
        return self.api_client.post(
            self.endpoint,
            payload=payload
        )

    # ------------------------
    # GENERIC: PUT
    # ------------------------
    def update(self, resource_id: int, payload: Dict[str, Any]) -> HttpResponse:
        return self.api_client.put(
            f"{self.endpoint}/{resource_id}",
            payload=payload
        )

    # ------------------------
    # GENERIC: DELETE
    # ------------------------
    def delete(self, resource_id: int, force: bool = True) -> HttpResponse:
        return self.api_client.delete(
            f"{self.endpoint}/{resource_id}",
            params={"force": force}
        )
