import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_test_email():
    # Email configuration
    sender_email = "dishita.expensetracker2025@gmail.com"
    sender_password = "tpwq ccaq rrwj kwxj"
    receiver_email = "dishita.tank@gmail.com"  # Replace with your email
    
    # Create message
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = "Test Email from Budget Tracker"
    
    # Add body
    body = "This is a test email sent directly using Python's smtplib."
    message.attach(MIMEText(body, "plain"))
    
    # Create SMTP session
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()  # Enable TLS
        server.login(sender_email, sender_password)
        
        # Send email
        text = message.as_string()
        server.sendmail(sender_email, receiver_email, text)
        print(f"Test email sent successfully to {receiver_email}")
        
        # Close session
        server.quit()
    except Exception as e:
        print(f"Error sending email: {str(e)}")

if __name__ == "__main__":
    send_test_email() 