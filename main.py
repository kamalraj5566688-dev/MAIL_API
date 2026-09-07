from fastapi import FastAPI, UploadFile, File, Form

from email_service import send_email


app = FastAPI()


@app.get("/")
def home():
    return {
        "message": "Mail API is running!"
    }


@app.post("/send-mail")
async def send_mail(
    to: str = Form(...),
    subject: str = Form(...),
    message: str = Form(...),
    file: UploadFile = File(...)
):

    # Read uploaded file
    file_data = await file.read()

    # Send email with attachment
    send_email(
        to_email=to,
        subject=subject,
        body=message,
        filename=file.filename,
        file_data=file_data
    )

    return {
        "message": "Email sent successfully!",
        "to": to,
        "subject": subject,
        "filename": file.filename
    }