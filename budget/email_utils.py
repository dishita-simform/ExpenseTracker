import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.conf import settings
import ssl

def send_email_direct(subject, message, recipient_list):
    """
    Send an email directly using smtplib with better error handling.
    """
    try:
        # Create message
        msg = MIMEMultipart()
        msg["From"] = settings.DEFAULT_FROM_EMAIL
        msg["To"] = ", ".join(recipient_list)
        msg["Subject"] = subject
        
        # Add body
        msg.attach(MIMEText(message, "plain"))
        
        # Create SSL context
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        # Create SMTP session
        server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        
        # Login
        server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        
        # Send email
        server.sendmail(
            settings.DEFAULT_FROM_EMAIL,
            recipient_list,
            msg.as_string()
        )
        
        # Close session
        server.quit()
        
        return True, "Email sent successfully"
    except Exception as e:
        error_message = f"Error sending email: {str(e)}"
        print(error_message)
        return False, error_message 