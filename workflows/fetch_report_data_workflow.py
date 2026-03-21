import logging
import os

import pandas as pd
from tenacity import *
from gbq_connector import CloudStorageClient

from schoolmint_api import SchoolmintAPI
from ftp import FTP
from utils.data_config import BASE_FILE_NAME
from utils.data_config import COLUMN_RENAME_MAP
from utils.data_config import CURRENT_YEAR_FOLDER
from utils.data_config import LOCALDIR
from utils.data_config import SFTP_SOURCEDIR
from utils.data_config import SM_REPORT_NAME
from utils import helpers


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
    ftp.download_dir(SFTP_SOURCEDIR, LOCALDIR)
    regional_file = get_latest_file(SM_REPORT_NAME)
    return [regional_file]


def prep_files_for_upload(files: list) -> pd. DataFrame:
    df_container = []
    for file in files:
        df_file = read_csv_to_df(f"{LOCALDIR}/{file}")
        df_container.append(df_file)
    df = pd.concat(df_container)
    return df


def check_for_new_columns(df: pd.DataFrame) -> bool:
    expected_columns = list(COLUMN_RENAME_MAP.values())

    new_columns = helpers.column_diff(df, expected_columns, add_cols=True)

    if new_columns:
        logging.info(f"Found the following new columns:")
        for column in new_columns:
            logging.info(column)
        logging.info("Please add these new columns to the data config.")
        return True
    else:
        return False


def check_for_deleted_columns(df: pd.DataFrame) -> bool:
    expected_columns = list(COLUMN_RENAME_MAP.keys())


    removed_columns = helpers.column_diff(df, expected_columns, remove_cols=True)

    if removed_columns:
        logging.info(f"The following columns appear missing:")
        for column in removed_columns:
            logging.info(column)
        logging.info("Please check the mapping in the data_config module to verify.")
        return True
    else:
        return False


def fetch_report(school_year: str, cloud_client: CloudStorageClient):

    ftp = FTP()

    ftp.archive_remote_files(SFTP_SOURCEDIR)
    ftp.delete_old_archive_files(SFTP_SOURCEDIR)

    api_suffixes = os.getenv("API_SUFFIXES").split(",")
    logging.info("Getting API data")
    SchoolmintAPI(api_suffixes).request_reports()
    if int(os.getenv("DELETE_LOCAL_FILES")):
        delete_data_files(LOCALDIR)

    logging.info("Downloading Files")
    files = download_from_ftp(ftp)
    joined_files = prep_files_for_upload(files)
    joined_files["school_year_4_digit"] = school_year
    check_for_deleted_columns(joined_files)
    joined_files = joined_files.rename(columns=COLUMN_RENAME_MAP)
    if check_for_new_columns(joined_files):
        logging.info("Filtering out new columns that are not in the config.")
        joined_files = joined_files[list(COLUMN_RENAME_MAP.values())]

    blob_name = f"{CURRENT_YEAR_FOLDER}/{BASE_FILE_NAME}_{school_year}.csv"
    bucket = os.getenv("BUCKET")
    cloud_client.load_dataframe_to_cloud_as_csv(bucket, blob_name, joined_files)