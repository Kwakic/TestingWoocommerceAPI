# import pytest
# import logging
# from dateutil.parser import isoparse  # For robust ISO date parsing
# from jsonschema import validate
# from tests.customers.schemas.customer import customer_schema
# from EcommerceAPI.src.utilities.date_timestamp_utils import get_customers_in_window
#
# logger = logging.getLogger(__name__)
# #  logger.setLevel(logging.DEBUG)  # already set in pytest.ini
#
# # Apply global markers for the test module
# pytestmark = [pytest.mark.customers, pytest.mark.regression, pytest.mark.EndtoEnd]
#
#
# @pytest.mark.tcid07
# @pytest.mark.parametrize("minute_offset", [1, 5])
# def test_list_customers_created_within_time_range_with_db_check(all_resources, minute_offset: int,
#                                                                 create_valid_customer):
#     """
#     ✅ End-to-end positive test that creates a customer and verifies the customer is returned when querying
#     with a timestamp window that includes their creation time.
#
#     This test validates the /customers API filtering logic based on `created_after` and `created_before` query
#     parameters, ensuring accurate inclusion of newly created customers.
#
#     It also checks end-to-end correctness across multiple layers: API response schema, filter logic, and database consistency.
#
#     **Steps:**
#     1. ✅ Create a new customer via POST (fixture-based).
#     2. ✅ Validate POST response conforms to the expected schema.
#     3. ✅ Use server-generated `date_created_gmt` timestamp as the filter global.
#     4. ✅ Build a buffer window using `build_created_after_before_window` with `negative=False`.
#     5. ✅ Call GET /customers using the time filters.
#     6. ✅ Assert the created customer is included in the filtered results.
#     7. ✅ Validate that all returned customers conform to schema.
#     8. ✅ Assert customer exists in DB and matches API response.
#
#     **Why use the server-side `date_created_gmt` as base_time?**
#     - Prevents issues caused by client-server time drift.
#     - Ensures filtering window is tightly aligned with actual creation time.
#     - The `minute_offset` param allows re-running this test with different buffer sizes for robustness. It is used tO:
#         - Test robustness across different time windows.
#         - Validate the filter logic holds regardless of how wide the window is.
#         - Simulate realistic delays between resource creation and subsequent querying.
#         Minute_offset helps mitigate test flakiness due to:
#             - Timestamp rounding
#             - DB commit delays
#             - API cache propagation
#             - Eventual consistency
#
#
#     **Why this test matters: **
#     - Confirms API filtering includes valid recent data.
#     - Prevents false negatives in real-time dashboards or filtered views.
#     - Verifies the system's time-based filter logic across different services (API + DB).
#     """
#
#     # -------------------------------------------
#     # 🔧 Access helpers and DAOs from test setup
#     # -------------------------------------------
#     customer_helper = all_resources.customer.helper
#     dao = all_resources.customer.dao
#
#     # -------------------------------------------
#     # ✅ Create customer via fixture factory
#     # -------------------------------------------
#     logger.info("🛠 Creating a test customer via factory fixture.")
#     # To keep the customer in the DB (i.e., skip deletion), pass: customer = create_customer_for_test(skip_cleanup=True)
#     customer = create_valid_customer()
#     customer_id = customer["id"]
#     customer_email = customer["email"]
#     # Early assert for id and email ensures immediate failure if response is malformed.
#     assert customer_id is not None, "❌ Customer ID not returned"
#     assert customer_email is not None, "❌ Customer Email not returned"
#     logger.info(f"✅ Assertion passed: Customer created: ID={customer_id}, Email={customer_email}")
#
#     # ------------------------------------------------------------------
#     # 📋 Schema Validation (It checks that the POST response is valid)
#     # ------------------------------------------------------------------
#     customer_helper.validate_customer_response_schema(customer=customer)
#     # -------------------------------------------
#     # ⏱ Prepare created_after and created_before filters using server timestamp
#     # -------------------------------------------
#     created_at_str = customer.get("date_created_gmt")
#     assert created_at_str, "❌ 'date_created_gmt' missing in response"
#     created_at = isoparse(created_at_str)  # converted version is: datetime.datetime(2025, 7, 2, 19, 48, 33)
#
#     # -------------------------------------------
#     # 📞 Call GET /customers with date filters
#     # -------------------------------------------
#     # ✅ Use the utility with logging now included inside it. ⏳ Parse server timestamps the exact creation time from
#     # the customer response (in GMT) using ISO parser to avoid datetime bugs.
#     filtered_customers = get_customers_in_window(
#         helper=customer_helper,
#         created_at=created_at,
#         before_min=minute_offset,
#         after_min=1,
#         negative=False
#     )
#
#     # Validate that we got results from the filtered API
#     assert filtered_customers, "❌ No customers returned from GET /customers with date filters"
#     logger.info(f"✅ Assertion passed: Customers returned from filtered GET: count={len(filtered_customers)}")
#
#     # -------------------------------------------
#     # 🔍 Ensure created customer is in filtered response
#     # -------------------------------------------
#     returned_ids = [c["id"] for c in filtered_customers]
#     assert customer_id in returned_ids, f"❌ Customer ID {customer_id} not found in filtered results"
#     logger.info(f"✅ Customer ID {customer_id} found in filtered API list")
#
#     # -------------------------------------------
#     # 📋 Validate schema for each returned customer.
#     # -------------------------------------------
#     for cust in filtered_customers:
#         validate(instance=cust, schema=customer_schema)
#     logger.info("📦 All customers in filtered list passed schema validation")
#
#     # ---------------------------------------------------------------------------------------------------------
#     # 🔍 Confirm customer exists in DB and API GET response matches DB.
#     # 🧩 Schema Validation (it checks that the GET response is valid).
#     # ---------------------------------------------------------------------------------------------------------
#     customer_helper.validate_customer_exists_and_matches(email=customer_email, dao=dao)
#     logger.info(f"🎯 Full validation complete for customer ID={customer_id}")
#
#     # You were filtering with timestamps generated locally that didn’t match exactly the customer’s creation timestamp
#     # on the server. Using the server’s actual creation time with a small buffer ensured your filters correctly included
#     # the newly created customer and prevented timezone-related errors.
#
#     # I used the actual customer’s creation time from the API response (date_created_gmt):
#     # Instead of relying on your local clock, you read the real creation timestamp reported by the server, which is the
#     # most accurate reference for filtering.
#     # Parsed the timestamp with a robust parser (isoparse):
#     # This ensured the datetime was correctly interpreted as UTC-aware, handling the timezone info without errors.
#     # Added a buffer window around the creation time (e.g., minus minute_offset and plus 1 minute):
#     # This accounted for slight timing differences or delays between when the customer was created and when you queried
#     # with filters, ensuring the customer falls within the filter range.
#     # Formatted timestamps correctly with timezone info (Z for UTC):
#     # This avoided confusion or comparison errors between naive and aware datetimes on the server.
#
# # 🔒 Why This Is Important in Tests
# #     - Prevents flaky tests due to timing issues between client and server
# #     - Ensures that filtering logic includes the newly created customer
# #     - Avoids comparing naive vs. timezone-aware datetimes, which is a common pitfall in Python
#
#
# @pytest.mark.negative_test
# @pytest.mark.tcid08
# def test_customer_should_not_returned_when_filtered_outside_creation_time(all_resources,
#                                                                           create_valid_customer):
#     """
#     ❌ Negative test: Verify that a newly created customer is *excluded* when querying with a timestamp filter
#     that does *not* include the actual creation time.
#
#     **Scenario:**
#     - A customer is created at a known time (e.g., 16:20).
#     - The test builds a filter window *outside* that time (e.g., 16:21 to 16:22).
#        -> created_after: '2025-08-03T16:21:06'
#        -> created_at_str : '2025-08-03T16:20:06'
#        -> created_before: '2025-08-03T16:19:06'
#     - The API is queried with these filters.
#     - The test asserts that the customer does NOT appear in the response.
#
#     **Why this matters:**
#     - Confirms the backend respects `created_after` and `created_before` boundaries.
#     - Prevents future regressions where filters might silently include too much data.
#     - Protects data filtering correctness (e.g., dashboards, reports, date-based UIs).
#
#     Steps:
#     1. ✅ Create a test customer and get the server-side creation timestamp (`date_created_gmt`).
#     2. ✅ Build an inverted (negative) time window using `build_created_after_before_window(..., negative=True)`.
#     3. ✅ Call GET /customers with the negative window.
#     4. ✅ Assert the customer is NOT present in the response list.
#
#     """
#
#     customer_helper = all_resources.customer.helper
#
#     logger.info("🛠 Creating a test customer via factory fixture.")
#     # To keep the customer (i.e., skip deletion), pass: customer = create_customer_for_test(skip_cleanup=True)
#     customer = create_valid_customer()
#     customer_id = customer["id"]
#
#     created_at_str = customer.get("date_created_gmt")
#     assert created_at_str, "❌ 'date_created_gmt' missing in response"
#     created_at = isoparse(created_at_str)  # converted version is: datetime.datetime(2025, 7, 2, 19, 48, 33)
#
#     # -------------------------------------------
#     # 📞 Call GET /customers with date filters
#     # -------------------------------------------
#
#     # Use the utility with logging now included inside it. ⏳ Parse server timestamps the exact creation time from
#     # the customer response (in GMT) using ISO parser to avoid datetime bugs.
#     filtered_customers = get_customers_in_window(
#         helper=customer_helper,
#         created_at=created_at,
#         before_min=1,
#         after_min=1,
#         negative=True
#     )
#
#     returned_ids = [c["id"] for c in filtered_customers]
#
#     # Assert the created customer is NOT included when filtered outside its creation window
#     assert customer_id not in returned_ids, (
#         f"❌ Customer ID {customer_id} was incorrectly included in results filtered outside its creation time"
#     )
#
#     logger.info(f"✅ Customer ID {customer_id} correctly excluded from filtered API list")
