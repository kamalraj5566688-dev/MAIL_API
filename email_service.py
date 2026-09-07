import os
import smtplib
from email.message import EmailMessage
from typing import List, Union
from dotenv import load_dotenv

load_dotenv()


def send_email(
    to_emails: Union[str, List[str]], 
    subject: str, 
    body: str, 
    filename: str = None, 
    file_data: bytes = None
) -> bool:
    sender_email = os.getenv("GMAIL_EMAIL")
    app_password = os.getenv("GMAIL_APP_PASSWORD")

    if not sender_email or not app_password:
        raise ValueError("Missing GMAIL_EMAIL or GMAIL_APP_PASSWORD in environment.")

    # Normalize comma-separated string or list to clean recipient array
    if isinstance(to_emails, str):
        recipients = [email.strip() for email in to_emails.split(",") if email.strip()]
    else:
        recipients = [email.strip() for email in to_emails if email.strip()]

    if not recipients:
        raise ValueError("No valid recipient addresses provided.")

    html_content = f"""<!DOCTYPE html>
<html>
    <body style="margin: 0; padding: 40px 20px; background-color: #f5f5f7; font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif; color: #1d1d1f; letter-spacing: -0.374px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 18px; border: 1px solid rgba(0, 0, 0, 0.08); padding: 40px; box-sizing: border-box;">
            <div style="font-size: 12px; font-weight: 600; color: #7a7a7a; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 16px;">Mail Dispatch</div>
            <h1 style="font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif; font-size: 28px; font-weight: 600; line-height: 1.15; margin: 0 0 20px 0; color: #1d1d1f; letter-spacing: -0.374px;">{subject}</h1>
            <div style="font-size: 17px; line-height: 1.47; color: #1d1d1f; white-space: pre-wrap;">{body}</div>
            <hr style="border: none; border-top: 1px solid #f0f0f0; margin: 32px 0 20px 0;">
            <p style="font-size: 12px; color: #7a7a7a; line-height: 1.2; margin: 0;">
                Dispatched securely via FastAPI &bull; Designed with Apple Aesthetics
            </p>
        </div>
    </body>
</html>
"""

    # Connect to SMTP once and send personalized individual copies
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender_email, app_password)

        for recipient in recipients:
            message = EmailMessage()
            message["From"] = sender_email
            message["To"] = recipient
            message["Subject"] = subject
            message.set_content(body)
            message.add_alternative(html_content, subtype="html")

            if filename and file_data:
                extension = filename.lower().split(".")[-1]
                mime_types = {
                    "jpg": ("image", "jpeg"),
                    "jpeg": ("image", "jpeg"),
                    "png": ("image", "png"),
                    "gif": ("image", "gif"),
                    "pdf": ("application", "pdf"),
                    "txt": ("text", "plain"),
                    "zip": ("application", "zip"),
                }
                maintype, subtype = mime_types.get(extension, ("application", "octet-stream"))
                message.add_attachment(
                    file_data,
                    maintype=maintype,
                    subtype=subtype,
                    filename=filename
                )

            server.send_message(message)

    return True