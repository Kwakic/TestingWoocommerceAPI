import pytest

pytestmark = [pytest.mark.integration]


@pytest.mark.tcid("TCID-011")
@pytest.mark.e2e
@pytest.mark.regression
def test_customer_full_lifecycle(
    customer_helper, customers_dao, create_valid_customer, all_resources
):
    # -------------------------------------------
    # 🛠 STEP 1 — CREATE
    # -------------------------------------------
    customer = create_valid_customer()
    customer_id = customer["id"]
    email = customer["email"]

    # VERIFY CREATED (API + DB)
    customer_helper.assert_customer_exists_and_matches_db(email, customers_dao)

    # -------------------------------------------
    # 🔁 STEP 2 — UPDATE
    # -------------------------------------------
    updated_email = f"updated_{email}"

    update_response = customer_helper.update_customer(
        customer_id, payload={"email": updated_email}, return_http_response=True
    )

    # FAIL FAST
    assert (
        update_response.status_code == 200
    ), f"Update failed: {update_response.status_code} → {update_response.text}"

    # VERIFY UPDATED (API + DB)
    customer_helper.assert_customer_exists_and_matches_db(updated_email, customers_dao)

    # -------------------------------------------
    # 🧹 STEP 3 — DELETE
    # -------------------------------------------
    delete_response = customer_helper.delete_customer(
        customer_id, return_http_response=True
    )

    # FAIL FAST
    assert (
        delete_response.status_code == 200
    ), f"Delete failed: {delete_response.status_code} → {delete_response.text}"

    # Prevent teardown double-delete
    all_resources.mark_deleted("customers", customer_id)

    # -------------------------------------------
    # 🔎 STEP 4 — VERIFY DELETED (API)
    # -------------------------------------------
    response = customer_helper.get_customer_by_id(
        customer_id, return_http_response=True
    )

    assert (
        response.status_code == 404
    ), f"Expected 404 after deletion, got {response.status_code}"

    # -------------------------------------------
    # 🗄 STEP 5 — VERIFY DELETED (DB)
    # -------------------------------------------
    db_customer = customers_dao.get_customer_by_email(updated_email)
    assert not db_customer, "❌ Customer still exists in DB after deletion"
