import pandas as pd

def column_diff(df: pd.DataFrame, incoming_columns: list, add_cols: bool = False, remove_cols: bool = False) -> list:

    columns_result = []

    if add_cols == remove_cols:
        raise ValueError("One of either 'add_cols' or 'remove_cols' should be True")

    if add_cols:
        for column in incoming_columns:
            if column not in df.columns:
                columns_result.append(column)

    if remove_cols:
        for column in df.columns:
            if column not in incoming_columns:
                columns_result.append(column)

    return columns_result
