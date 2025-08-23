from fastapi import FastAPI
from sqlalchemy.orm import Session
from .db import SessionLocal, engine
from .models import Base, EmailRecord
from .kafka_consumer import start_consumer
from .email_sender import send_email
import traceback
from threading import Thread
from pydantic import BaseModel

Base.metadata.create_all(bind=engine)
app = FastAPI(
    title="Consumer API",
    version="1.0.0",
    description=(
        "Consumer service that listens to Kafka messages and sends emails.\n\n"
        "OpenAPI JSON at /openapi.json. Swagger UI at /docs. ReDoc at /redoc."
    ),
    terms_of_service="https://canon.local/terms",
    license_info={"name": "Proprietary"},
    docs_url="/docs",
    redoc_url="/redoc",
)

@app.on_event("startup")
async def boot():
    def handle(message: dict) -> None:
        rec_id = message.get("id")
        if not rec_id:
            print("Skip message without id")
            return
        db: Session = SessionLocal()
        try:
            rec = db.get(EmailRecord, rec_id)
            if not rec:
                print("Record not found for id", rec_id)
                return
            try:
                # --- Build a professional acknowledgement email ---
                email_subject = f"Thank you for contacting us – Ticket {rec.email_id}"

                body_lines = [
                    f"Hello {rec.first_name},",
                    "",
                    "Thank you for reaching out to us. We have successfully received your request regarding:",
                    f'"{rec.subject}"',
                    "",
                    "Details you provided:",
                    "",
                    f"{rec.body}",
                    "",
                    f"Your reference ticket number is {rec.email_id}.",
                ]

                # If a file was included, mention it in the email body
                if getattr(rec, "attachment_name", None):
                    size_bytes = len(rec.attachment_data) if getattr(rec, "attachment_data", None) else 0
                    body_lines.extend([
                        "",
                        "We also received the following file with your request:",
                        f"- {rec.attachment_name} ({size_bytes} bytes)",
                    ])

                body_lines.extend([
                    "",
                    "Best regards,",
                    "CANON Support Team",
                ])

                email_body = "\n".join(body_lines)

                send_email(
                    to_addr=rec.email,
                    subject=email_subject,
                    body=email_body,
                    attachment_name=rec.attachment_name,
                    attachment_bytes=rec.attachment_data
                )
                print("Email sent for", rec_id)
            except Exception as e:
                print("Email send error:", e)
                traceback.print_exc()
        finally:
            db.close()

    # Run the Kafka consumer in a background thread so the HTTP server stays responsive
    Thread(target=start_consumer, args=(handle,), daemon=True).start()

# Health response model
class HealthResp(BaseModel):
    ok: bool

@app.get(
    "/health",
    response_model=HealthResp,
    tags=["Health"],
    summary="Health check",
    description="Returns ok:true if the consumer service is running and serving docs.",
)
def health():
    return {"ok": True}
