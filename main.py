import argparse
import logging
import os
import sys
import traceback

from job_notifications import create_notifications
import pandas as pd
import pygsheets
from tenacity import *

from api import API
from ftp import FTP
from data_warehouse_connection import DataWarehouseConnector


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
parser.add_argument(
    "--targets", help="Sync enrollment targets from Google Sheet", action="store_true"
)
args = parser.parse_args()

notifications = create_notifications("Schoolmint", "mailgun", logs="app.log")

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
    logging.info(f"Read {count} rows from CSV file '{csv}'.")
    if int(os.getenv("REJECT_EMPTY_FILES")):
        if count == 0:
            raise Exception(f"ERROR: No data was loaded from CSV file '{csv}'.")
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
    logging.info("Attempting to download files")
    ftp.download_dir(SOURCEDIR, LOCALDIR)
    regional_file = get_latest_file("Regional Automated Application Data Raw")
    return [regional_file]


def process_application_data(dw_conn, files, school_year):
    """
    Take application data from csv and insert into table.

    :param conn: Database connection
    :type conn: Object
    :param file: Name of the Application Data file
    :type file: String
    :param school_year: 4 digit school year
    :type school_year: String
    """
    df_container = []
    for file in files:
        df_file = read_csv_to_df(f"{LOCALDIR}/{file}")
        df_container.append(df_file)
    df = pd.concat(df_container, ignore_index=True)
    # df.to_csv("files/data.csv")
    result = dw_conn.exec_sproc(f"{os.getenv('SPROC_RAW_PREP')}")
    # count = result.fetchone()[0]
    count = 0
    table = os.getenv("DB_RAW_TABLE")
    if count == 0:
        # TODO review for future years to see if this needs to stay
        dw_conn.insert_into(table, df)
        result = dw_conn.exec_sproc(f"{os.getenv('SPROC_RAW_POST')}")
        # result_set = result.fetchone()
        # logging.info(f"Loaded {result_set[1]} rows into backup table '{table}_backup'.")
        # logging.info(f"Loaded {result_set[0]} rows into table '{table}''.")
    else:
        raise Exception(f"ERROR: Table {table} was not truncated.")


def process_change_tracking(dw_conn):
    """
    Execute sproc to generate change history.

    :param dw_conn: Database connection
    :type dw_conn: Object
    """
    logging.info(f"Running {os.getenv('SPROC_CHANGE_TRACK')}")
    result = dw_conn.exec_sproc(os.getenv("SPROC_CHANGE_TRACK"))
    # count = result.fetchone()[0]
    # logging.info(f"Loaded {count} rows into Change History table.")
    logging.info(f"Loaded rows rows into Change History table.")


def process_fact_daily_status(dw_conn):
    """
    Execute sproc to generate fact daily status table.

    :param dw_conn: Database connection
    :type dw_conn: Object
    """
    logging.info(f"Running {os.getenv('SPROC_FACT_DAILY')}")
    result = dw_conn.exec_sproc(os.getenv("SPROC_FACT_DAILY"))
    # count = result.fetchone()[0]
    # logging.info(f"Loaded {count} rows into Fact Daily Status table.")
    logging.info(f"Loaded rows into Fact Daily Status table.")


def sync_enrollment_targets(dw_conn, school_year):
    """
    Pull enrollment target numbers from spreadsheet and write to ProgressMonitoring table.
    """
    logging.info(f"Running sync_enrollment_targets func")
    client = pygsheets.authorize(service_file="service.json")
    sheet = client.open_by_key(os.getenv("TARGETS_SHEET_ID"))
    worksheet = sheet.worksheet_by_title(os.getenv("TARGETS_SHEET_TITLE"))
    df = worksheet.get_as_df()
    pd.to_datetime(df["Goal_date"])
    dw_conn.exec_cmd(  # drop into sqlalchemy because we are locked into an older version of sqlsorcery
        f"""
        DELETE FROM custom.SchoolMint_ProgressMonitoring
        WHERE Schoolyear4digit={school_year}
        """
    )
    dw_conn.insert_into("SchoolMint_ProgressMonitoring", df)
    logging.info(f"Loaded {len(df)} rows into Progress Monitoring table.")


def main():
    try:
        school_year = os.getenv("CURRENT_SCHOOL_YEAR")
        dw_conn = DataWarehouseConnector()
        ftp = FTP()

        ftp.archive_remote_files(SOURCEDIR)
        ftp.delete_old_archive_files(SOURCEDIR)

        api_suffixes = [os.getenv("API_SUFFIXES")]
        logging.info("Getting API data")
        API(api_suffixes).request_reports()
        if int(os.getenv("DELETE_LOCAL_FILES")):
            delete_data_files(LOCALDIR)

        logging.info("Downloading Files")
        files = download_from_ftp(ftp)

        process_application_data(dw_conn, files, school_year)

        process_change_tracking(dw_conn)

        if args.targets:
            sync_enrollment_targets(dw_conn, school_year)
            logging.info(f"Running sproc_SchoolMint_LoadTargetsWide")
            dw_conn.exec_sproc("sproc_SchoolMint_LoadTargetsWide")
            logging.info(f"Running sproc_Schoolmint_create_intercepts")
            dw_conn.exec_sproc("sproc_Schoolmint_create_intercepts")
            logging.info(f"Running sproc_Schoolmint_load_Fact_PM")
            dw_conn.exec_sproc("sproc_Schoolmint_load_Fact_PM")

        process_fact_daily_status(dw_conn)

        notifications.notify()

    except Exception as e:
        logging.exception(e)
        stack_trace = traceback.format_exc()
        notifications.simple_email(
            to_address=os.getenv("FAILURE_EMAIL"),
            from_address=os.getenv("FROM_ADDRESS"),
            subject="Schoolmint Connector Failed",
            body="See data notifications channel for more details",
        )
        notifications.notify(error_message=stack_trace)


if __name__ == "__main__":
    main()
