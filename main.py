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

parser = argparse.ArgumentParser()
parser.add_argument(
    "--school-year",
    dest="school_year",
    required=True,
    help="School year in YYYY format; ex. '2025'")
parser.add_argument(
    "--dbt-refresh",
    help="Runs dbt refresh job",
    dest="dbt_refresh",
    action="store_true"
)
parser.add_argument(
    "--semt-refresh",
    help="Runs an adhoc dbt job to refresh the source of the SEMT trackers",
    dest="semt_refresh",
    action="store_true"
)
args = parser.parse_args()

notifications = create_notifications("Schoomint Connector", "mailgun")
notifications.extend_job_name(f" - {args.school_year}")


# Some of the colum names of the schoolmint report are incredibly long, so this map renames these columns
COLUMN_RENAME_MAP = {
    'In which country was the student born?': 'country_of_birth',
    'When did the student first attend school in the United S...': 'first_attend_school_us',
    'What grade level did the student first attend school in ...': 'first_grade_level_attend_school_us',
    'Has the student ever attended a California public (distr...': 'has_student_ever_attended_california_public_school',
    'Has the student ever attended school outside of the Unit...': 'has_student_ever_attended_school_outside_united_states',
    'Has the student ever experienced interruption in their s...': 'has_student_ever_experienced_interruption_in_schooling',
    'Is the student in Special Education?': 'is_student_in_special_education',
    'Does the student receive speech therapy?': 'is_student_receiving_speech_therapy',
    'Does the student have an Individualized Education Progra...': 'does_student_have_iep',
    'Does the student have a 504 plan?': 'does_student_have_504_plan',
    'Where do you and the student currently live?': 'where_does_guardian_and_student_live',
    'Is the student in Foster Care?': 'is_student_in_foster_care',
    'If yes, please provide the 19 Digit Foster Case ID.': 'foster_care_case_id',
    'Does the student have Medi-Cal Health Insurance?': 'does_student_have_medical_health_insurance',
    'If the student is eligible for public benefits (Medi-Cal...': 'do_you_auth_kipp_to_release_student_info_for_billing',
    'Select all food allergies that apply:': 'student_food_allergies',
    'Select all medication allergies that apply:': 'student_medication_allergies',
    'Select any other allergies that apply:': 'student_other_allergies',
    'If needed, you can provide more details about the studen...': 'student_allergy_details',
    'If needed, you can provide more details about the studen....1': 'student_medical_condition_details',
    'If needed, you can provide more details about the studen....2': 'student_mental_health_history',
    'Does the student have any medical conditions or concerns...': 'does_student_have_medical_conditions_concerns',
    'Does the student have any mental health or behavioral ne...': 'does_student_have_mental_health_behavioral_needs',
    'Does the student require any daily medication?': 'does_student_require_daily_medication',
    'Does the student require any emergency medications?': 'does_student_require_emergency_medication',
    'Select all medical conditions or concerns that apply:': 'medical_conditions_or_concerns',
    'Select all mental health or behavioral needs that apply:': 'mental_health_or_behavioral_needs',
    'Is there an order regarding educational custody or other...': 'is_there_an_order_regarding_custody_or_other_issues',
    'If yes, please explain. You will be asked to submit  a c...': 'custody_order_or_other_issues_explanation',
}



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
    regional_file = get_latest_file("Regional Automated Application Data SFTP")
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
    joined_files = joined_files.rename(columns=COLUMN_RENAME_MAP)

    cloud_client = CloudStorageClient()

    blob_name = f"schoolmint/schoolmint_raw_application_data/schoolmint_raw_data_{school_year}.csv"
    bucket = os.getenv("BUCKET")
    cloud_client.load_dataframe_to_cloud_as_csv(bucket, blob_name, joined_files)

    if args.dbt_refresh:
        logging.info("Running dbt snapshot")
        dbt_conn = DbtClient()
        dbt_conn.run_job()


    if args.semt_refresh:
        job_id = os.getenv("SEMT_JOB_ID")
        logging.info("Refreshing the SEMT datasource")
        dbt_conn = DbtClient()
        dbt_conn.run_job(job_id=job_id)


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
