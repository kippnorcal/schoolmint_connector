import os
import json

from gbq_connector import CloudStorageClient

from utils.data_config import BASE_FILE_NAME
from utils.data_config import CURRENT_YEAR_FOLDER
from utils.data_config import LOCALDIR


def column_template(col) -> dict:
    return   {
        "name": col,
        "mode": "NULLABLE",
        "type": "STRING",
        "description": "",
        "fields": []
    }

def generate_schema(school_year: str, cloud_storage: CloudStorageClient) -> None:
    bucket = os.getenv("BUCKET")
    current_report_blob_name = f"{CURRENT_YEAR_FOLDER}/{BASE_FILE_NAME}_{school_year}.csv"
    current_report_df = cloud_storage.get_csv_blob_as_dataframe(bucket, current_report_blob_name)

    # get columns from df
    columns = current_report_df.columns.tolist()

    json_schema = []
    for col in columns:
        json_schema.append(column_template(col))

    file = json.dumps(json_schema, indent=2)
    with open(f"{LOCALDIR}/schema.json", "w") as f:
        f.write(file)

