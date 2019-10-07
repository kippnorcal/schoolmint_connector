import argparse
import datetime as dt
import glob
import logging
import os
import sys
import time
import traceback

import pandas as pd
from sqlsorcery import MSSQL
from tenacity import *

from api import API
from ftp import FTP
from mailer import Mailer

LOCALDIR = "files"
SOURCEDIR = "schoolmint"


logging.basicConfig(
    handlers=[
        logging.FileHandler(filename="app.log", mode="w+"),
        logging.StreamHandler(sys.stdout),
    ],
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %I:%M:%S%p %Z",
)


def read_logs(filename):
    with open(filename) as f:
        return f.read()


def read_csv_to_df(csv):
    """ Read the csv into a dataframe in preparation for database load """
    if not os.path.isfile(csv):
        raise Exception(
            f"ERROR: '{csv}' file does not exist. Most likely problem downloading from sFTP."
        )
    df = pd.read_csv(csv, sep=",", quotechar='"', doublequote=True, dtype=str, header=0)
    count = len(df.index)
    if count == 0:
        raise Exception(f"ERROR: No data was loaded from CSV file '{csv}'.")
    else:
        logging.info(f"{count} rows successfully imported from CSV file '{csv}'.")
    return df


def backup_and_truncate_table(conn, prep_sproc):
    """ Execute the prep sproc, which truncates the primary table. """
    result = conn.exec_sproc(prep_sproc)
    count = result.fetchone()[0]
    if count == 0:
        return True
    else:
        raise Exception(f"ERROR: Table {table} was not truncated.")


def get_records_count(conn, schema, table):
    """ Count the number of records in a given table. """
    result = conn.query(f"SELECT COUNT(1) records FROM {schema}.{table};")
    count = result["records"].values[0]
    return count


def load_from_backup_table(conn, schema, table):
    """
    Load data from backup table to primary table,
    only when there was an issue loading the csv into the primary table.
    """
    sql_insert = f"INSERT INTO {schema}.{table} SELECT * FROM {schema}.{table}_backup;"
    result = conn.query(sql_insert)
    count = get_records_count(conn, schema, table)
    raise Exception(
        f"ERROR: No rows loaded into {table}. {count} records reverted from backup table."
    )


def check_table_load(conn, schema, table):
    """ Ensure data was loaded successfully into the primary table. """
    count = get_records_count(conn, schema, table)
    if count == 0:
        load_from_backup_table(conn, schema, table)
    else:
        backup_count = get_records_count(conn, schema, f"{table}_backup")
        logging.info(
            f"{backup_count} rows successfully loaded into backup table {table}_backup."
        )
        logging.info(f"{count} rows successfully loaded into table {table}.")


def delete_data_files(directory):
    """ Delete data files (not everything) from the given directory """
    for file in os.listdir(directory):
        if "Data" in file:
            os.remove(os.path.join(directory, file))


def get_todays_file(filename):
    """ Get the file that matches the given name.
    Assume there is only one since we archived the others. """
    files = os.listdir(LOCALDIR)
    matching_file = [file for file in files if filename in file]
    if matching_file:
        logging.info(f"'{filename}' successfully downloaded.")
        return matching_file[0]
    else:
        raise Exception(f"Error: '{filename}' was not downloaded.")


@retry(wait=wait_fixed(30), stop=stop_after_attempt(60))
def download_from_ftp(ftp):
    """
    Download data files from FTP.
    
    It can take some time for SchoolMint to upload the reports after the API request,
    so we use Tenacity retry to wait up to 30 min.
    """
    ftp.download_dir(SOURCEDIR, LOCALDIR)
    app_file = get_todays_file("Automated Application Data Raw")
    app_index_file = get_todays_file("Automated Application Data Index")
    return app_file, app_index_file


def process_application_data(conn, schema, file):
    """ Take application data from csv and insert into table """
    df = read_csv_to_df(f"{LOCALDIR}/{file}")
    if backup_and_truncate_table(conn, os.getenv("SPROC_RAW_PREP")):
        table = os.getenv("DB_RAW_TABLE")
        conn.insert_into(table, df)
        check_table_load(conn, schema, table)


def process_application_data_index(conn, schema, file):
    """ Take application data index from csv and insert into table """
    df = read_csv_to_df(f"{LOCALDIR}/{file}")
    if backup_and_truncate_table(conn, os.getenv("SPROC_RAW_INDEX_PREP")):
        table = os.getenv("DB_RAW_INDEX_TABLE")
        conn.insert_into(table, df)
        check_table_load(conn, schema, table)


def process_change_tracking(conn):
    """ Generate Change History """
    SchoolYear4Digit = os.getenv("SchoolYear4Digit", "2021")
    Enrollment_Period = os.getenv("Enrollment_Period", "2021")
    # sproc=f"sproc_SchoolMint_Create_ChangeTracking_Entries '{SchoolYear4Digit}','{Enrollment_Period}'"
    sproc = os.getenv("SPROC_CHANGE_TRACK")

    result = conn.exec_sproc(sproc)
    ChangeTrackingInsertedRowCT = result.fetchone()[0]
    logging.info(
        f"{ChangeTrackingInsertedRowCT} Rows Successfully Loaded into Change Log"
    )


def process_FactDailyStatus(conn):
    """ Generate Fact Daily Status """
    SchoolYear4Digit = os.getenv("SchoolYear4Digit", "2021")
    # sproc=f"sproc_SchoolMint_Create_FactDailyStatus '{SchoolYear4Digit}'"
    sproc = os.getenv("SPROC_FACT_DAILY")

    result = conn.exec_sproc(sproc)
    FactDailyStatusInsertedRowCT = result.fetchone()[0]
    logging.info(
        f"{FactDailyStatusInsertedRowCT} Rows Successfully Loaded into FactDailyStatus"
    )


def main():
    try:
        schema = os.getenv("DB_SCHEMA")
        conn = MSSQL()
        mailer = Mailer()
        ftp = FTP()

        # get files
        ftp.archive_remote_files(SOURCEDIR)
        API().request_reports()
        if eval(os.getenv("DELETE_LOCAL_FILES", "True")):
            delete_data_files(LOCALDIR)
        app_file, app_index_file = download_from_ftp(ftp)

        process_application_data(conn, schema, app_file)
        process_application_data_index(conn, schema, app_index_file)

        # process_change_tracking(conn)
        # process_FactDailyStatus(conn)

        success_message = read_logs("app.log")
        mailer.notify(results=success_message)
    except Exception as e:
        logging.exception(e)
        stack_trace = traceback.format_exc()
        mailer.notify(success=False, error_message=stack_trace)


if __name__ == "__main__":
    main()
