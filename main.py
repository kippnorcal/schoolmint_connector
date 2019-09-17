from os import getenv
import argparse
import os
import pandas as pd
from sqlsorcery import MSSQL
from mailer import Mailer
import logging
import sys
import traceback
import downloadftp
from tenacity import *
import datetime 
import time

from api import API




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
	conn = Connection()
	if eval(getenv("DEV_DB_Environment", "False")):
		#Development Environment
		sproc='sproc_zdev_Paycom_Create_ChangeTracking_Entries'
	else:
		sproc='sproc_Paycom_Create_ChangeTracking_Entries'

	result=conn.exec_sproc(sproc)	
	ChangeTrackingInsertedRowCT=result.fetchone()[0]
	logging.info(f'{ChangeTrackingInsertedRowCT} Rows Successfully Loaded into Change Log')
	
	return ChangeTrackingInsertedRowCT
	#RowCT=conn.query(sql)


def send_email_notifications():
	conn = Connection()
	if eval(getenv("DEV_DB_Environment", "False")):
		#Development Environment
		view='custom.vw_Paycom_EmailNotifications_GetUnsent_dev'	
	else:
		view='custom.vw_Paycom_EmailNotifications_GetUnsent'
		
	result=conn.query(f'select * from {view}')  ##View  
	result.fillna("", inplace = True) 
	EmailsSent=0
	for index,row in result.iterrows():
		Email_To=getenv("TEST_EMAIL_ADDRESS", row['Email_To'])
		Email_CC=getenv("TEST_CC_ADDRESS", row['Email_CC'])
		Email_BCC=getenv("TEST_BCC_ADDRESS",'')
		EmailSubject_EventDate=row['EmailSubject_EventDate']
		EmailSubject=f"{row['EmailBody_EventType']} - {row['Employee_Name']} ({row['EmailSubject_EventDate']} Change ID = {row['ChangeID']})"
		msg=f'''Employee Change Event: {row['EmailBody_EventType']}
Change Date in Paycom: {row['ChangeTracking_Date']}

Actions Required: {row['EmailBody_Actions']}
 
{row['EmailBody_Details_PlainText']}
'''
		mailer = Mailer()
		mailer.send_mail( "EmployeeUpdates KIPP Bay Area <techprovisioning@kippbayarea.org>", msg, Email_CC, Email_BCC , Email_To, EmailSubject)
		if eval(getenv("DEV_DB_Environment", "False")):
			#Development Environment
			sproc='sproc_Paycom_zdev_EmailNotifications_MarkSent'			
		else:
			sproc='sproc_Paycom_EmailNotifications_MarkSent'

		result=conn.exec_sproc(f"{sproc} @ChangeID={row['ChangeID']}")
		EmailsSent += 1

	logging.info(f'{EmailsSent} Emails Sent')
	return EmailsSent




def process_email_notifications():
	##Generate Email Notifications Rows
	conn = Connection()
	if eval(getenv("DEV_DB_Environment", "False")):
		#Development Environment
		sproc='sproc_zdev_Paycom_EmailNotifications_Populate'			
	else:
		sproc='sproc_Paycom_EmailNotifications_Populate'

	result=conn.exec_sproc(sproc)
	EmailNotificationsInsertedRowCT=result.fetchone()[0]
	logging.info(f'{EmailNotificationsInsertedRowCT} Rows Successfully Loaded into Email Notifications')
	
	return EmailNotificationsInsertedRowCT

def api_request():
	api = API()
	api_tokens = [getenv("API_TOKEN_DATA"),getenv("API_TOKEN_DATA_INDEX")]
	for api_token in api_tokens:
		api.post_demand_export(api_token=api_token)

#Try Every 30 Seconds for 30 minutes
@retry(wait = wait_fixed(30) , stop=stop_after_attempt(60))
def download_files(deletelocalfiles=False,sourcedir=None,localdir=None,finalCSVname=None,DeleteRemoteFiles=False,RemoteFileIncludeString=""):
	#Clean Out Destination Directory
	if deletelocalfiles:
		filelist = [ filename for filename in os.listdir(localdir) ]
		for filename in filelist:
			if RemoteFileIncludeString in filename:
				os.remove(os.path.join(localdir, filename))


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

	#Delete Files From Remote Server When Done Downloading
	if DeleteRemoteFiles:
	 	downloading.delete_files_remotedir(sourcedir)



def main():
	try:
		#Set Up ENV Variables
		Schema = getenv("DBSCHEMA", 'custom')

		#eval is used here to convert value from string to boolean
		deletelocalfiles= eval(getenv("DELETELOCALFILES", "True"))
		DeleteRemoteFiles=eval(getenv("DELETE_REMOTE_FILES", "True"))

		if eval(getenv("DEV_DB_Environment", "False")):
			#Development Environment
			RawTable = getenv("DBRAWTABLE", 'schoolmint_zdevpk_ApplicationData_raw')
			RawIndexTable = getenv("DBRAW_INDEX_TABLE", 'schoolmint_zdevpk_applicationdataindex_raw')
			raw_sproc='sproc_zdev_schoolmint_raw_preparetables'
			index_sproc='sproc_zdev_schoolmint_rawindex_preparetables'
		else:
			raw_sproc='Prod Sproc'
			index_sproc='Prod Sproc'



		#Instantiate Mailer
		mailer = Mailer()

		# Hit API
		api_request()

		# Check if files exist and wait if they don't

		#Download Latest Files

		download_files(deletelocalfiles=deletelocalfiles,sourcedir='schoolmint',localdir='files',finalCSVname='AutomatedApplicationData2020.csv',DeleteRemoteFiles=False,RemoteFileIncludeString="Data Raw")

		#Load Data Frame from Downloaded CSV
		RawRowsImported, df= read_from_csv('files/AutomatedApplicationData2020.csv')

		#Load Database from DataFrame
		RawBackupRowCT, RawRowCT= insert_into_table(df, Schema,RawTable,raw_sproc)

		download_files(deletelocalfiles=deletelocalfiles,sourcedir='schoolmint',localdir='files',finalCSVname='AutomatedApplicationDataIndex2020.csv',DeleteRemoteFiles=DeleteRemoteFiles,RemoteFileIncludeString="Data Index")
	
		#Load Data Frame from Downloaded CSV
		RawIndexRowsImported, df= read_from_csv('files/AutomatedApplicationDataIndex2020.csv')

		#Load Database from DataFrame
		RawIndexBackupRowCT, RawIndexRowCT= insert_into_table(df, Schema,RawIndexTable,index_sproc)

		#Create Change Tracking Rows
		# ChangeTrackingInsertedRowCT=process_change_tracking()

		# #Create Email Notifications Rows
		# EmailNotificationsInsertedRowCT=process_email_notifications()

		# #Send Email Notifications
		# EmailsSent=send_email_notifications()

		#Send Success Message
		success_message = read_logs("app.log")
		mailer.notify(results=success_message)
		# {ChangeTrackingInsertedRowCT} Rows Successfully Loaded into Change Log
		# {EmailNotificationsInsertedRowCT} Rows Successfully Loaded into Email Notifications Table
		# {EmailsSent} Emails Sent
		# '''
		# mailer.notify(results=msg)


	except Exception as e:
		logging.exception(e)
		stack_trace = traceback.format_exc()
		mailer.notify(success=False, error_message=stack_trace)

if __name__ == "__main__":
	main()