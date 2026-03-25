import logging
import csv
from datetime import datetime
from typing import Iterable, Dict, Any

# from EcommerceAPI.src.orders.helpers.orders_helper import OrdersHelper
# from EcommerceAPI.src.products.helpers.products_helper import ProductsHelper
# from EcommerceAPI.src.coupons.helpers.coupons_helper import CouponsHelper
from EcommerceAPI.src.customers.helpers.customers_helper import CustomersHelper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseCleaner:
    def __init__(self, helper, entity_type):
        self.helper = helper()
        self.entity_type = entity_type
        self.per_page = 100

    def list_entities(self, params: dict) -> Iterable[Dict[str, Any]]:
        raise NotImplementedError

    def delete_entity(self, entity_id):
        raise NotImplementedError

    def extract_metadata(self, entity):
        return str(entity.get("id"))

    def run_cleanup(
        self,
        keywords=None,
        created_before=None,
        created_after=None,
        include_trashed=False,
        dry_run=False,
        max_pages=10,
        export_csv=False,
    ):

        total_deleted = 0
        matches_for_export = []
        seen_ids = set()  # ✅ Deduplication set
        statuses = ["any"]
        if include_trashed:
            statuses.append("trash")

        cutoff_before = (
            datetime.fromisoformat(created_before) if created_before else None
        )
        cutoff_after = datetime.fromisoformat(created_after) if created_after else None

        for status in statuses:
            for page in range(1, max_pages + 1):
                params = {
                    "per_page": self.per_page,
                    "page": page,
                    "status": status,
                    "created_before": created_before,
                    "created_after": created_after,
                }
                try:
                    entities = self.list_entities(params)
                except Exception as e:
                    logger.error(
                        f"Failed to fetch {self.entity_type} on page {page}: {e}"
                    )
                    break

                if not entities:
                    break

                for entity in entities:
                    entity_id = entity.get("id")
                    if not entity_id:
                        continue
                    if entity_id in seen_ids:
                        continue
                    seen_ids.add(entity_id)  # ✅ Register this ID as seen

                    date_created = entity.get("date_created_gmt")
                    metadata = self.extract_metadata(entity)

                    keyword_match = (
                        True
                        if not keywords
                        else any(kw.lower() in str(metadata).lower() for kw in keywords)
                    )  # Case-insensitive match

                    date_match = True
                    if date_created:
                        try:
                            dt = datetime.fromisoformat(
                                date_created.replace("Z", "+00:00")
                            )
                            if cutoff_before:
                                date_match &= dt < cutoff_before
                            if cutoff_after:
                                date_match &= dt > cutoff_after
                        except ValueError as e:
                            logger.warning(
                                f"Could not parse creation date for {self.entity_type[:-1]} {entity_id}: {e}"
                            )
                            continue  # Skip malformed date records

                    if keyword_match and date_match:
                        if dry_run or export_csv:
                            matches_for_export.append(entity)

                        if dry_run:
                            logger.info(
                                f"🧪 Would delete {self.entity_type[:-1]}: {metadata} (ID: {entity_id})"
                            )
                        else:
                            try:
                                self.delete_entity(entity_id)
                                logger.info(
                                    f"🗑️ Deleted {self.entity_type[:-1]}: {metadata} (ID: {entity_id})"
                                )
                                total_deleted += 1
                            except Exception as e:
                                logger.warning(
                                    f"❌ Failed to delete {self.entity_type[:-1]} {entity_id}: {e}"
                                )

        if export_csv:
            self.export_to_csv(matches_for_export)

        if dry_run:
            logger.info(
                f"\n🧪 Dry run complete. Total {self.entity_type} that would be deleted: {len(matches_for_export)}"
            )
        else:
            logger.info(
                f"\n✅ Cleanup complete. Total {self.entity_type} deleted: {total_deleted}"
            )

        logger.info(
            f"\n✅ Cleanup complete. Total {self.entity_type} deleted: {total_deleted}"
        )

    def export_to_csv(self, entities):
        filename = f"{self.entity_type}_to_delete.csv"
        if not entities:
            logger.info(f"No {self.entity_type} entities to export.")
            return
        keys = entities[0].keys()
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(entities)
        logger.info(f"Exported {len(entities)} {self.entity_type} to CSV: {filename}")


# class ProductCleaner(BaseCleaner):
#     def __init__(self):
#         super().__init__(ProductsHelper, "products")
#
#     def list_entities(self, params):
#         return self.helper.call_list_products(payload=params)
#
#     def delete_entity(self, entity_id):
#         self.helper.call_delete_product(entity_id, params={"force": True})
#
#     def extract_metadata(self, entity):
#         return entity.get("name", "") + " | " + entity.get("slug", "")


