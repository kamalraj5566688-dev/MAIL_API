import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()


def send_email(to_email, subject, body, filename=None, file_data=None):

    sender_email = os.getenv("GMAIL_EMAIL")
    app_password = os.getenv("GMAIL_APP_PASSWORD")

    message = EmailMessage()

    message["From"] = sender_email
    message["To"] = to_email
    message["Subject"] = subject

    # Plain text version
    message.set_content(body)

    # HTML version
    html_content = f"""
    <html>
        <body>
            <h2>{subject}</h2>

            <p>{body}</p>

            <hr>

            <p>
                <small>
                    Sent using FastAPI Gmail Mail API
                </small>
            </p>
        </body>
    </html>
    """

    message.add_alternative(html_content, subtype="html")

    # Add attachment if provided
    if filename and file_data:

        # Detect MIME type from file extension
        extension = filename.lower().split(".")[-1]

        mime_types = {
            "jpg": ("image", "jpeg"),
            "jpeg": ("image", "jpeg"),
            "png": ("image", "png"),
            "gif": ("image", "gif"),
            "pdf": ("application", "pdf"),
            "txt": ("text", "plain"),
        }

        maintype, subtype = mime_types.get(
            extension,
            ("application", "octet-stream")
        )

        message.add_attachment(
            file_data,
            maintype=maintype,
            subtype=subtype,
            filename=filename
        )

    # Connect to Gmail SMTP
    with smtplib.SMTP("smtp.gmail.com", 587) as server:

        server.starttls()

        server.login(
            sender_email,
            app_password
        )

        server.send_message(message)

    return True

