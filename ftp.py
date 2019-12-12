import os
import datetime as dt
import sys
import time

import pysftp


class FTP:
    """Class for the local FTP connection."""

    def __init__(self):
        """Initialize connection to the FTP server."""
        FTP_HOST = os.getenv("FTP_HOSTNAME")
        FTP_USER = os.getenv("FTP_USERNAME")
        FTP_PWD = os.getenv("FTP_PWD")
        self.ARCHIVE_MAX_DAYS = int(os.getenv("ARCHIVE_MAX_DAYS"))

        self.cnopts = pysftp.CnOpts()
        self.cnopts.hostkeys = None
        self.ftpsrv = pysftp.Connection(
            host=FTP_HOST, username=FTP_USER, password=FTP_PWD, cnopts=self.cnopts
        )

    def download_dir(self, remotedir, localdir):
        """
        Download all files from the remote directory to the local directory.
        
        :param remotedir: Path of the remote directory that we are getting files from (ie. the FTP directory)
        :type remotedir: String
        :param localdir: Path of the local directory that we are saving files to
        :type localdir: String
        """
        # 3 is the number of files plus the archive directory
        if len(self.ftpsrv.listdir(remotepath=remotedir)) >= 3:
            time.sleep(30)  # wait to allow the files to finish uploading
            self.ftpsrv.get_d(remotedir, localdir, preserve_mtime=True)

    def _archive_file(self, file):
        """
        Place the file in an 'archive' folder within its directory.

        :param file: Path and name of the file that will be archived. 
        :type file: String
        """
        self.ftpsrv.rename(
            file, file.replace(self.remotedir, f"{self.remotedir}/archive")
        )

    def _do_nothing(self, file):
        """
        Used for files and unknown file types.

        :param file: Path and name of the file that will be ignored. 
        :type file: String
        """
        pass

    def archive_remote_files(self, remotedir):
        """
        Archive all of the files in the specified remote directory. 
        
        :param remotedir: Path of the remote directory (ie. the FTP directory)
        :type remotedir: String
        """
        self.remotedir = remotedir
        self.ftpsrv.walktree(
            self.remotedir,
            fcallback=self._archive_file,
            dcallback=self._do_nothing,
            ucallback=self._do_nothing,
            recurse=False,
        )

    def _delete_old_file(self, file):
        """
        Find the age limit based on the env variable and delete files older than this limit.

        :param file: Path and name of the file
        :type file: String
        """
        stat = self.ftpsrv.stat(file)
        age_limit = dt.datetime.now() - dt.timedelta(self.ARCHIVE_MAX_DAYS)
        if stat.st_mtime < age_limit.timestamp():
            self.ftpsrv.remove(file)

    def delete_old_archive_files(self, remotedir):
        """
        Delete old files from the archive folder.

        :param remotedir: Path of the remote directory (ie. the FTP directory)
        :type remotedir: String
        """
        archivedir = f"{remotedir}/archive"
        self.ftpsrv.walktree(
            archivedir,
            fcallback=self._delete_old_file,
            dcallback=self._do_nothing,
            ucallback=self._do_nothing,
            recurse=False,
        )
