from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool
from EcommerceAPI.src.utilities.credentials_utility import get_db_credentials
import logging

logger = logging.getLogger(__name__)


class DBUtility:
    def __init__(self):
        creds = get_db_credentials()
        self.engine: Engine = create_engine(
            f"mysql+pymysql://{creds['user']}:{creds['password']}@{creds['host']}:{creds['port']}/{creds['database']}",
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_recycle=1800,
            pool_pre_ping=True,
        )
        self.table_prefix = creds['table_prefix']
        self.database = creds['database']

    def execute_select(self, sql: str, params=None):
        with self.engine.connect() as conn:
            result = conn.execute(text(sql), params or {})
            return [dict(row._mapping) for row in result]  # noinspection PyProtectedMember

    def execute_sql(self, sql: str, params=None):
        with self.engine.begin() as conn:
            result = conn.execute(text(sql), params or {})
            return result.rowcount

