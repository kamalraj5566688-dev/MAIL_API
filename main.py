import sys
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Response
from fastapi.responses import FileResponse
from email_service import (
    send_brevo_request,
    parse_recipients_file,
    send_bulk_personalized
)

sys.stdout.reconfigure(line_buffering=True)

app = FastAPI(title="Mail Dispatch Studio")

BASE_DIR = Path(__file__).resolve().parent
HTML_FILE = BASE_DIR / "index.html"


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)


@app.get("/health", tags=["Monitoring"])
async def health_check():
    return {"status": "ok", "service": "Mail Dispatch Studio"}


@app.get("/", response_class=FileResponse)
@app.get("/index.html", response_class=FileResponse)
async def home():
    if not HTML_FILE.is_file():
        raise HTTPException(status_code=404, detail="index.html not found.")
    return FileResponse(HTML_FILE, media_type="text/html")


@app.post("/send-mail")
async def send_mail_endpoint(
    to: Optional[str] = Form(None),
    cc: Optional[str] = Form(None),
    bcc: Optional[str] = Form(None),
    subject: str = Form(...),
    message: str = Form(...),
    file: Optional[UploadFile] = File(None),
    recipients_file: Optional[UploadFile] = File(None)
):
    # Parse CC and BCC
    cc_list = [e.strip() for e in cc.split(",") if e.strip()] if cc else None
    bcc_list = [e.strip() for e in bcc.split(",") if e.strip()] if bcc else None

    # Read attachment if provided
    att_name = None
    att_data = None
    if file and file.filename:
        att_name = file.filename
        att_data = await file.read()

    # MODE A: Bulk Personalization via Spreadsheet (.csv or .xlsx)
    if recipients_file and recipients_file.filename:
        file_bytes = await recipients_file.read()
        records = parse_recipients_file(recipients_file.filename, file_bytes)

        if not records:
            raise HTTPException(
                status_code=400,
                detail="No valid recipient emails were detected in the uploaded file."
            )

        result = send_bulk_personalized(
            records=records,
            subject_template=subject,
            body_template=message,
            cc_list=cc_list,
            bcc_list=bcc_list,
            attachment_name=att_name,
            attachment_data=att_data
        )

        return {
            "mode": "bulk_personalization",
            "message": f"Successfully delivered {result['successful']} of {result['total']} personalized emails!",
            "details": result
        }

    # MODE B: Direct Recipients
    elif to and to.strip():
        to_list = [e.strip() for e in to.split(",") if e.strip()]
        if not to_list:
            raise HTTPException(status_code=400, detail="Please enter at least one recipient email.")

        ok, msg = send_brevo_request(
            to_list=to_list,
            subject=subject,
            body=message,
            cc_list=cc_list,
            bcc_list=bcc_list,
            attachment_name=att_name,
            attachment_data=att_data
        )

        if not ok:
            raise HTTPException(status_code=500, detail=msg)

        return {
            "mode": "standard_dispatch",
            "message": f"Email delivered successfully to {len(to_list)} recipient(s)!",
            "to": to_list,
            "cc": cc_list,
            "bcc": bcc_list
        }

    else:
        raise HTTPException(
            status_code=400,
            detail="Please provide recipient emails in 'To' or upload a CSV/XLSX spreadsheet."
        )