import argparse
from datetime import datetime
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
import ftp
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
    if not os.path.isfile(csv):
        raise Exception(
            f"ERROR: '{csv}' file does not exist. Most likely problem downloading from sFTP."
        )
    df = pd.read_csv(csv, sep=",", quotechar='"', doublequote=True, dtype=str, header=0)
    count = len(df.index)
    if count == 0:
        raise Exception(f"ERROR: No data was loaded from CSV file '{csv}'")
    else:
        logging.info(f"{count} rows successfully imported from CSV file '{csv}'")
    return df


def backup_and_truncate_table(conn, prep_sproc):
    result = conn.exec_sproc(prep_sproc)
    count = result.fetchone()[0]
    if count == 0:
        return True
    else:
        raise Exception(f"ERROR: Table {table} was not truncated.")


def get_records_count(conn, schema, table):
    result = conn.query(f"SELECT COUNT(1) records FROM {schema}.{table};")
    count = result["records"].values[0]
    return count


def load_from_backup_table(conn, schema, table):
    sql_insert = f"INSERT INTO {schema}.{table} SELECT * FROM {schema}.{table}_backup;"
    result = conn.query(sql_insert)
    count = get_records_count(conn, schema, table)
    raise Exception(
        f"ERROR: No rows loaded into {table}. {count} records reverted from backup table."
    )


def check_table_load(conn, schema, table):
    """Ensure data loaded successfully into destination table. If not, reload from backup table."""
    count = get_records_count(conn, schema, table)
    if count == 0:
        load_from_backup_table(conn, schema, table)
    else:
        backup_count = get_records_count(conn, schema, f"{table}_backup")
        logging.info(
            f"{backup_count} rows successfully loaded into backup table {table}_backup."
        )
        logging.info(f"{count} rows successfully loaded into table {table}.")


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


def delete_data_files(directory):
    files = [file for file in os.listdir(directory)]
    for file in files:
        if "Data" in file:
            os.remove(os.path.join(directory, file))


def check_todays_file_exists(filename):
    date = datetime.now().strftime("%m%d%y")
    expected_filename = f"{LOCALDIR}/{filename}*{date}*.csv"
    if len(glob.glob(expected_filename)) == 0:
        raise Exception(f"Error: '{filename}' was not downloaded.")
    else:
        logging.info(f"'{filename}' successfully downloaded")


# Try Every 30 Seconds for 30 minutes
@retry(wait=wait_fixed(30), stop=stop_after_attempt(60))
def download_from_ftp():
    # TODO: all files are getting downloaded to local since we aren't deleting remote files
    conn = ftp.Connection()
    conn.download_dir(SOURCEDIR, LOCALDIR)
    check_todays_file_exists("Automated Application Data Raw")
    check_todays_file_exists("Automated Application Data Index")


def rename_file(new_name=None, string_match=""):
    new_path = ""
    files = sorted(
        os.listdir(LOCALDIR), key=lambda x: os.path.getctime(LOCALDIR + "/" + x)
    )
    for file in files:
        if string_match in file:
            old_path = f"{LOCALDIR}/{file}"
            new_path = f"{LOCALDIR}/{new_name}"
            os.rename(old_path, new_path)
    if os.path.exists(new_path):
        logging.info(f"'{new_path}' successfully renamed")
    else:
        raise Exception(f"Error: '{LOCALDIR}/{new_name}' was not successfully renamed")
    return new_path


def process_application_data(conn, schema):
    """ Take application data from csv and insert into table """
    csv = rename_file(
        new_name="AutomatedApplicationData2020.csv", string_match="Data Raw"
    )
    df = read_csv_to_df(csv)
    if backup_and_truncate_table(conn, os.getenv("SPROC_RAW_PREP")):
        table = os.getenv("DB_RAW_TABLE")
        conn.insert_into(table, df)
        check_table_load(conn, schema, table)


def process_application_data_index(conn, schema):
    """ Take application data index from csv and insert into table """
    csv = rename_file(
        new_name="AutomatedApplicationDataIndex2020.csv", string_match="Data Index"
    )
    df = read_csv_to_df(csv)
    if backup_and_truncate_table(conn, os.getenv("SPROC_RAW_INDEX_PREP")):
        table = os.getenv("DB_RAW_INDEX_TABLE")
        conn.insert_into(table, df)
        check_table_load(conn, schema, table)


def main():
    try:
        schema = os.getenv("DB_SCHEMA")
        conn = MSSQL()
        mailer = Mailer()

        # get files
        API().request_reports()
        # if eval(os.getenv("DELETE_LOCAL_FILES", "True")):
        #     delete_data_files(LOCALDIR)
        # download_from_ftp()

        # process_application_data(conn, schema)
        # process_application_data_index(conn, schema)

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

