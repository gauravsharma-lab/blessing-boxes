import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from django.conf import settings

def send_sendgrid_email(subject, message, recipient_list):
    """
    Sends an email using the SendGrid HTTP API.
    Bypasses SMTP port restrictions on Render.
    """
    api_key = os.environ.get('SENDGRID_API_KEY')
    if not api_key:
        print("Error: SENDGRID_API_KEY not found in environment.")
        return False

    # Ensure recipient_list is a list
    if isinstance(recipient_list, str):
        recipient_list = [recipient_list]

    for recipient in recipient_list:
        if not recipient:
            continue
            
        email = Mail(
            from_email=settings.DEFAULT_FROM_EMAIL,
            to_emails=recipient,
            subject=subject,
            plain_text_content=message
        )
        
        try:
            sg = SendGridAPIClient(api_key)
            response = sg.send(email)
            print(f"Email sent to {recipient}. Status: {response.status_code}")
        except Exception as e:
            print(f"SendGrid Error for {recipient}: {e}")
            return False
            
    return True
