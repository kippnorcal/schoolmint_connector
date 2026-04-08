from io import BytesIO
import os
import logging

import pandas as pd
from google.cloud.storage import Blob
from gbq_connector import CloudStorageClient

from utils.data_config import CURRENT_YEAR_FOLDER, HISTORICAL_FOLDER, BASE_FILE_NAME


def process_blob(blob: Blob, bucket: str, cloud_storage: CloudStorageClient, rename_map: dict):
    logging.info(f"Processing: gs://{blob.bucket.name}/{blob.name}")

    csv_bytes = blob.download_as_bytes()
    df = pd.read_csv(BytesIO(csv_bytes))
    df = df.fillna("").astype(str)

    df = df.rename(columns=rename_map)

    cloud_storage.load_dataframe_to_cloud_as_csv(bucket, blob.name, df)


def run_workflow(cloud_storage: CloudStorageClient, rename_map: dict):
    bucket = os.getenv("BUCKET")

    count = 0
    for blob in cloud_storage.list_blobs(bucket, HISTORICAL_FOLDER, file_extension = ".csv"):
        process_blob(blob, bucket, cloud_storage, rename_map)
        count += 1
    logging.info(f"Added new columns to {count} historical CSV file(s)")
