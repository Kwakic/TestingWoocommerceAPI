# """
# JWT authentication strategy.
# """
#
# from typing import Dict, Any
# from .base_auth import AuthStrategy
#
#
# class JWTAuth(AuthStrategy):
#
#     def __init__(self, token: str):
#         self.token = token
#
#     def apply(self, request_kwargs: Dict[str, Any]) -> Dict[str, Any]:
#
#         headers = request_kwargs.setdefault("headers", {})
#         headers["Authorization"] = f"Bearer {self.token}"
#
#         return request_kwargs
