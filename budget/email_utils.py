from django.core.mail import send_mail
from django.conf import settings

def send_email_direct(subject, message, recipient_list):
    """
    Send an email directly using Django's email backend.
    
    Args:
        subject (str): Email subject
        message (str): Email body message
        recipient_list (list): List of recipient email addresses
        
    Returns:
        tuple: (success (bool), message (str))
    """
    try:
        sent = send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=False
        )
        if sent:
            return True, "Email sent successfully"
        return False, "Failed to send email"
    except Exception as e:
        return False, f"Error sending email: {str(e)}" 