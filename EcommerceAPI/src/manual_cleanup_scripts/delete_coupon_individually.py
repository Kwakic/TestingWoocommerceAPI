# from EcommerceAPI.src.helpers.wooNOTUSED_coupons_helper import CouponsHelper
#
# import logging as logger
#
# """
# The WooCommerce doesn't support bulk deletion of coupons via a list of IDs in a single call. So your safest route is to:
#     - Fetch the coupons (optionally with filters like name prefix or date).
#     - Loop over the returned list.
#     - Call the 'delete_it.py' endpoint for each coupon, with 'force=true'.
# """
#
#
# def delete_coupons_by_code_suffix(suffix="50off"):
#     helper = CouponsHelper()
#     coupons = helper.call_list_all_coupons(params={"per_page": 100})
#     import pdb;pdb.set_trace()
#
#     # Check if Coupons Are Being Fetched
#     # print(f"Fetched {len(coupons)} coupons")
#
#     for coupon in coupons:
#         code = coupon['code']
#         coupon_id = coupon['id']
#         if code.endswith(suffix):  # If you want to match anything that contains "tcid" (not just ends with it),
#             # you could change this line: "if suffix.lower() in code.lower():"
#             try:
#                 helper.call_delete_coupon(coupon_id, params={"force": True})
#                 logger.info(f"Deleted coupon: {code} (ID: {coupon_id})")
#             except Exception as e:
#                 logger.warning(f"Failed to delete_it.py coupon {coupon_id}: {e}")
#
#
# if __name__ == '__main__':
#     logger.basicConfig(level=logger.INFO)
#     delete_coupons_by_code_suffix(suffix="tcid37")  # Change suffix if needed
#
# # or run this query in your SQL:
# # DELETE FROM wp_posts WHERE post_type = 'shop_coupon' AND post_status = 'trash' AND post_title LIKE '%tcid%';
