from io import StringIO

from typing import Union

from google import auth
from google.cloud import storage
from pandas import DataFrame


class GoogleCloudConnection:

    def __init__(self):
        self._storage_client = self._build_client()

    @staticmethod
    def _build_client():
        credentials, project = auth.default(
            scopes=[
                "https://www.googleapis.com/auth/cloud-platform"
            ]
        )

        return storage.Client(credentials=credentials, project=project)

    def load_file_to_cloud(self, bucket: str, blob: str, local_file_path: str):
        bucket = self._storage_client.bucket(bucket)
        blob: storage.Blob = bucket.blob(blob)
        blob.upload_from_file(local_file_path)

    def load_dataframe_to_cloud(self, bucket: str, blob: str, df: DataFrame):
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)

        bucket = self._storage_client.bucket(bucket)
        blob: storage.Blob = bucket.blob(blob)
        blob.upload_from_string(csv_buffer.getvalue(), content_type="text/csv")
