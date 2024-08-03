import argparse
import datetime as dt
import glob
import logging
import os
import sys
import time
import traceback

from job_notifications import create_notifications
import pandas as pd
import pygsheets
from tenacity import *

from api import API
from ftp import FTP
from google_cloud_connections import GoogleCloudConnection

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
parser.add_argument("--school-year", dest="school_year", help="School year in YYYY format; ex. '2025'", nargs=1)
args = parser.parse_args()

notifications = create_notifications("Schoomint Connector", "mailgun")


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
    df_container = []
    for file in files:
        df_file = read_csv_to_df(f"{LOCALDIR}/{file}")
        df_container.append(df_file)
    df = pd.concat(df_container)
    result = conn.exec_sproc(f"{os.getenv('SPROC_RAW_PREP')} {school_year}")
    count = result.fetchone()[0]
    logging.info(f"Ran sproc and processed {count} records from {len(files)} files")
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


def sync_enrollment_targets(conn, school_year):
    """
    Pull enrollment target numbers from spreadsheet and write to ProgressMonitoring table.
    """
    client = pygsheets.authorize(service_file="service.json")
    sheet = client.open_by_key(os.getenv("TARGETS_SHEET_ID"))
    worksheet = sheet.worksheet_by_title(os.getenv("TARGETS_SHEET_TITLE"))
    df = worksheet.get_as_df()
    conn.engine.execute(  # drop into sqlalchemy because we are locked into an older version of sqlsorcery
        f"""
        DELETE FROM custom.SchoolMint_ProgressMonitoring
        WHERE Schoolyear4digit={school_year}
        """
    )
    conn.insert_into("SchoolMint_ProgressMonitoring", df)
    logging.info(f"Loaded {len(df)} rows into Progress Monitoring table.")


def prep_files_for_upload(files) -> pd. DataFrame:
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
    df = pd.concat(df_container)
    return df


def main():
    school_year = args.school_year
    ftp = FTP()

    ftp.archive_remote_files(SOURCEDIR)
    ftp.delete_old_archive_files(SOURCEDIR)

    api_suffixes = os.getenv("API_SUFFIXES").split(",")
    logging.info("Getting API data")
    API(api_suffixes).request_reports()
    if int(os.getenv("DELETE_LOCAL_FILES")):
        delete_data_files(LOCALDIR)

    logging.info("Downloading Files")
    files = download_from_ftp(ftp)
    joined_files = prep_files_for_upload(files)

    blob_name = f"schoolmint/schoolmint_raw_data_{school_year}.csv"
    gcc = GoogleCloudConnection()
    bucket = os.getenv("BUCKET")
    gcc.load_dataframe_to_cloud(bucket, blob_name, joined_files)


if __name__ == "__main__":
    try:
        main()
        notifications.notify()
    except Exception as e:
        logging.exception(e)
        stack_trace = traceback.format_exc()
        failure_email_address = os.getenv("FAILURE_EMAIL")
        if failure_email_address is not None:
            notifications.simple_email(
                to_address=failure_email_address,
                subject="Schoolmint Connector - Failed",
                body="See #data_notifications for details."
            )
        notifications.notify(error_message=stack_trace)
