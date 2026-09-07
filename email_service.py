import os
import smtplib
from email.message import EmailMessage
from typing import List, Union, Optional
from dotenv import load_dotenv

load_dotenv()


def send_email(
    to_emails: Union[str, List[str]],
    subject: str,
    body: str,
    filename: Optional[str] = None,
    file_data: Optional[bytes] = None
) -> bool:
    sender_email = os.getenv("GMAIL_EMAIL")
    raw_password = os.getenv("GMAIL_APP_PASSWORD")

    # Clean credentials and eliminate accidental spaces
    sender_email = sender_email.strip() if sender_email else None
    app_password = raw_password.replace(" ", "").strip() if raw_password else None

    if not sender_email or not app_password:
        print("[CONFIG ERROR] Missing GMAIL_EMAIL or GMAIL_APP_PASSWORD in environment variables.")
        return False

    # Normalize comma-separated string or list to clean recipient array
    if isinstance(to_emails, str):
        recipients = [email.strip() for email in to_emails.split(",") if email.strip()]
    else:
        recipients = [email.strip() for email in to_emails if email.strip()]

    if not recipients:
        print("[VALIDATION ERROR] No valid recipient addresses provided.")
        return False

    print(f"[DISPATCH START] Preparing to send to {len(recipients)} recipient(s): {recipients}")

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

    mime_types = {
        "jpg": ("image", "jpeg"),
        "jpeg": ("image", "jpeg"),
        "png": ("image", "png"),
        "gif": ("image", "gif"),
        "pdf": ("application", "pdf"),
        "txt": ("text", "plain"),
        "zip": ("application", "zip"),
    }

    try:
        # Use Port 465 (Direct SSL) to bypass Render port 587 throttling
        print("[SMTP] Connecting to smtp.gmail.com:465 with direct SSL...")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as server:
            print("[SMTP] Authenticating with Google...")
            server.login(sender_email, app_password)
            print("[SMTP] Authentication successful.")

            for recipient in recipients:
                message = EmailMessage()
                message["From"] = f"Mail Dispatch Studio <{sender_email}>"
                message["To"] = recipient
                message["Subject"] = subject
                message.set_content(body)
                message.add_alternative(html_content, subtype="html")

                if filename and file_data:
                    extension = filename.lower().split(".")[-1]
                    maintype, subtype = mime_types.get(extension, ("application", "octet-stream"))
                    message.add_attachment(
                        file_data,
                        maintype=maintype,
                        subtype=subtype,
                        filename=filename
                    )

                server.send_message(message)
                print(f"[MAIL SENT] Delivered to -> {recipient}")

        print("[DISPATCH COMPLETE] All messages dispatched successfully.")
        return True

    except smtplib.SMTPAuthenticationError as e:
        print(f"[AUTH ERROR] Google rejected your credentials. Check GMAIL_APP_PASSWORD: {e}")
    except smtplib.SMTPConnectError as e:
        print(f"[CONNECTION ERROR] Could not establish connection to smtp.gmail.com: {e}")
    except Exception as e:
        print(f"[UNEXPECTED ERROR] {type(e).__name__}: {e}")

    return False
