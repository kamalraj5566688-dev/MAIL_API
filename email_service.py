import os
import io
import csv
import re
import base64
import requests
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv
import openpyxl

load_dotenv()

BREVO_API_KEY = os.getenv("BREVO_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "gamerkamal028@gmail.com")
BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


def build_html_wrapper(subject: str, body: str) -> str:
    """Wraps body text in an Apple-inspired email template."""
    return f"""<!DOCTYPE html>
<html>
    <body style="margin: 0; padding: 40px 20px; background-color: #f5f5f7; font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif; color: #1d1d1f;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 18px; border: 1px solid rgba(0, 0, 0, 0.08); padding: 40px; box-sizing: border-box;">
            <div style="font-size: 12px; font-weight: 600; color: #7a7a7a; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 16px;">Mail Dispatch</div>
            <h1 style="font-size: 24px; font-weight: 600; line-height: 1.25; margin: 0 0 20px 0; color: #1d1d1f;">{subject}</h1>
            <div style="font-size: 16px; line-height: 1.55; color: #1d1d1f; white-space: pre-wrap;">{body}</div>
            <hr style="border: none; border-top: 1px solid #f0f0f0; margin: 32px 0 20px 0;">
            <p style="font-size: 12px; color: #86868b; margin: 0;">
                Dispatched securely via Mail Dispatch Studio &bull; Designed with Apple Aesthetics
            </p>
        </div>
    </body>
</html>"""


def parse_recipients_file(filename: str, content: bytes) -> List[Dict[str, str]]:
    """
    Parses .csv or .xlsx spreadsheets into normalized row dictionaries.
    Resolves unquoted carriage returns and detects delimiters automatically.
    """
    records: List[Dict[str, str]] = []
    ext = filename.lower().split(".")[-1]

    # Guard: Detect if an Excel (.xlsx) file was renamed or uploaded with a .csv extension
    if content.startswith(b"PK\x03\x04"):
        ext = "xlsx"

    if ext == "csv":
        # Decode and normalize Windows/HTTP multipart carriage returns (\r\r\n, \r\n, \r) to \n
        raw_text = content.decode("utf-8-sig", errors="ignore")
        normalized_text = (
            raw_text.replace("\r\r\n", "\n")
            .replace("\r\n", "\n")
            .replace("\r", "\n")
        )

        # Detect delimiter (comma, semicolon, or tab)
        sample = normalized_text[:2048]
        delimiter = ","
        if sample.count(";") > sample.count(",") and sample.count(";") > sample.count("\t"):
            delimiter = ";"
        elif sample.count("\t") > sample.count(","):
            delimiter = "\t"

        text_stream = io.StringIO(normalized_text, newline="")
        reader = csv.DictReader(text_stream, delimiter=delimiter)

        for row in reader:
            if not row:
                continue
            clean_row = {
                str(k).strip(): str(v).strip()
                for k, v in row.items()
                if k is not None and v is not None
            }
            if clean_row:
                records.append(clean_row)

    elif ext in ["xlsx", "xls"]:
        wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
        sheet = wb.active
        rows = list(sheet.iter_rows(values_only=True))
        if rows:
            headers = [
                str(h).strip() if h is not None else f"col_{idx}"
                for idx, h in enumerate(rows[0])
            ]
            for data_row in rows[1:]:
                row_dict = {}
                for idx, cell in enumerate(data_row):
                    if idx < len(headers):
                        row_dict[headers[idx]] = str(cell).strip() if cell is not None else ""
                if any(row_dict.values()):
                    records.append(row_dict)

    # Locate email field across common header aliases
    valid_records = []
    for rec in records:
        email_key = None
        for k in rec.keys():
            if k.lower() in ["email", "e-mail", "mail", "recipient", "to", "email address", "email_id"]:
                email_key = k
                break

        # Fallback: inspect field values for an '@' address
        if not email_key:
            for k, val in rec.items():
                if "@" in val and "." in val:
                    email_key = k
                    break

        if email_key and rec.get(email_key):
            rec["__email__"] = rec[email_key].strip()
            valid_records.append(rec)

    return valid_records


def substitute_placeholders(template: str, context: Dict[str, str]) -> str:
    """Replaces placeholders like {name} or {Company} case-insensitively."""
    lookup = {k.lower().strip(): v for k, v in context.items() if not k.startswith("__")}

    def replacer(match: re.Match) -> str:
        key = match.group(1).lower().strip()
        return lookup.get(key, match.group(0))

    return re.sub(r"\{([a-zA-Z0-9_]+)\}", replacer, template)


def send_brevo_request(
    to_list: List[str],
    subject: str,
    body: str,
    cc_list: Optional[List[str]] = None,
    bcc_list: Optional[List[str]] = None,
    attachment_name: Optional[str] = None,
    attachment_data: Optional[bytes] = None
) -> Tuple[bool, str]:
    """Transmits an email payload to Brevo's v3 REST endpoint."""
    if not BREVO_API_KEY:
        return False, "BREVO_API_KEY is not configured in environment variables."

    payload: Dict[str, Any] = {
        "sender": {"name": "Mail Dispatch Studio", "email": SENDER_EMAIL},
        "to": [{"email": e} for e in to_list],
        "subject": subject,
        "htmlContent": build_html_wrapper(subject, body),
        "textContent": body
    }

    if cc_list:
        payload["cc"] = [{"email": e} for e in cc_list]
    if bcc_list:
        payload["bcc"] = [{"email": e} for e in bcc_list]

    if attachment_name and attachment_data:
        payload["attachment"] = [
            {
                "name": attachment_name,
                "content": base64.b64encode(attachment_data).decode("utf-8")
            }
        ]

    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY.strip(),
        "content-type": "application/json"
    }

    try:
        res = requests.post(BREVO_API_URL, json=payload, headers=headers, timeout=15)
        if res.status_code in [200, 201, 202]:
            return True, res.json().get("messageId", "sent")
        else:
            return False, f"Brevo API error ({res.status_code}): {res.text}"
    except Exception as e:
        return False, str(e)


def send_bulk_personalized(
    records: List[Dict[str, str]],
    subject_template: str,
    body_template: str,
    cc_list: Optional[List[str]] = None,
    bcc_list: Optional[List[str]] = None,
    attachment_name: Optional[str] = None,
    attachment_data: Optional[bytes] = None
) -> Dict[str, Any]:
    """Sends personalized copies to each recipient parsed from a spreadsheet."""
    sent_count = 0
    failures = []

    print(f"[BULK START] Processing {len(records)} personalized records...")

    for row in records:
        target_email = row["__email__"]
        personalized_subject = substitute_placeholders(subject_template, row)
        personalized_body = substitute_placeholders(body_template, row)

        ok, msg = send_brevo_request(
            to_list=[target_email],
            subject=personalized_subject,
            body=personalized_body,
            cc_list=cc_list,
            bcc_list=bcc_list,
            attachment_name=attachment_name,
            attachment_data=attachment_data
        )

        if ok:
            sent_count += 1
            print(f"[BULK SUCCESS] Sent to {target_email}")
        else:
            failures.append({"email": target_email, "error": msg})
            print(f"[BULK FAIL] Failed for {target_email}: {msg}")

    return {
        "total": len(records),
        "successful": sent_count,
        "failed": len(failures),
        "failure_details": failures
    }