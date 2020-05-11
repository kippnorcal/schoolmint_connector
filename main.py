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
from migrations import migrate_mssql, migrate_postgres

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
logging.getLogger("paramiko").setLevel(logging.ERROR)

parser = argparse.ArgumentParser(description="Additional migration options")
parser.add_argument("--mssql", help="Run migrations for MS SQL", action="store_true")
parser.add_argument(
    "--postgres", help="Run migrations for PostgreSQL", action="store_true"
)
args = parser.parse_args()


def read_logs(filename):
    """
    Read the given file.
    
    :param filename: Name of the file to be read (in this case, the logs)
    :type filename: String
    :return: Contents of the file
    :rtype: String
    """
    with open(filename) as f:
        return f.read()


def read_csv_to_df(csv):
    """
    Read the csv into a dataframe in preparation for database load.
    
    :param csv: Name of the csv file to be read into a DataFrame
    :type csv: String
    :return: Contents of the csv file
    :rtype: DataFrame
    """
    if not os.path.isfile(csv):
        raise Exception(
            f"ERROR: '{csv}' file does not exist. Most likely problem downloading from sFTP."
        )
    df = pd.read_csv(csv, sep=",", quotechar='"', doublequote=True, dtype=str, header=0)
    count = len(df.index)
    if count == 0:
        raise Exception(f"ERROR: No data was loaded from CSV file '{csv}'.")
    else:
        logging.info(f"Read {count} rows from CSV file '{csv}'.")
    return df


def delete_data_files(directory):
    """
    Delete data files (not everything) from the given directory.

    :param directory: Directory that we want to delete data files from
    :type directory: String
    """
    for file in os.listdir(directory):
        if "Data" in file:
            os.remove(os.path.join(directory, file))


def get_latest_file(filename):
    """
    Get the file that matches the given name.
    Reverse sort by modification date in case there are multiple.
    
    :param filename: Name of the file that we're looking for
    :type filename: String
    :return: Name of the most recently modified file with the given name
    :rtype: String
    """
    all_files = os.listdir(LOCALDIR)
    matched_files = [file for file in all_files if filename in file]
    files = sorted(
        matched_files,
        key=lambda file: os.path.getmtime(f"{LOCALDIR}/{file}"),
        reverse=True,
    )
    if files:
        file = files[0]
        logging.info(f"Downloaded '{file}'.")
        return file
    else:
        raise Exception(f"Error: '{filename}' was not downloaded.")


@retry(wait=wait_fixed(30), stop=stop_after_attempt(60))
def download_from_ftp(ftp):
    """
    Download data files from FTP. It can take some time for SchoolMint 
    to upload the reports after the API request, so we use Tenacity retry 
    to wait up to 30 min.

    :param ftp: FTP connection
    :type ftp: Object
    :return: Names of the files downloaded from the FTP
    :rtype: List
    """
    ftp.download_dir(SOURCEDIR, LOCALDIR)
    regional_file = get_latest_file("Regional Automated Application Data Raw")
    bridge_file = get_latest_file("Bridge Automated Application Data Raw")
    return [regional_file, bridge_file]


def process_application_data(conn, files, school_year):
    """
    Take application data from csv and insert into table.
    
    :param conn: Database connection
    :type conn: Object
    :param file: Name of the Application Data file
    :type file: String
    :param school_year: 4 digit school year
    :type school_year: String
    """
    df = pd.DataFrame()
    for file in files:
        df_file = read_csv_to_df(f"{LOCALDIR}/{file}")
        df = df.append(df_file)
    result = conn.exec_sproc(f"{os.getenv('SPROC_RAW_PREP')} {school_year}")
    count = result.fetchone()[0]
    table = os.getenv("DB_RAW_TABLE")
    if count == 0:
        # for 2021 enrollment period, exclude duplicate Bridge records coming from the KBA SM instance
        # all of these records (and more) are already found in the Oakland Enrolls instance
        # TODO review for future years to see if this needs to stay
        bridge_id = "164"
        df = df.loc[df["School_Applying_to"] != bridge_id]
        conn.insert_into(table, df)
        result = conn.exec_sproc(f"{os.getenv('SPROC_RAW_POST')} {school_year}")
        result_set = result.fetchone()
        logging.info(f"Loaded {result_set[1]} rows into backup table '{table}_backup'.")
        logging.info(f"Loaded {result_set[0]} rows into table '{table}''.")
    else:
        raise Exception(f"ERROR: Table {table} was not truncated.")


def process_change_tracking(conn):
    """
    Execute sproc to generate change history.
    
    :param conn: Database connection
    :type conn: Object
    """
    result = conn.exec_sproc(os.getenv("SPROC_CHANGE_TRACK"))
    count = result.fetchone()[0]
    logging.info(f"Loaded {count} rows into Change History table.")


def process_fact_daily_status(conn):
    """
    Execute sproc to generate fact daily status table.
    
    :param conn: Database connection
    :type conn: Object
    """
    result = conn.exec_sproc(os.getenv("SPROC_FACT_DAILY"))
    count = result.fetchone()[0]
    logging.info(f"Loaded {count} rows into Fact Daily Status table.")


def main():
    try:
        school_year = os.getenv("CURRENT_SCHOOL_YEAR")
        conn = MSSQL()
        ftp = FTP()

        ftp.archive_remote_files(SOURCEDIR)
        ftp.delete_old_archive_files(SOURCEDIR)

        api_suffixes = os.getenv("API_SUFFIXES").split(",")
        API(api_suffixes).request_reports()
        if eval(os.getenv("DELETE_LOCAL_FILES", "True")):
            delete_data_files(LOCALDIR)
        files = download_from_ftp(ftp)

        process_application_data(conn, files, school_year)

        process_change_tracking(conn)
        process_fact_daily_status(conn)

        success_message = read_logs("app.log")
        mailer = Mailer()
        mailer.notify(results=success_message)

    except Exception as e:
        logging.exception(e)
        stack_trace = traceback.format_exc()
        mailer = Mailer()
        mailer.notify(success=False, error_message=stack_trace)


if __name__ == "__main__":
    if args.mssql:
        migrate_mssql()
    elif args.postgres:
        migrate_postgres()
    else:
        main()
