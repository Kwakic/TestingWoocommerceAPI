
def filter_out_soft_deleted(
    items: list[dict],
    get_db_record_fn,
    id_field: str = "email",
    deleted_flag: str = "user_status",
    deleted_value: int = 1
) -> list[dict]:
    """
    Generic filter to remove soft-deleted entities based on DB flag.

    What this function REALLY is:
    "Soft-deleted entities should be excluded"

    Use it in your test:
        filtered_customers = filter_out_soft_deleted(
        items=raw_customers,
        get_db_record_fn=customers_dao.get_customer_by_email,
        id_field="email",
        deleted_flag="user_status",
        deleted_value=1
    )
    """

    filtered = []

    for item in items:
        identifier = item.get(id_field)

        db_record = get_db_record_fn(identifier)

        if not db_record:
            continue

        if db_record.get(deleted_flag) == deleted_value:
            continue

        filtered.append(item)

    return filtered
