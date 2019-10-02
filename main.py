import argparse
import datetime 
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
import downloadftp
from mailer import Mailer

LOCALDIR = 'files'
RAWTABLE = getenv("DB_RAW_TABLE", 'schoolmint_ApplicationData_raw')
RAWINDEXTABLE = getenv("DB_RAW_INDEX_TABLE", 'schoolmint_ApplicationDataIndex_raw')


logging.basicConfig(
	handlers = [logging.FileHandler(filename="app.log",mode='w+'), logging.StreamHandler(sys.stdout)],
	level=logging.INFO,
	format="%(asctime)s | %(levelname)s: %(message)s",
	datefmt="%Y-%m-%d %I:%M:%S%p %Z",
)


def read_logs(filename):
	with open(filename) as f:
		return f.read()

def read_from_csv(CSVFilename):

	#Ensure File Really Exists
	if (not os.path.isfile(CSVFilename)):
		raise Exception(f'Error: "{CSVFilename}" File Does Not Exists. Most likely problem downloading from sFTP')

	#Load CSV into Pandas DF
	df = pd.read_csv(CSVFilename,  sep=',', quotechar = '"' , doublequote = True,dtype=str,header=0)

	#Ensure Data is really in the DataFrame
	RowsImported=(len(df.index))
	if (RowsImported == 0):
		raise Exception(f'Error - No Data Was Loaded From CSV File: "{CSVFilename}"')
	else:
		logging.info(f'{RowsImported} Rows Successfully Imported From CSV File')
		
	return RowsImported,df

def insert_into_table(df,Schema,Table,prepare_sproc):
	

	conn = MSSQL()
	result=conn.exec_sproc(prepare_sproc)
	InitialRowCT=result.fetchone()[0]

	#Ensure Destination Table is Clean and Ready to be Loaded
	if (InitialRowCT == 0 ):

		#Load table from DF
		conn.insert_into(Table, df)

		#Get Counts Of Loaded Data
		sql=f"select count(1) ct from {Schema}.{Table};"
		result=conn.query(sql)
		RowCT=result['ct'].values[0]

		
		#Ensure data loaded successfully into destination table. If not, reload from backup table.
		if (RowCT == 0 ):
			sql=f"insert into {Schema}.{Table} select * from {Schema}.{Table}_backup;select count(1) ct from {Schema}.{Table};"
			result=conn.query(sql)
			InsertedRowCT=result['ct'].values[0]

			raise Exception(f'Error No Rows Loaded Into Table. {InsertedRowCT} Rows Reverted From Backup Table')
		else:
			#Since we loaded data into destination table successfully. Lets get count of rows in final backup table.
			sql=f"select count(1) ct from {Schema}.{Table}_backup;"
			result=conn.query(sql)
			BackupRowCT=result['ct'].values[0]
			
			logging.info(f'{BackupRowCT} Rows Successfully Loaded into Backup Table')
			logging.info(f'{RowCT} Rows Successfully Loaded into Table')


	else:
		raise Exception('Error Loading Data. Table Was Not Truncated.')		

	return BackupRowCT,RowCT


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


#Try Every 30 Seconds for 30 minutes
@retry(wait = wait_fixed(30) , stop=stop_after_attempt(60))
def download_files(sourcedir=None,localdir=None,finalCSVname=None,RemoteFileIncludeString=""):
	#DownloadNewFiles
	downloading = downloadftp.Connection()
	downloading.download_dir(sourcedir,localdir)
	
	#Rename Latest Downloaded File Index File
	dst=""
	filelist =  sorted(os.listdir(localdir), key = lambda x: os.path.getctime(localdir + '/' + x))   
	for filename in filelist:
	 	if RemoteFileIncludeString in filename:
	 		src =localdir + '/' + filename 
	 		dst =localdir + '/' +  finalCSVname
	 		os.rename(src, dst) 

	if os.path.exists(dst):
		logging.info(f'{dst} Successfully Downloaded')
	else:
		raise Exception(f"Error: '{localdir}/{finalCSVname}' Was Not Successfully Downloaded")


def main():
	try:
		Schema = getenv("DBSCHEMA", 'custom')

		raw_sproc='sproc_SchoolMint_Raw_PrepareTables'
		index_sproc='sproc_SchoolMint_RawIndex_PrepareTables'

		mailer = Mailer()

		# Hit API
		api_request()

		if eval(getenv("DELETE_LOCAL_FILES", "True")):
			delete_data_files(LOCALDIR)

		download_files(sourcedir='schoolmint',localdir='files',finalCSVname='AutomatedApplicationData2020.csv',RemoteFileIncludeString="Data Raw")

		#Load Data Frame from Downloaded CSV
		RawRowsImported, df= read_from_csv('files/AutomatedApplicationData2020.csv')

		#Add SchoolYear4Digit to DataFrame
		df['SchoolYear4Digit'] = getenv("SchoolYear4Digit", '2021')

		#Load Database from DataFrame
		RawBackupRowCT, RawRowCT= insert_into_table(df, Schema,RAWTABLE,raw_sproc)

		download_files(sourcedir='schoolmint',localdir='files',finalCSVname='AutomatedApplicationDataIndex2020.csv',RemoteFileIncludeString="Data Index")
	
		#Load Data Frame from Downloaded CSV
		RawIndexRowsImported, df= read_from_csv('files/AutomatedApplicationDataIndex2020.csv')

		#Add SchoolYear4Digit to DataFrame
		df['SchoolYear4Digit'] = getenv("SchoolYear4Digit", '2021')

		#Load Database from DataFrame
		RawIndexBackupRowCT, RawIndexRowCT= insert_into_table(df, Schema,RAWINDEXTABLE,index_sproc)

		#Create Change Tracking Rows
		ChangeTrackingInsertedRowCT=process_change_tracking()

		#Create FactDailyStatus Rows
		ChangeFactDailyStatusInsertedRowCT=process_FactDailyStatus()

		#Send Success Message
		success_message = read_logs("app.log")
		mailer.notify(results=success_message)

	except Exception as e:
		logging.exception(e)
		stack_trace = traceback.format_exc()
		mailer.notify(success=False, error_message=stack_trace)

if __name__ == "__main__":
	main()