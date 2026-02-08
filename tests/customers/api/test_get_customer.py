# import pytest
# import logging
#
# from jsonschema import validate
# from json import loads
#
# from tests.customers.schemas.customer import error_schema
#
#
# logger = logging.getLogger(__name__)
# #  logger.setLevel(logging.DEBUG)  # already set in pytest.ini
#
# pytestmark = [pytest.mark.customers, pytest.mark.regresion]
#
#
# @pytest.mark.customers
# @pytest.mark.tcid13
# def test_get_customer_by_email(all_resources, create_valid_customer):
#     """
#     Validate that a created customer can be retrieved by email (a custom query like GET /customers?email={email}).
#     Verifies:
#     - POST /customers creates a customer
#     - GET /customers/{id} returns the correct customer data
#     - Schema validation for GET response
#     - Data consistency between DB and API
#     :param all_resources:
#     :param create_valid_customer:
#     :return:
#     """
#
#     # -------------------------------------------
#     # 🔧 Access helpers and DAOs from test setup
#     # -------------------------------------------
#
#     customer_helper = all_resources.entities["customers"].helper  # High-level API helper
#     dao = all_resources.entities["customers"].dao  # DAO: Database Access Object for direct DB queries
#
#     # -------------------------------
#     #  ✅ Create customer via fixture factory
#     # -------------------------------
#     logger.info("🛠 Creating a test customer via factory fixture.")
#     # To keep the customer in the DB (i.e., skip deletion), pass: customer = create_customer_for_test(skip_cleanup=True)
#     customer = create_valid_customer()
#     customer_id = customer["id"]
#     email = customer["email"]
#     # Early assert for id and email ensures immediate failure if response is malformed.
#     assert customer_id is not None, "❌ Customer ID not returned"
#     assert email is not None, "❌ Customer Email not returned"
#     logger.info(f"✅ Assertion passed: Customer created: ID={customer_id}, Email={email}")
#
#     # ------------------------------------------------------------------
#     # 📋 Schema Validation (It checks that the POST response is valid)
#     # ------------------------------------------------------------------
#     customer_helper.validate_customer_response_schema(customer=customer)
#
#     # ---------------------------------------------------------------------------------------------------------
#     # 🔍 Confirm customer exists in DB and API GET response matches DB.
#     # 🧩 Schema Validation (it checks that the GET response is valid).
#     # ---------------------------------------------------------------------------------------------------------
#     customer_helper.validate_customer_exists_and_matches(email=email, dao=dao)
#     logger.info(f"🎯 Full validation complete for customer ID={customer_id}")
#
#
# @pytest.mark.tcid14
# def test_get_customer_by_id(all_resources, create_valid_customer):
#     """
#     Validate that a created customer can be retrieved by ID (validates the endpoint GET /customers/{id}).
#     Verifies:
#     - POST /customers creates a customer
#     - GET /customers/{id} returns the correct customer data
#     - Schema validation for GET response
#     - Data consistency between DB and API
#     """
#     # -------------------------------------------
#     # 🔧 Access helpers and DAOs from test setup
#     # -------------------------------------------
#     customer_helper = all_resources.entities["customers"].helper
#     dao = all_resources.entities["customers"].dao
#
#     # -------------------------------
#     # ✅ Create customer via fixture factory
#     # -------------------------------
#     logger.info("🛠 Creating a test customer for retrieval by ID.")
#     customer = create_valid_customer()
#     customer_id = customer["id"]
#     email = customer["email"]
#     assert customer_id, "❌ Customer ID not returned"
#     assert email, "❌ Customer Email not returned"
#     logger.info(f"✅ Created customer: ID={customer_id}, Email={email}")
#
#     # ------------------------------------------------------------------
#     # 📋 Schema Validation (It checks that the POST response is valid)
#     # ------------------------------------------------------------------
#     customer_helper.validate_customer_response_schema(customer=customer)
#
#     # ------------------------------------------------------------
#     # 🔍 Get customer by ID and validate
#     # ------------------------------------------------------------
#     logger.info(f"🔎 Fetching customer by ID: {customer_id}")
#     customer_from_get = customer_helper.call_get_customer_by_id(customer_id)
#     assert customer_from_get["id"] == customer_id, (f"❌ Mismatched ID: Expected {customer_id}, "
#                                                     f"got {customer_from_get['id']}")
#     assert customer_from_get["email"] == email, (f"❌ Mismatched email: Expected {email}, "
#                                                  f"got {customer_from_get['email']}")
#     logger.info(f"✅ Fetched customer by ID matches created one: ID={customer_id}, Email={email}")
#
#     # ------------------------------------------------------------------
#     # 📋 Schema Validation (GET response)
#     # ------------------------------------------------------------------
#     # The validate_customer_response_schema(customer_from_get) is validating the response from: GET /customers/{id}
#     customer_helper.validate_customer_response_schema(customer=customer_from_get)
#
#     # ------------------------------------------------------------------
#     # 🧩 Use helper to validate list endpoint and DB consistency
#     # ------------------------------------------------------------------
#     # The validate_customer_response_schema(customer_from_get) is validating the response from: GET /customers?email=...
#     customer_helper.validate_customer_exists_and_matches(email=email, dao=dao)
#     logger.info(f"🎯 Full validation complete for customer ID={customer_id}")
#
#
# @pytest.mark.negative_test
# @pytest.mark.tcid17
# def test_retrieve_nonexistent_customer_returns_404(all_resources, create_valid_customer):
#     """
#      🚫  Attempt to GET a nonexistent customer.
#     - Expect 404
#     - Validate error schema
#     """
#     customer_helper = all_resources.customer.helper
#     fake_customer_id = 99999999
#
#     logger.info(f"🚫 Retrieving non-existent customer ID: {fake_customer_id}")
#     response = customer_helper.call_get_customer_by_id(customer_id=fake_customer_id, expected_status_code=404)
#
#     if isinstance(response, str):
#         response = loads(response)
#
#     assert response['code'] == 'woocommerce_rest_invalid_id', "❌ Error 'code' should not be empty"
#     assert response['message'], "❌ Error 'message' should not be empty"
#
#     validate(instance=response, schema=error_schema)
#     logger.info("✅ Error response schema validated for non-existent customer fetch")
#
#
#
#
