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
    parser.add_argument(
        "-g, --generate-schema-json",
        help="Generates a JSON schema for a BigQuery external table; must mount a volume to 'file' directory using -v flag",
        dest="generate_schema",
        action="store_true"
    )
    parser.add_argument(
        "--rename-hist-column",
        dest="rename_hist_column",
        nargs=2,
        action="append",
        metavar=("OLD", "NEW"),
        help="Rename a column in historical table: --rename-column old_name new_name",
    )

    return parser.parse_args()
