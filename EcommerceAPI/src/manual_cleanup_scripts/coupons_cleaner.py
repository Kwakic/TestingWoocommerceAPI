from datetime import datetime
from EcommerceAPI.src.helpers.wooNOTUSED_coupons_helper import CouponsHelper

import logging as logger
logger.basicConfig(level=logger.INFO)


def delete_test_coupons(keywords: list[str], created_before: str = None):
    #  DON'T USE THIS SCRIPT IF it will be reused elsewhere. Only for STANDALONE!
    """
    Deletes coupons (including soft-deleted) whose codes contain specified keywords
    and were optionally created before a given date.

    Args:
        keywords (list[str]): List of substrings to match in coupon codes.
        created_before (str, optional): ISO 8601 date string (e.g., '2025-05-10T00:00:00').
    """
    coupon_helper = CouponsHelper()
    total_deleted = 0

    # Parse date if provided
    cutoff_date = None
    if created_before:
        try:
            cutoff_date = datetime.fromisoformat(created_before)
            logger.info(f"🗓️ Will delete coupons created before: {cutoff_date}")
        except ValueError:
            logger.error("❌ Invalid date format. Use ISO 8601 format: 'YYYY-MM-DDTHH:MM:SS'")
            return

    logger.info(f"🔍 Searching for coupons with keywords: {keywords}")

    def process_by_status(status: str):
        nonlocal total_deleted
        page = 1
        per_page = 100

        while True:
            coupons = coupon_helper.call_list_all_coupons(params={"status": status, "per_page": per_page, "page": page})
            if not coupons:
                break

            for coupon in coupons:
                code = coupon.get('code', '')
                coupon_id = coupon.get('id')
                created_gmt = coupon.get('date_created_gmt')

                keyword_match = any(keyword.lower() in code.lower() for keyword in keywords)

                date_match = True
                if created_gmt and cutoff_date:
                    try:
                        created_date = datetime.fromisoformat(created_gmt.replace('Z', '+00:00'))
                        date_match = created_date < cutoff_date
                    except ValueError:
                        logger.warning(f"⚠️ Could not parse 'date_created_gmt' for coupon {coupon_id}")
                        continue

                if keyword_match and date_match:
                    try:
                        coupon_helper.call_delete_coupon(coupon_id, params={"force": True})
                        logger.info(f"🗑️ Deleted [{status}] coupon: {code} (ID: {coupon_id})")
                        total_deleted += 1
                    except Exception as e:
                        logger.warning(f"❌ Failed to delete coupon {coupon_id} ({code}): {e}")
            page += 1

    # Process both active and trashed coupons
    process_by_status("any")
    process_by_status("trash")
    # status="any" covers all coupons regardless of publication status (draft, publish, etc.).
    # status="trash" specifically catches those that were soft-deleted.
    # force=True ensures permanent deletion.

    logger.info(f"\n✅ Cleanup complete. Total coupons deleted: {total_deleted}")


if __name__ == '__main__':
    # Customize before running
    keywords_to_match = ['tcid', 'test', '50off']
    created_before_date = '2025-05-10T00:00:00'  # Set to None to disable date filter

    delete_test_coupons(keywords=keywords_to_match, created_before=created_before_date)



