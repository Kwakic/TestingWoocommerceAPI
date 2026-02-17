from typing import List, Dict, Any

from EcommerceAPI.src.validators.shared.base_validators import (
    assert_resource_exists,
    assert_resource_matches_db,
    assert_single_resource_by_field,
)


def assert_customer_exists_in_api(customers: List[Dict[str, Any]], email: str) -> Dict[str, Any]:
    return assert_resource_exists(customers, identifier=email, field="email")


def assert_customer_matches_db(customer: Dict[str, Any], db_customer: Dict[str, Any]) -> None:
    assert_resource_matches_db(
        customer,
        db_customer,
        id_field_api="id",
        id_field_db="ID",
        email_field_api="email",
        email_field_db="user_email",
    )


def assert_single_customer_with_email(
        customers: List[Dict[str, Any]],
        email: str
) -> Dict[str, Any]:
    return assert_single_resource_by_field(customers, value=email, field="email")
