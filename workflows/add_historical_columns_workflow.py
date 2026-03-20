import argparse
from io import BytesIO
import os
import logging
import sys

import pandas as pd
from google.cloud.storage import Blob
from gbq_connector import CloudStorageClient

HISTORICAL_FOLDER = "schoolmint/schoolmint_raw_application_data_historical"


def add_new_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Modify this function to add your new columns.

    Examples:
      df["new_col"] = "some value"
      df["full_name"] = df["first_name"] + " " + df["last_name"]
      df["row_number"] = range(1, len(df) + 1)
    """
    # Example columns:
    df["new_col_1"] = "default value"
    df["new_col_2"] = len(df)
    return df


def process_blob(blob: Blob, input_prefix: str, output_prefix: str):
    print(f"Processing: gs://{blob.bucket.name}/{blob.name}")

    csv_bytes = blob.download_as_bytes()
    df = pd.read_csv(BytesIO(csv_bytes))

    df = add_new_columns(df)

    # Preserve the filename/path after the input prefix
    relative_path = blob.name[len(input_prefix):].lstrip("/")
    output_name = f"{output_prefix.rstrip('/')}/{relative_path}"

    out_blob = output_bucket.blob(output_name)
    out_blob.upload_from_file(out_buffer, content_type="text/csv")

    print(f"Written to: gs://{output_bucket.name}/{output_name}")


def run_workflow(gcs_client: CloudStorageClient):


    bucket = os.getenv("BUCKET")
    count = 0
    for blob in gcs_client.list_blobs(bucket, HISTORICAL_FOLDER, file_extension = ".csv"):
        process_blob(bucket)
        count += 1
    logging.info(f"Added new columns to {count} historical CSV file(s)")
