from os import getenv
import logging
from time import sleep

import pandas as pd
from sqlalchemy import create_engine, delete, inspect
from sqlalchemy import Table, MetaData
from sqlalchemy.sql import text as sa_text

try:
    import pyodbc
except ImportError:
    pyodbc = None


class DataWarehouseConnector:
    """Child class that inherits from Connection with specific configuration
        for connecting to MS SQL."""

    def __init__(
        self, schema=None, port=None, server=None, db=None, user=None, pwd=None, driver=None
    ):
        self.server = server or getenv("MS_SERVER") or getenv("DB_SERVER")
        self.port = port or getenv("MS_PORT") or getenv("DB_PORT") or "1433"
        self.db = db or getenv("MS_DB") or getenv("DB")
        self.user = user or getenv("MS_USER") or getenv("DB_USER")
        self.pwd = pwd or getenv("MS_PWD") or getenv("DB_PWD")
        self.schema = schema or getenv("MS_SCHEMA") or getenv("DB_SCHEMA") or "dbo"
        self.driver = driver or getenv("MS_DRIVER") or self._get_driver()
        cstr = f"mssql+pyodbc://{self.user}:{self.pwd}@{self.server}:{self.port}/{self.db}?driver={self.driver}"
        self.engine = create_engine(cstr, fast_executemany=True)

    @staticmethod
    def _get_driver():
        return pyodbc.drivers()[-1].replace(" ", "+")

    def truncate(self, tablename):
        sql_str = f"TRUNCATE TABLE {self.schema}.{tablename}"
        command = sa_text(sql_str).execution_options(autocommit=True)
        self.engine.execute(command)

    def exec_sproc(self, stored_procedure, autocommit=False):
        sql_str = f"EXEC {self.schema}.{stored_procedure}"
        command = sa_text(sql_str).execution_options(autocommit=autocommit)
        with self.engine.begin() as connection:
            result = connection.execute(command)
        sleep(5)  # sleeping to let the sproc finish
        return result

    def insert_into(self, table, df, if_exists="append", chunksize=None, dtype=None):
        with self.engine.begin() as connection:
            df.to_sql(name=table, schema=self.schema, con=connection, if_exists=if_exists, chunksize=chunksize, dtype=dtype, index=False)

    def exec_cmd(self, command):
        with self.engine.begin() as conn:
            command = sa_text(command)
            result = conn.execute(command)
        return result
