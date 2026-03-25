# from EcommerceAPI.src.utils.credentials_utility import get_oauth2_token
#
# class OAuth2Auth(AuthStrategy):
#
#     def __init__(self):
#         self.access_token = get_oauth2_token()
#
#     def apply(self, request_kwargs):
#
#         headers = request_kwargs.setdefault("headers", {})
#         headers["Authorization"] = f"Bearer {self.access_token}"
#
#         return request_kwargs
