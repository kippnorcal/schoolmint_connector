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


    def download_dir(self,sourcedir,destinationdir):
        self.sourcedir = sourcedir
        result=self.ftpsrv.get_d(self.sourcedir, destinationdir, preserve_mtime=True)
