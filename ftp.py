import base64
import datetime as dt
import os
import posixpath
import stat
import time

import paramiko


class FTP:
    """Class for the local FTP connection."""

    def __init__(self):
        """Initialize connection to the FTP server."""
        self.FTP_HOST = os.getenv("FTP_HOSTNAME")
        self.FTP_USER = os.getenv("FTP_USERNAME")
        self.FTP_PWD = os.getenv("FTP_PWD")
        self.ARCHIVE_MAX_DAYS = int(os.getenv("ARCHIVE_MAX_DAYS"))
        self.client = paramiko.SSHClient()
        self.key = self._add_hostkeys()
        self.client.connect(
            hostname=self.FTP_HOST,
            username=self.FTP_USER,
            pkey=self.key,
            allow_agent=False,
            look_for_keys=False,
        )
        self.ftpsrv = self.client.open_sftp()

    def _add_hostkeys(self):
        """
        Trusts only the sftp host key to prevent man in the middle attacks.
        Key can be acquired using OpenSSH: ssh-keyscan {sftp_url}
        """
        hostkey = paramiko.Ed25519Key.from_private_key_file("/root/.ssh/schoolmint_pipeline")
        self.client.load_host_keys("/root/.ssh/known_hosts")
        self.client.set_missing_host_key_policy(paramiko.RejectPolicy())
        return hostkey

    def close(self):
        """Close the SFTP session and the underlying SSH connection."""
        self.ftpsrv.close()
        self.client.close()

    def _list_files(self, remotedir):
        """
        List the regular files (not directories) in the remote directory.

        :param remotedir: Path of the remote directory
        :type remotedir: String
        :return: Attributes of each file, with the file name in 'filename'
        :rtype: List of paramiko.SFTPAttributes
        """
        return [
            attr
            for attr in self.ftpsrv.listdir_attr(remotedir)
            if stat.S_ISREG(attr.st_mode)
        ]

    def download_dir(self, remotedir, localdir):
        """
        Download all files from the remote directory to the local directory.

        :param remotedir: Path of the remote directory that we are getting files from (ie. the FTP directory)
        :type remotedir: String
        :param localdir: Path of the local directory that we are saving files to
        :type localdir: String
        """
        # 2 is the number of files plus the archive directory
        if len(self.ftpsrv.listdir(remotedir)) >= 2:
            time.sleep(30)  # wait to allow the files to finish uploading
            for attr in self._list_files(remotedir):
                local_file = os.path.join(localdir, attr.filename)
                self.ftpsrv.get(posixpath.join(remotedir, attr.filename), local_file)
                # preserve mtime so the latest file can be found by modification date
                os.utime(local_file, (attr.st_atime, attr.st_mtime))

    def archive_remote_files(self, remotedir):
        """
        Archive all of the files in the specified remote directory by placing
        them in an 'archive' folder within that directory.

        :param remotedir: Path of the remote directory (ie. the FTP directory)
        :type remotedir: String
        """
        for attr in self._list_files(remotedir):
            self.ftpsrv.rename(
                posixpath.join(remotedir, attr.filename),
                posixpath.join(remotedir, "archive", attr.filename),
            )

    def delete_old_archive_files(self, remotedir):
        """
        Delete files from the archive folder that are older than the
        ARCHIVE_MAX_DAYS limit.

        :param remotedir: Path of the remote directory (ie. the FTP directory)
        :type remotedir: String
        """
        age_limit = dt.datetime.now() - dt.timedelta(days=self.ARCHIVE_MAX_DAYS)
        for attr in self._list_files(remotedir):
            if attr.st_mtime < age_limit.timestamp():
                self.ftpsrv.remove(posixpath.join(remotedir, attr.filename))
