# import os
# import json
# from typing import Any, Dict, List
#
#
# def load_coupon_scenarios(filename: str = 'coupon_scenarios.json') -> List[Dict[str, Any]]:
#     """
#     Load coupon scenarios from a JSON file located in the 'data' directory.
#
#     Args:
#         filename (str): The name of the JSON file to load.
#
#     Returns:
#         List[Dict[str, Any]]: A list of coupon scenario dictionaries.
#
#     Raises:
#         FileNotFoundError: If the JSON file does not exist at the expected path.
#         ValueError: If the JSON file content is invalid or malformed.
#     """
#     test_dir = os.path.dirname(__file__)
#     data_path = os.path.abspath(os.path.join(test_dir, '..', '..', 'data', filename))
#
#     if not os.path.isfile(data_path):
#         raise FileNotFoundError(
#             f"\n🚫 {filename} not found at expected location:\n  {data_path}\n"
#             f"💡 Make sure the file exists under 'EcommerceAPI/data/'.\n"
#             f"🧭 Current working directory: {os.getcwd()}"
#         )
#     # If you’d rather not fail the test collection and skip scenarios when the file is missing:
#     # if not os.path.isfile(data_path):
#     #     print(f"⚠️ Warning: coupon_scenarios.json not found at {data_path}. No scenarios loaded.")
#     #     return []
#
#     with open(data_path, 'r', encoding='utf-8') as f:
#         try:
#             return json.load(f)
#         except json.JSONDecodeError as e:
#             raise ValueError(f"❌ JSON decoding failed: {e}\nCheck formatting in {data_path}")
