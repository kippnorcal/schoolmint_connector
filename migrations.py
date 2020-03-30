import os
import traceback

import pandas as pd
from sqlsorcery import MSSQL, PostgreSQL
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.sql import text as sa_text
from sqlalchemy.types import Boolean


def migrate_mssql():
    try:
        sql = MSSQL()

        # Tables
        sql.exec_cmd_from_file(
            "sql/mssql/tables/schoolmint_ApplicationData_changehistory.sql"
        )
        sql.exec_cmd_from_file(
            "sql/mssql/tables/schoolmint_ApplicationData_raw_backup.sql"
        )
        sql.exec_cmd_from_file("sql/mssql/tables/schoolmint_ApplicationData_raw.sql")
        sql.exec_cmd_from_file(
            "sql/mssql/tables/schoolmint_ApplicationDataIndex_raw_backup.sql"
        )
        sql.exec_cmd_from_file(
            "sql/mssql/tables/schoolmint_ApplicationDataIndex_raw.sql"
        )
        sql.exec_cmd_from_file("sql/mssql/tables/schoolmint_ApplicationStatuses.sql")
        sql.exec_cmd_from_file("sql/mssql/tables/schoolmint_FactDailyStatus.sql")
        sql.exec_cmd_from_file("sql/mssql/tables/schoolmint_lk_Enrollment.sql")
        sql.exec_cmd_from_file("sql/mssql/tables/schoolmint_ProgressMonitoring.sql")
        sql.exec_cmd_from_file("sql/mssql/tables/schoolmint_SchoolCodes.sql")

        # Load lookup tables
        enrollments = pd.read_csv("sql/data/lk_enrollment.csv")
        sql.insert_into("schoolmint_lk_Enrollment", enrollments)

        application_statuses = pd.read_csv("sql/data/application_statuses.csv")
        sql.insert_into("schoolmint_ApplicationStatuses", application_statuses)

        # Views
        sql.exec_cmd_from_file("sql/mssql/views/vw_schoolmint_AppStatusList.sql")
        sql.exec_cmd_from_file(
            "sql/mssql/views/vw_schoolmint_FactDailyStatus_InterimTargets.sql"
        )
        sql.exec_cmd_from_file("sql/mssql/views/vw_schoolmint_FactDailyStatus.sql")
        sql.exec_cmd_from_file("sql/mssql/views/vw_schoolmint_ProgressMonitoring.sql")
        sql.exec_cmd_from_file(
            "sql/mssql/views/vw_schoolmint_FactProgressMonitoring.sql"
        )
        sql.exec_cmd_from_file("sql/mssql/views/vw_schoolmint_Index_Demographics.sql")

        # Stored Procedures
        sql.exec_cmd_from_file(
            "sql/mssql/sprocs/sproc_schoolmint_Create_ChangeTracking_Entries.sql"
        )
        sql.exec_cmd_from_file(
            "sql/mssql/sprocs/sproc_schoolmint_Create_FactDailyStatus.sql"
        )
        sql.exec_cmd_from_file(
            "sql/mssql/sprocs/sproc_schoolmint_Index_PostProcess.sql"
        )
        sql.exec_cmd_from_file(
            "sql/mssql/sprocs/sproc_schoolmint_Index_PrepareTables.sql"
        )
        sql.exec_cmd_from_file("sql/mssql/sprocs/sproc_schoolmint_Raw_PostProcess.sql")
        sql.exec_cmd_from_file(
            "sql/mssql/sprocs/sproc_schoolmint_Raw_PrepareTables.sql"
        )

    except ProgrammingError as e:
        if "Cannot open database" in str(e):
            print("ERROR: First create your database and schema manually")


def migrate_postgres():
    try:
        sql = PostgreSQL()

        # Tables
        sql.exec_cmd_from_file(
            "sql/postgresql/tables/schoolmint_ApplicationData_changehistory.sql"
        )
        sql.exec_cmd_from_file(
            "sql/postgresql/tables/schoolmint_ApplicationData_raw_backup.sql"
        )
        sql.exec_cmd_from_file(
            "sql/postgresql/tables/schoolmint_ApplicationData_raw.sql"
        )
        sql.exec_cmd_from_file(
            "sql/postgresql/tables/schoolmint_ApplicationDataIndex_raw_backup.sql"
        )
        sql.exec_cmd_from_file(
            "sql/postgresql/tables/schoolmint_ApplicationDataIndex_raw.sql"
        )
        sql.exec_cmd_from_file(
            "sql/postgresql/tables/schoolmint_ApplicationStatuses.sql"
        )
        sql.exec_cmd_from_file("sql/postgresql/tables/schoolmint_FactDailyStatus.sql")
        sql.exec_cmd_from_file("sql/postgresql/tables/schoolmint_lk_Enrollment.sql")
        sql.exec_cmd_from_file(
            "sql/postgresql/tables/schoolmint_ProgressMonitoring.sql"
        )
        sql.exec_cmd_from_file("sql/postgresql/tables/schoolmint_SchoolCodes.sql")

        # Load lookup tables
        enrollments = pd.read_csv("sql/data/lk_enrollment.csv")
        sql.insert_into("schoolmint_lk_Enrollment", enrollments)

        application_statuses = pd.read_csv("sql/data/application_statuses.csv")
        sql.insert_into(
            "schoolmint_ApplicationStatuses",
            application_statuses,
            dtype={"Application": Boolean, "Registration": Boolean},
        )

        # Views
        sql.exec_cmd_from_file("sql/postgresql/views/vw_schoolmint_AppStatusList.sql")
        sql.exec_cmd_from_file("sql/postgresql/views/vw_schoolmint_FactDailyStatus.sql")
        sql.exec_cmd_from_file(
            "sql/postgresql/views/vw_schoolmint_FactDailyStatus_InterimTargets.sql"
        )
        sql.exec_cmd_from_file(
            "sql/postgresql/views/vw_schoolmint_Index_Demographics.sql"
        )
        sql_str = sql._read_sql_file(
            "sql/postgresql/views/vw_schoolmint_ProgressMonitoring.sql"
        )
        command = sa_text(sql_str).execution_options(autocommit=True)
        sql.engine.execute(command)
        sql.exec_cmd_from_file(
            "sql/postgresql/views/vw_schoolmint_FactProgressMonitoring.sql"
        )

        # Stored Procedures
        sql.exec_cmd_from_file(
            "sql/postgresql/sprocs/sproc_schoolmint_Create_ChangeTracking_Entries.sql"
        )
        sql.exec_cmd_from_file(
            "sql/postgresql/sprocs/sproc_schoolmint_Create_FactDailyStatus.sql"
        )
        sql.exec_cmd_from_file(
            "sql/postgresql/sprocs/sproc_schoolmint_Index_PostProcess.sql"
        )
        sql.exec_cmd_from_file(
            "sql/postgresql/sprocs/sproc_schoolmint_Index_PrepareTables.sql"
        )
        sql.exec_cmd_from_file(
            "sql/postgresql/sprocs/sproc_schoolmint_Raw_PostProcess.sql"
        )
        sql.exec_cmd_from_file(
            "sql/postgresql/sprocs/sproc_schoolmint_Raw_PrepareTables.sql"
        )

    except ProgrammingError as e:
        if "Cannot open database" in str(e):
            print("ERROR: First create your database and schema manually")

    except Exception as e:
        print(e)
        print(traceback.format_exc())
