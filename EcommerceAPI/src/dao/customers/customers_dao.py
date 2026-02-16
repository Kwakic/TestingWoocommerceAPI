from EcommerceAPI.src.utilities.dbUtility import DBUtility
import logging
import random

from typing import Protocol, Optional, List, Dict, Any

logger = logging.getLogger(__name__)


# Data access object = (DAO)
class CustomersDAO(object):  # object in the parenthesis will inherit objects by default in Python 3
    """
    Data Access Object for customers (wp_users table).
    """

    def __init__(self):
        self.db_helper = DBUtility()
        self.table_name = f"{self.db_helper.database}.{self.db_helper.table_prefix}users"

    def get_customer_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single customer by their email address.
        Args:
            email: Email address (should be unique).
        Returns:
            Dictionary with customer fields or None if not found.
        """

        # Validate input email — it must be a non-empty string
        if not isinstance(email, str) or not email.strip():
            raise ValueError("Invalid email provided. Must be a non-empty string.")
        # .strip(): This is a built-in Python string method that removes leading and trailing
        # whitespace from the string. Defensive programming: prevents bugs caused by input like " user@domain.com ".
        # Prevents unnecessary query failures or false negatives when whitespace is not trimmed.

        # Define the query using a parameterized %s placeholder. `LIMIT 1` ensures we return only one user (email should
        # be unique anyway)
        sql = f"SELECT * FROM {self.table_name} WHERE user_email = :email LIMIT 1;"

        # Parameters must be passed as a tuple (even if there's just one value)
        params = {"email": email.strip()}  # Ensures we pass a tuple with 1 element to execute()
        # 🔁 Tuple Use: (email.strip(),)
        # Note the comma: ( ... , ) In Python, ('value') is just a string. But ('value',) is a 1-element tuple — which
        # is required for execute(sql, params) to work correctly with 1 param.

        # Now we need to execute the query. For that, we will use the package called 'PyMySQL' and we write a code in
        # 'dbUtility.py' file. It doesn't have sense to write code to access a database to create connection, get
        # credentials, etc. Instead, we create a DB helper class 'dbUtility.py' because every connection will need
        # that(repetitive).
        try:
            rs_sql = self.db_helper.execute_select(sql, params)  # Execute the query securely with the parameter
            if not rs_sql:  # Handle a case when no result is found
                logger.info(f" 🔍Verifying DB. NO customer found for email: '{email}'")
                return None

            customer = rs_sql[0]  # Return the first (and only) result from the list
            logger.debug(f"Found customer for email '{email}': {customer}")  # Log the result at debug level
            return customer  # Always returns a single dict or None (not a list)

        except Exception as e:  # Log and re-raise any database or logic error
            logger.exception(f"Error retrieving customer by email '{email}': {e}")  # The only thing you might want to
            # do: use logger.exception(...) inside your except blocks instead of logger.error(...) with str(e).
            # logger.exception automatically includes the stack trace, which is helpful for test/debug environments.
            raise

        # | Feature                      | Description                                                              |
        # | ---------------------------- | ------------------------------------------------------------------------ |
        # | **Secure Query**             | Uses `WHERE user_email = %s` with a parameter tuple                      |
        # | **Input Validation**         | Raises error if email is not a clean string                              |
        # | **Safe Execution**           | Wrapped in `try/except` with clear logging                               |
        # | **Efficient**                | Uses `LIMIT 1` — avoids loading more rows than necessary                 |
        # | **Consistent Return Format** | Always returns a **dict** (if found) or `None` (if not)                  |
        # | **Logging**                  | Uses `info` when nothing found, `debug` for result, `error` on exception |

    def soft_delete_customer_by_id(self, customer_id: int) -> int:
        """
        Soft-deletes a customer by setting `user_status` to 1.

        :param customer_id: ID of the customer to soft-delete_it.py.
        :return: Number of rows affected (should be 1 if successful).
        :raises ValueError: If customer_id is invalid.
        :raises Exception: If the database update fails.

        Returns:
            Number of rows affected (should be 1 if successful).
        """
        if not isinstance(customer_id, int) or customer_id <= 0:
            raise ValueError(f"Invalid customer ID: {customer_id}. Must be a positive integer.")
        sql = f"UPDATE {self.table_name} SET user_status = 1 WHERE ID = :id"
        params = {"id": customer_id}
        try:
            rows_affected = self.db_helper.execute_sql(sql, params)
            log_msg = f"Soft-deleting customer ID={customer_id} → Rows affected: {rows_affected}"
            if rows_affected == 1:
                logger.info(f"✅ {log_msg}")
            else:
                logger.warning(f"⚠️ {log_msg}")
            return rows_affected
        except Exception as e:
            logger.exception(f"❌ Failed to soft-delete_it.py customer ID={customer_id}: {e}")
            raise

    def get_customer_by_id(self, customer_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a customer by their ID.
        Args:
            customer_id: Customer ID.
        Returns:
            Dictionary with customer fields or None if not found.
        """
        if not isinstance(customer_id, int) or customer_id <= 0:
            raise ValueError("Invalid customer ID provided.")
        sql = f"SELECT * FROM {self.table_name} WHERE ID = :id LIMIT 1"
        params = {"id": customer_id}
        try:
            results = self.db_helper.execute_select(sql, params)
            return results[0] if results else None
        except Exception as e:
            logger.exception(f"Error retrieving customer by ID '{customer_id}': {e}")
            raise

    def get_random_customer_from_db(self, qty: int = 1, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Retrieve random customer(s) from the last 5000 entries, optionally filtered by fields in wp_users.
        Args:
            qty: number of random customers to retrieve
            filters: optional, dictionary of filters (e.g., {'user_status': 0, 'user_login': 'admin'})
        Returns:
            List of randomly selected customers

        Note: For this particular test case, we need only one customer, but in the future we might need multiple
        customers, so that's we specified the quantity (qty). This function's job is to randomly pick one or more
        customers from the database.
        """

        # 🔐 Step-by-Step
        #     ✅ Define a VALID_FILTER_COLUMNS set with the allowed columns.
        #     ✅ Check that each key in filters is in this set.
        #     ❌ If not, raise a ValueError with a clear message.
        #     ✅ Continue building the WHERE clause only for valid keys.

        # We enhance the method with a column whitelist to prevent:
        #     - Typos in filter keys
        #     - SQL injection via column names
        #     - Runtime errors from invalid field names
        VALID_FILTER_COLUMNS = {
            "ID", "user_login", "user_email", "user_status", "user_nicename", "user_url", "user_registered",
            "display_name", "user_activation_key"
        }

        # It prepares the global query. If you want to filter by something like user_status = 0, the where_clauses will
        # contain "user_status = %s" and params will contain [0].
        base_sql = f"SELECT * FROM {self.table_name}"
        where_clauses = []
        params = {}

        # Dynamically builds the WHERE clause based on the provided filters.
        # Example:
        #     - Input: filters={'user_status': 0, 'user_login': 'testuser_ugiyygevho'}
        #     - Result:
        #         SQL: "WHERE user_status = %s AND user_login = %s"
        #         Params: [0, 'testuser_ugiyygevho']
        if filters:
            for column, value in filters.items():
                if column not in VALID_FILTER_COLUMNS:
                    raise ValueError(
                        f"Invalid filter column '{column}'. "
                        f"Allowed columns are: {', '.join(sorted(VALID_FILTER_COLUMNS))}"
                    )
                where_clauses.append(f"{column} = :{column}")
                params[column] = value

        if where_clauses:  # If filters exist, adds them to the query string.
            base_sql += " WHERE " + " AND ".join(where_clauses)

        # It finalizes the SQL query:
        base_sql += " ORDER BY id DESC LIMIT 5000;" # recommended way to retrieve the last user; then we randomize in
        # our python code
        try:
            rs_sql = self.db_helper.execute_select(base_sql, params)  # The response will return a list. It uses
            # DBUtility to execute the query securely with placeholders. This avoids SQL injection.
            if not rs_sql:  # ❗ Check for Empty Result.
                logger.warning(f"No customers found with filters: {filters}")
                return []  # Defensive programming: if the query returns nothing, log a warning and return an empty list
            qty = int(qty)  # 🔢Convert and Validate qty. Ensures qty is an integer (in case the caller passed a string)
            if qty > len(rs_sql):  # If the requested quantity is more than what's available, it returns the entire list
                # and logs a warning. Prevents random.sample() from raising a ValueError. E.g., If qty=10 but the result
                # has only 2 users, it logs a warning and returns both.
                logger.warning(f"Requested {qty} customers, but only {len(rs_sql)} available. Returning all.")
                return rs_sql
            selected_customers = random.sample(rs_sql, qty)  # Randomly selects users from the list without replacement
            # (i.e., no duplicates). random.sample(population, k) guarantees a uniformly random subset of size k. No
            # duplicates, unlike random.choices.
            logger.debug(f"Randomly selected {qty} customer(s) with filters {filters}: {selected_customers}")
            return selected_customers  # Logs the selected subset of customers (at debug level). Returns the random
            # selection back to the caller.

        except Exception as e:
            logger.exception(f"Error retrieving random customer(s) with filters {filters}: {e}")
            raise  # If anything goes wrong during the query or selection:
            # - Logs the exception at error level.
            # - Re-raises it so the caller can handle it (or it can fail loudly in tests).

    # ✅ Example:
    # If you call: get_random_customer_from_db(qty=1, filters={"user_status": 0})
    # It could randomly return either of:
    #     - testuser_ugiyygevho
    #     - testuser_jmkwuydjcp
    # Because both have user_status = 0 and appear in the latest 5000 entries.

    #  ✅ Example Usage
    # 1. Get one random active user: dao.get_random_customer_from_db(filters={"user_status": 0})
    # 2. Get three random administrators: dao.get_random_customer_from_db(qty=3, filters={"user_login": "admin"})

    # 🧪 Example Call (Valid)
    # customers = dao.get_random_customer_from_db(qty=2, filters={"user_status": 0,"user_login": "testuser_ugiyygevho"})
    # ✅ Works and builds a safe query like:
    # SELECT * FROM wp_users WHERE user_status = %s AND user_login = %s ORDER BY ID DESC LIMIT 5000;

    # ❌ Example Call (Invalid Filter Key)
    # dao.get_random_customer_from_db(filters={"user_role": "admin"})
    # Raises:
    # ValueError: Invalid filter column 'user_role'. Allowed columns are: ID, display_name, user_activation_key, ...

    # 📌 Advantages
    # | Feature         | Benefit                              |
    # | --------------- | ------------------------------------ |
    # | Dynamic filters | Easily extend to new columns         |
    # | Secure queries  | Prevent SQL injection                |
    # | Maintainable    | Centralized WHERE clause logic       |
    # | Reusable        | Can plug into multiple test contexts |
