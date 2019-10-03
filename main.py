import argparse
from datetime import datetime
import glob
import logging
import os
from os import getenv
import sys
import time
import traceback

import pandas as pd
from sqlsorcery import MSSQL
from tenacity import *

from api import API
import ftp
from mailer import Mailer

LOCALDIR = 'files'
SOURCEDIR = 'schoolmint'


logging.basicConfig(
	handlers = [logging.FileHandler(filename="app.log",mode='w+'), logging.StreamHandler(sys.stdout)],
	level=logging.INFO,
	format="%(asctime)s | %(levelname)s: %(message)s",
	datefmt="%Y-%m-%d %I:%M:%S%p %Z",
)


def read_logs(filename):
	with open(filename) as f:
		return f.read()


def read_csv_to_df(CSVFilename):
	if (not os.path.isfile(CSVFilename)):
		raise Exception(f"Error: '{CSVFilename}' File Does Not Exist. Most likely problem downloading from sFTP")
	df = pd.read_csv(CSVFilename, sep=',', quotechar='"', doublequote=True, dtype=str, header=0)
	if len(df.index)==0:
		raise Exception(f"Error - No Data Was Loaded From CSV File: '{CSVFilename}'")
	else:
		logging.info(f'{len(df.index)} Rows Successfully Imported From CSV File')
	return df


def backup_and_truncate_table(conn, prepare_sproc):
	result = conn.exec_sproc(prepare_sproc)
	InitialRowCT = result.fetchone()[0]
	if InitialRowCT == 0:
		return True
	else:
		raise Exception('Error Loading Data. Table Was Not Truncated.')		


def get_table_row_count(conn, Schema, Table):
	result = conn.query(f"select count(1) ct from {Schema}.{Table};")
	count = result['ct'].values[0]
	return count


def load_from_backup_table(conn, Schema, Table):
	sql=f"insert into {Schema}.{Table} select * from {Schema}.{Table}_backup;"
	result=conn.query(sql)
	InsertedRowCT = get_table_row_count(conn, Schema, Table)
	raise Exception(f'Error No Rows Loaded Into Table. {InsertedRowCT} Rows Reverted From Backup Table')


def check_table_load(conn, Schema, Table):
	"""Ensure data loaded successfully into destination table. If not, reload from backup table."""
	RowCT = get_table_row_count(conn, Schema, Table)
	if (RowCT == 0):
		load_from_backup_table(conn, Schema, Table)
	else:
		BackupRowCT = get_table_row_count(conn, Schema, f'{Table}_backup')
		logging.info(f'{BackupRowCT} Rows Successfully Loaded into Backup Table {Table}_backup')
		logging.info(f'{RowCT} Rows Successfully Loaded into Table {Table}')	


def process_change_tracking():
	##Generate Change History
	conn = MSSQL()
	SchoolYear4Digit=getenv("SchoolYear4Digit", '2021')
	Enrollment_Period=getenv("Enrollment_Period", '2021')
	sproc=f"sproc_SchoolMint_Create_ChangeTracking_Entries '{SchoolYear4Digit}','{Enrollment_Period}'"

	result=conn.exec_sproc(sproc)	
	ChangeTrackingInsertedRowCT=result.fetchone()[0]
	logging.info(f'{ChangeTrackingInsertedRowCT} Rows Successfully Loaded into Change Log')
	
	return ChangeTrackingInsertedRowCT
	#RowCT=conn.query(sql)


def process_FactDailyStatus():
	##Generate Change History
	conn = MSSQL()
	SchoolYear4Digit=getenv("SchoolYear4Digit", '2021')
	sproc=f"sproc_SchoolMint_Create_FactDailyStatus '{SchoolYear4Digit}'"

	result=conn.exec_sproc(sproc)	
	FactDailyStatusInsertedRowCT=result.fetchone()[0]
	logging.info(f'{FactDailyStatusInsertedRowCT} Rows Successfully Loaded into FactDailyStatus')
	
	return FactDailyStatusInsertedRowCT


def api_request():
	api = API()
	api_tokens = [getenv("API_TOKEN_DATA"),getenv("API_TOKEN_DATA_INDEX")]
	for api_token in api_tokens:
		api.post_demand_export(api_token=api_token)


def delete_data_files(directory):
	filelist = [ filename for filename in os.listdir(directory) ]
	for filename in filelist:
		if 'Data' in filename:
			os.remove(os.path.join(directory, filename))


def check_todays_file_exists(filename):
	date = datetime.now().strftime('%m%d%y')
	expected_filename = f"{LOCALDIR}/{filename}*{date}*.csv"
	if len(glob.glob(expected_filename))==0:
		raise Exception(f"Error: '{filename}' was not downloaded.")
	else:
		logging.info(f"'{expected_filename}' successfully downloaded")


#Try Every 30 Seconds for 30 minutes
@retry(wait=wait_fixed(30), stop=stop_after_attempt(60))
def download_from_ftp():
	# TODO: all files are getting downloaded to local since we aren't deleting remote files
	conn = ftp.Connection()
	conn.download_dir(SOURCEDIR,LOCALDIR)
	check_todays_file_exists("Automated Application Data Raw")
	check_todays_file_exists("Automated Application Data Index")


def rename_file(finalCSVname=None, stringmatch=""):
	dst = ""
	filelist = sorted(os.listdir(LOCALDIR), key=lambda x: os.path.getctime(LOCALDIR + '/' + x))
	for filename in filelist:
	 	if stringmatch in filename:
	 		src = f'{LOCALDIR}/{filename}'
	 		dst = f'{LOCALDIR}/{finalCSVname}'
	 		os.rename(src, dst)
	if os.path.exists(dst):
		logging.info(f"'{dst}' Successfully Renamed")
	else:
		raise Exception(f"Error: '{LOCALDIR}/{finalCSVname}' Was Not Successfully Renamed")
	return dst


def main():
	try:
		schema = getenv("DBSCHEMA")
		conn = MSSQL(schema=schema)
		mailer = Mailer()

		# get files
		api_request()
		if eval(getenv("DELETE_LOCAL_FILES", "True")):
			delete_data_files(LOCALDIR)
		download_from_ftp()

		# process Application Data file
		dst = rename_file(finalCSVname='AutomatedApplicationData2020.csv',stringmatch="Data Raw")
		df = read_csv_to_df(dst)
		if backup_and_truncate_table(conn, getenv("SPROC_RAW_PREP")):
			table = getenv("DB_RAW_TABLE")
			conn.insert_into(table, df)
			check_table_load(conn, schema, table)

		# process Application Data Index file
		dst = rename_file(finalCSVname='AutomatedApplicationDataIndex2020.csv',stringmatch="Data Index")
		df = read_csv_to_df(dst)
		if backup_and_truncate_table(conn, getenv("SPROC_RAW_INDEX_PREP")):
			table = getenv("DB_RAW_INDEX_TABLE")
			conn.insert_into(table, df)
			check_table_load(conn, schema, table)

		# execute sprocs
		# ChangeTrackingInsertedRowCT=process_change_tracking()
		# ChangeFactDailyStatusInsertedRowCT=process_FactDailyStatus()

		# notification
		success_message = read_logs("app.log")
		mailer.notify(results=success_message)
	except Exception as e:
		logging.exception(e)
		stack_trace = traceback.format_exc()
		mailer.notify(success=False, error_message=stack_trace)

if __name__ == "__main__":
	main()