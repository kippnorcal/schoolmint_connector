import argparse
import logging
import os
import sys
import traceback

from job_notifications import create_notifications
import pandas as pd
from tenacity import *
from gbq_connector import CloudStorageClient
from gbq_connector import DbtClient

from schoolmint_api import SchoolmintAPI
from ftp import FTP

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
parser.add_argument("--school-year", dest="school_year", help="School year in YYYY format; ex. '2025'")
args = parser.parse_args()

notifications = create_notifications("BigQuery Dev: Schoomint Connector", "mailgun")


def read_csv_to_df(file_name: str) -> pd.DataFrame:
    if not os.path.isfile(file_name):
        raise Exception(
            f"ERROR: '{file_name}' file does not exist. Most likely problem downloading from sFTP."
        )
    df = pd.read_csv(file_name, sep=",", quotechar='"', doublequote=True, dtype=str, header=0)
    count = len(df.index)
    logging.info(f"Read {count} rows from CSV file '{file_name}'.")
    if int(os.getenv("REJECT_EMPTY_FILES")):
        if count == 0:
            raise Exception(f"ERROR: No data was loaded from CSV file '{file_name}'.")
    return df


def delete_data_files(directory: str) -> None:
    """
    Delete data files (not everything) from the given directory.

    :param directory: Directory that we want to delete data files from
    :type directory: String
    """
    for file in os.listdir(directory):
        if "Data" in file:
            os.remove(os.path.join(directory, file))


def get_latest_file(filename: str):
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
def download_from_ftp(ftp: FTP) -> list:
    """
    Download data files from FTP. It can take some time for SchoolMint
    to upload the reports after the API request, so we use Tenacity retry
    to wait up to 30 min.
    """
    logging.info("Attempting to download files")
    ftp.download_dir(SOURCEDIR, LOCALDIR)
    regional_file = get_latest_file("Regional Automated Application Data Raw")
    return [regional_file]


def prep_files_for_upload(files: list) -> pd. DataFrame:
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
    SchoolmintAPI(api_suffixes).request_reports()
    if int(os.getenv("DELETE_LOCAL_FILES")):
        delete_data_files(LOCALDIR)

    logging.info("Downloading Files")
    files = download_from_ftp(ftp)
    joined_files = prep_files_for_upload(files)
    joined_files["school_year_4_digit"] = school_year

    cloud_client = CloudStorageClient()

    blob_name = f"schoolmint/schoolmint_raw_data_{school_year}.csv"
    bucket = os.getenv("BUCKET")
    cloud_client.load_dataframe_to_cloud_as_csv(bucket, blob_name, joined_files)

    logging.info("Running dbt snapshot")
    dbt_conn = DbtClient()
    dbt_conn.run_job()


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
                from_address=os.getenv("FROM_ADDRESS"),
                to_address=failure_email_address,
                subject="BigQuery Schoolmint Connector - Failed",
                body="See #data_notifications for details."
            )
        notifications.notify(error_message=stack_trace)
