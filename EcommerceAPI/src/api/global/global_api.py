"""
Base API Layer

Provides generic HTTP methods for all entities.

🎯 Purpose:
- Centralize HTTP request logic
- Avoid duplication across CustomersApi, OrdersApi, etc.
"""

from typing import Dict, Any, Optional


class BaseApi:
    def __init__(self, request_utility, endpoint: str):
        self.request_utility = request_utility
        self.endpoint = endpoint

    # ------------------------
    # GENERIC: GET (list)
    # ------------------------
    def get_all(self, params: Optional[Dict[str, Any]] = None, expected_status_code: int = 200):
        return self.request_utility.get(
            self.endpoint,
            params=params,
            expected_status_code=expected_status_code,
        )

    # ------------------------
    # GENERIC: GET by ID
    # ------------------------
    def get_by_id(self, resource_id: int, expected_status_code: int = 200):
        return self.request_utility.get(
            f"{self.endpoint}/{resource_id}",
            expected_status_code=expected_status_code,
        )

    # ------------------------
    # GENERIC: POST
    # ------------------------
    def create(self, payload: Dict[str, Any], expected_status_code: int = 201):
        return self.request_utility.post(
            self.endpoint,
            payload=payload,
            expected_status_code=expected_status_code,
        )

    # ------------------------
    # GENERIC: PUT
    # ------------------------
    def update(self, resource_id: int, payload: Dict[str, Any], expected_status_code: int = 200):
        return self.request_utility.put(
            f"{self.endpoint}/{resource_id}",
            payload=payload,
            expected_status_code=expected_status_code,
        )

    # ------------------------
    # GENERIC: DELETE
    # ------------------------
    def delete(self, resource_id: int, expected_status_code: int = 200, force: bool = True):
        return self.request_utility.delete(
            f"{self.endpoint}/{resource_id}",
            params={"force": force},
            expected_status_code=expected_status_code,
        )
