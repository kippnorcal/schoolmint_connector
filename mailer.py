from smtplib import SMTP_SSL
from os import getenv
from email.mime.text import MIMEText


class Mailer:
    def __init__(self):
        self.user = getenv("GMAIL_USER")
        self.password = getenv("GMAIL_PWD")
        self.server = SMTP_SSL("smtp.gmail.com", 465)
        self.from_address = "KIPP Bay Area Job Notification"
        self.to_name = getenv("TO_NAME")
        self.to_address = getenv("TO_ADDRESS")
        self.to_bcc = getenv("BCC_ADDRESS",'')

    def _subject_line(self):
        subject_type = "Success" if self.success else "Error"
        return f"SchoolMint - {subject_type}"

    def _body_text(self):
        if self.success:
            return f"SchoolMint was successful:\n{self.results}"
        else:
            return f"SchoolMint encountered an error:\n{self.error_message}"

    def _message(self):
        msg = MIMEText(self._body_text())
        msg["Subject"] = self._subject_line()
        msg["From"] = self.from_address
        msg["To"] = self.to_name + ' <'+self.to_address+'>'
        return msg.as_string()

    def notify(self, results=None, success=True, error_message=None):
        self.results = results
        self.success = success
        self.error_message = error_message
        with self.server as s:
            s.login(self.user, self.password)
            msg = self._message()
            recpt=[self.to_address ,self.to_bcc]
            s.sendmail(self.user, recpt, msg)

    def send_mail(self, EmailFrom, EmailBody, EmailCC, EmailBCC, EmailTo, EmailSubject  ):
        msg = MIMEText(EmailBody)
        msg["Subject"] = EmailSubject
        msg["From"] = EmailFrom
        msg["To"] = EmailTo
        msg["CC"] = EmailCC
        msg=msg.as_string()

        with self.server as s:
            s.login(self.user, self.password)
            recpt=[EmailTo ,EmailBCC]
            s.sendmail(self.user, recpt, msg)            
