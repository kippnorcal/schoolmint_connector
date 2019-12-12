from smtplib import SMTP_SSL
from os import getenv
from email.mime.text import MIMEText


class Mailer:
    """Class to send email notifications about the job status."""

    def __init__(self):
        """Initialize connection to the mail server."""
        self.user = getenv("GMAIL_USER")
        self.password = getenv("GMAIL_PWD")
        self.server = SMTP_SSL("smtp.gmail.com", 465)
        self.from_address = "KIPP Bay Area Job Notification"
        self.to_name = getenv("TO_NAME")
        self.to_address = getenv("TO_ADDRESS")
        self.to_bcc = getenv("BCC_ADDRESS", "")

    def _subject_line(self):
        """
        Return success/error in subject based on job status.
        
        :return: Job name and success/error status
        :rtype: String
        """
        subject_type = "Success" if self.success else "Error"
        return f"SchoolMint - {subject_type}"

    def _body_text(self):
        """
        Generate email body message based on job status.
        
        :return: Email body with results or error message
        :rtype: String
        """
        if self.success:
            return f"SchoolMint was successful:\n{self.results}"
        else:
            return f"SchoolMint encountered an error:\n{self.error_message}"

    def _message(self):
        """
        Build the email message body.
        
        :return: Message text
        :rtype: MIMEText object
        """
        msg = MIMEText(self._body_text())
        msg["Subject"] = self._subject_line()
        msg["From"] = self.from_address
        msg["To"] = self.to_name + " <" + self.to_address + ">"
        return msg.as_string()

    def notify(self, results=None, success=True, error_message=None):
        """
        Send the notification message.
        
        :param results: contains the logger messages
        :type results: String
        :param success: True if the job was successful, False if there was an error
        :type success: Boolean
        :param error_message: contains stack trace if there is one
        :type error_message: String
        """
        self.results = results
        self.success = success
        self.error_message = error_message
        with self.server as s:
            s.login(self.user, self.password)
            msg = self._message()
            recpt = [self.to_address, self.to_bcc]
            s.sendmail(self.user, recpt, msg)
