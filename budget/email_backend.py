import ssl
import smtplib
from django.core.mail.backends.smtp import EmailBackend
from django.conf import settings

class CustomEmailBackend(EmailBackend):
    """
    Custom email backend that handles SSL certificate issues more gracefully.
    """
    def open(self):
        """
        Override the open method to set the SSL context properly.
        """
        if self.connection:
            return False
        
        try:
            # Create SSL context with certificate verification disabled
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # Create SMTP connection with the SSL context
            self.connection = smtplib.SMTP(self.host, self.port)
            self.connection.ehlo()
            self.connection.starttls(context=ssl_context)
            self.connection.ehlo()
            
            if self.username and self.password:
                self.connection.login(self.username, self.password)
            
            return True
        except Exception as e:
            print(f"Error opening email connection: {str(e)}")
            return False 