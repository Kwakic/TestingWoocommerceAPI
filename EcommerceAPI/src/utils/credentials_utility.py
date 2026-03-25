import os


class MissingCredentialsError(Exception):
    """
    Custom error: Easier to catch and test MissingCredentialsError.
    """

    pass


def get_wc_api_keys():
    wc_key = os.environ.get("WC_KEY")
    wc_secret = os.environ.get("WC_SECRET")
    if not wc_key or not wc_secret:
        raise MissingCredentialsError(
            "Set WC_KEY and WC_SECRET in environment or .env file."
        )
    return {"wc_key": wc_key, "wc_secret": wc_secret}


def get_db_credentials():
    db_user = os.environ.get("DB_USER")
    db_password = os.environ.get("DB_PASSWORD")
    db_host = os.environ.get("DB_HOST")
    db_port = os.environ.get("DB_PORT")
    db_name = os.environ.get("DB_DATABASE")
    db_table_prefix = os.environ.get("DB_TABLE_PREFIX", "")
    db_socket = os.environ.get("DB_SOCKET", "")
    if not all([db_user, db_password, db_host, db_port, db_name]):
        raise MissingCredentialsError(
            "Set DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_DATABASE in environment or .env "
            "file."
        )
    return {
        "user": db_user,
        "password": db_password,
        "host": db_host,
        "port": int(db_port),
        "database": db_name,
        "table_prefix": db_table_prefix,
        "socket": db_socket,
    }
