import os
import sys
import pysftp

class Connection:
    def __init__(self):
        FTP_HOST = os.getenv("FTP_Hostname")
        FTP_USER = os.getenv("FTP_Username")
        FTP_PWD = os.getenv("FTP_PWD")

        self.cnopts = pysftp.CnOpts()
        self.cnopts.hostkeys = None
        self.ftpsrv = pysftp.Connection(host=FTP_HOST, username=FTP_USER, password=FTP_PWD, cnopts=self.cnopts)
       
   
    def testFTP(self,remotedir):
        self.data = self.ftpsrv.listdir(remotedir)
        self.ftpsrv.close()

        for i in self.data:
            print(i)

        return 1

    def download_dir(self,sourcedir,destinationdir):
        self.sourcedir = sourcedir
        result=self.ftpsrv.get_d(self.sourcedir, destinationdir, preserve_mtime=True)


    def delete_files_remotedir(self,remotedir):
        self.remotefiles = self.ftpsrv.listdir(remotedir)
        if len(self.remotefiles) >0:
            for filename in self.remotefiles: 
                self.ftpsrv.remove(f"{remotedir}/{filename}")



