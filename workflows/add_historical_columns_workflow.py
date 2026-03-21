import argparse
from io import BytesIO
import os
import logging
import sys

import pandas as pd
from google.cloud.storage import Blob
from gbq_connector import CloudStorageClient

from utils import helpers

HISTORICAL_FOLDER = "schoolmint/schoolmint_raw_application_data_historical"


def add_new_columns(df: pd.DataFrame, columns: list) -> pd.DataFrame:

    columns_to_add = helpers.column_diff(df, columns, add_cols=True)

    if columns_to_add:
        for column in columns_to_add:
            df[column] = ""
            logging.info(f"--Added new column '{column}' to the dataframe.")
    else:
        logging.info("No columns to add.")

    return df


def columns_to_remove(df: pd.DataFrame, columns: list) -> pd.DataFrame:

    cols_to_remove = helpers.column_diff(df, columns, remove_cols=True)

    if cols_to_remove:
        for column in cols_to_remove:
            logging.info(f"--Removed column '{column}' from the dataframe")
        df = df.drop(columns=cols_to_remove)
    else:
        logging.info("No columns to remove.")

    return df


def process_blob(blob: Blob, bucket: str, cloud_storage: CloudStorageClient, columns: list):
    print(f"Processing: gs://{blob.bucket.name}/{blob.name}")

    csv_bytes = blob.download_as_bytes()
    df = pd.read_csv(BytesIO(csv_bytes))
    df = df.astype(str)

    df = add_new_columns(df, columns)
    df = columns_to_remove(df, columns)

    cloud_storage.load_dataframe_to_cloud_as_csv(bucket, blob.name, df)


def run_workflow(school_year: str, cloud_storage: CloudStorageClient):
    bucket = os.getenv("BUCKET")
    current_report_blob_name = f"schoolmint/schoolmint_raw_application_data/schoolmint_raw_data_{school_year}.csv"
    current_report_df = cloud_storage.get_csv_blob_as_dataframe(bucket, current_report_blob_name)
    # get columns from df
    columns = current_report_df.columns.tolist()



    count = 0
    for blob in cloud_storage.list_blobs(bucket, HISTORICAL_FOLDER, file_extension = ".csv"):
        process_blob(blob, bucket, cloud_storage, columns)
        count += 1
    logging.info(f"Added new columns to {count} historical CSV file(s)")
