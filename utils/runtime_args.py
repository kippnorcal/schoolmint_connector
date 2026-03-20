import argparse

def get_runtime_args():
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
    parser.add_argument(
        "-a, --add-cols-hist",
        help="Adds new report columns to the historical files",
        dest="add_historical_columns",
        action="store_true"
    )

    return parser.parse_args()
