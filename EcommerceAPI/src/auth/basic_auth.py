# """
# HTTP Basic authentication strategy.
# """
#
# from typing import Dict, Any
# from .base_auth import AuthStrategy
#
#
# class BasicAuth(AuthStrategy):
#
#     def __init__(self, username: str, password: str):
#         self.username = username
#         self.password = password
#
#     def apply(self, request_kwargs: Dict[str, Any]) -> Dict[str, Any]:
#
#         request_kwargs["auth"] = (self.username, self.password)
#
#         return request_kwargs