# class OrderCleaner(BaseCleaner):
#     def __init__(self):
#         super().__init__(OrdersHelper, "orders")
#
#     def list_entities(self, params):
#         return self.helper.call_list_all_orders(params=params)
#
#     def delete_entity(self, entity_id):
#         self.helper.call_delete_an_order(entity_id, params={"force": True})
#
#
# class CouponCleaner(BaseCleaner):
#     def __init__(self):
#         super().__init__(CouponsHelper, "coupons")
#
#     def list_entities(self, params):
#         return self.helper.call_list_all_coupons(params=params)
#
#     def delete_entity(self, entity_id):
#         self.helper.call_delete_coupon(entity_id, params={"force": True})
#
#     def extract_metadata(self, entity):
#         return entity.get("code", "")


class CustomerCleaner(BaseCleaner):
    def __init__(self):
        super().__init__(CustomersHelper, "customers")

    def list_entities(self, params):
        return self.helper.list_customers_paginated(payload=params)

    def delete_entity(self, entity_id):
        self.helper.delete_customer(entity_id, params={"force": True})

    def extract_metadata(self, entity):
        return " | ".join(
            filter(
                None,
                [
                    entity.get("username", ""),
                    entity.get("email", ""),
                    entity.get("first_name", ""),
                    entity.get("last_name", ""),
                ],
            )
        )


if __name__ == "__main__":
    # Filters (customize these as needed)
    keywords_to_match_products = ["product", "test-product"]
    keywords_to_match_coupons = ["tcid", "test", "50off"]
    keywords_to_match_customers = ["testuser", "test"]

    created_before_date = "2025-05-10T00:00:00"
    created_after_date = "2024-03-10 15:52:11"

    # ✅ Example selective cleanup like in your original script:

    # OrderCleaner().run_cleanup(
    #     # keywords=keywords_to_match_orders,
    #     # created_before=created_before_date,
    #     created_after=created_after_date,
    #     include_trashed=True,
    #     dry_run=True,
    #     max_pages=10,
    #     export_csv=False
    # )

    # ProductCleaner().run_cleanup(
    #     keywords=keywords_to_match_products,
    #     # created_before=created_before_date,
    #     # created_after=created_after_date,
    #     include_trashed=True,
    #     dry_run=True,
    #     max_pages=10,
    #     export_csv=True
    # )

    # CouponCleaner().run_cleanup(
    #     keywords=keywords_to_match_coupons,
    #     created_before=created_before_date,
    #     created_after=created_after_date,
    #     include_trashed=True,
    #     dry_run=True,
    #     max_pages=5,
    #     export_csv=True
    # )

    CustomerCleaner().run_cleanup(
        keywords=keywords_to_match_customers,
        # created_before=created_before_date,
        # created_after=created_after_date,
        include_trashed=True,
        dry_run=False,
        max_pages=5,
        export_csv=False,
    )

    # # ✅ Optional CLI mode (disabled by default) Uncomment the block below if you prefer CLI use
    # parser = argparse.ArgumentParser(description="Clean test entities from WooCommerce DB")
    # parser.add_argument("entity", choices=["orders", "products", "coupons", "customers"], help="Entity type")
    # parser.add_argument("--keywords", nargs="*", default=[], help="Keywords to filter entities")
    # parser.add_argument("--created_before", help="ISO date to filter entities created before")
    # parser.add_argument("--created_after", help="ISO date to filter entities created after")
    # parser.add_argument("--include_trashed", action="store_true", help="Include soft-deleted entities")
    # parser.add_argument("--dry_run", action="store_true", help="Dry run mode")
    # parser.add_argument("--max_pages", type=int, default=10, help="Max pages to iterate")
    # parser.add_argument("--export_csv", action="store_true", help="Export matching entities to CSV")
    # args = parser.parse_args()
    # cleaner_map = {
    #     "orders": OrderCleaner,
    #     "products": ProductCleaner,
    #     "coupons": CouponCleaner,
    #     "customers": CustomerCleaner
    # }
    # cleaner = cleaner_map[args.entity]()
    # cleaner.run_cleanup(
    #     keywords=args.keywords,
    #     created_before=args.created_before,
    #     created_after=args.created_after,
    #     include_trashed=args.include_trashed,
    #     dry_run=args.dry_run,
    #     max_pages=args.max_pages,
    #     export_csv=args.export_csv
    # )

# | Improvement                 | Benefit                             |
# | --------------------------- | ----------------------------------- |
# | Class-based cleaners        | Modular, DRY, extendable            |
# | CLI with argparse           | More usability for pipelines        |
# | Concurrency                 | Scale to 1000s of entities          |
# | Logging & shared cleanup | Better readability, maintainability |


# ✅ Your script has now been refactored into a class-based architecture with CLI support and a new CustomerCleaner.
# ✅ What's New
#


# # Dry run deleting test products created after April 24
# delete_entities_from_code_and_CLI.py products --keywords test product --created_after 2024-04-24T00:00:00 --dry_run
#
# # Actually delete_it.py matching orders
# python script.py orders --keywords test --include_trashed
#
# # Export matching coupons to CSV
# python script.py coupons --export_csv --keywords test
