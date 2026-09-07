from pathlib import Path
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks, Response
from fastapi.responses import FileResponse
from email_service import send_email

app = FastAPI(title="Mail Dispatch Studio")

BASE_DIR = Path(__file__).resolve().parent
HTML_FILE = BASE_DIR / "index.html"


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Silences browser favicon requests to avoid 404 logs."""
    return Response(status_code=204)


@app.get("/health", tags=["Monitoring"])
async def health_check():
    """Ping endpoint for UptimeRobot to prevent Render 15-minute sleep."""
    return {"status": "ok", "service": "Mail Dispatch Studio"}


@app.get("/", response_class=FileResponse)
@app.get("/index.html", response_class=FileResponse)
async def home():
    """Serves the frontend interface."""
    if not HTML_FILE.is_file():
        raise HTTPException(
            status_code=404,
            detail=f"index.html was not found in {BASE_DIR}."
        )
    return FileResponse(HTML_FILE, media_type="text/html")


@app.post("/send-mail")
async def send_mail_endpoint(
    background_tasks: BackgroundTasks,
    to: str = Form(...),
    subject: str = Form(...),
    message: str = Form(...),
    file: Optional[UploadFile] = File(None)
):
    """Processes comma-separated recipients and offloads dispatch to background tasks."""
    recipient_list = [email.strip() for email in to.split(",") if email.strip()]

    if not recipient_list:
        raise HTTPException(
            status_code=400,
            detail="Please provide at least one valid recipient email."
        )

    filename = None
    file_data = None

    if file and file.filename:
        filename = file.filename
        file_data = await file.read()

    # Offload SMTP transfer so the UI returns immediately
    background_tasks.add_task(
        send_email,
        to_emails=recipient_list,
        subject=subject,
        body=message,
        filename=filename,
        file_data=file_data
    )

    return {
        "message": f"Email dispatched to {len(recipient_list)} recipient(s)!",
        "recipients": recipient_list,
        "subject": subject,
        "filename": filename
    }
