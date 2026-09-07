import os
import base64
import requests
from typing import List, Union, Optional
from dotenv import load_dotenv

load_dotenv()

BREVO_API_KEY = os.getenv("BREVO_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "kamalraj5566688@gmail.com")
BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


def send_email(
    to_emails: Union[str, List[str]],
    subject: str,
    body: str,
    filename: Optional[str] = None,
    file_data: Optional[bytes] = None
) -> bool:
    if not BREVO_API_KEY:
        print("[CONFIG ERROR] BREVO_API_KEY is missing in environment variables.")
        return False

    # Format recipients into Brevo schema [{"email": "user@example.com"}]
    if isinstance(to_emails, str):
        recipients_list = [email.strip() for email in to_emails.split(",") if email.strip()]
    else:
        recipients_list = [email.strip() for email in to_emails if email.strip()]

    if not recipients_list:
        print("[VALIDATION ERROR] No valid recipient addresses provided.")
        return False

    to_payload = [{"email": email} for email in recipients_list]

    html_content = f"""<!DOCTYPE html>
<html>
    <body style="margin: 0; padding: 40px 20px; background-color: #f5f5f7; font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif; color: #1d1d1f;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 18px; border: 1px solid rgba(0, 0, 0, 0.08); padding: 40px; box-sizing: border-box;">
            <div style="font-size: 12px; font-weight: 600; color: #7a7a7a; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 16px;">Mail Dispatch</div>
            <h1 style="font-size: 26px; font-weight: 600; line-height: 1.2; margin: 0 0 20px 0; color: #1d1d1f;">{subject}</h1>
            <div style="font-size: 16px; line-height: 1.5; color: #1d1d1f; white-space: pre-wrap;">{body}</div>
            <hr style="border: none; border-top: 1px solid #f0f0f0; margin: 32px 0 20px 0;">
            <p style="font-size: 12px; color: #7a7a7a; margin: 0;">
                Dispatched securely via FastAPI &bull; Designed with Apple Aesthetics
            </p>
        </div>
    </body>
</html>"""

    payload = {
        "sender": {"name": "Mail Dispatch Studio", "email": SENDER_EMAIL},
        "to": to_payload,
        "subject": subject,
        "htmlContent": html_content,
        "textContent": body
    }

    # Attach base64-encoded file if present
    if filename and file_data:
        b64_encoded = base64.b64encode(file_data).decode("utf-8")
        payload["attachment"] = [
            {
                "name": filename,
                "content": b64_encoded
            }
        ]

    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY.strip(),
        "content-type": "application/json"
    }

    print(f"[HTTPS DISPATCH] Sending to {len(to_payload)} recipient(s) via Brevo API...")
    try:
        response = requests.post(BREVO_API_URL, json=payload, headers=headers, timeout=15)
        if response.status_code in [200, 201, 202]:
            print(f"[MAIL SUCCESS] Delivered successfully! MessageId: {response.json().get('messageId')}")
            return True
        else:
            print(f"[BREVO API ERROR] Status {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"[REQUEST FAILED] {e}")
        return False
