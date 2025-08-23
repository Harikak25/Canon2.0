import uuid, os
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from .db import SessionLocal, engine
from .models import Base, EmailRecord
from .kafka_producer import publish
from .schemas import SubmitIn


Base.metadata.create_all(bind=engine)
app = FastAPI(
    title="Producer API",
    version="1.0.0",
    description=(
        "Producer service that accepts complaint submissions and publishes IDs to Kafka.\n\n"
        "OpenAPI JSON at /openapi.json. Swagger UI at /docs. ReDoc at /redoc."
    ),
    terms_of_service="https://canon.local/terms",
    license_info={"name": "Proprietary"},
    docs_url="/docs",
    redoc_url="/redoc",
)

class SubmitOut(BaseModel):
    id: str
    status: str
    warning: str | None = None


# Health response model
class HealthResp(BaseModel):
    ok: bool

@app.get(
    "/health",
    response_model=HealthResp,
    tags=["Health"],
    summary="Health check",
    description="Returns ok:true if the producer service is running and serving docs.",
)
def health():
    return {"ok": True}


@app.post(
    "/submit",
    response_model=SubmitOut,
    status_code=201,
    tags=["Submissions"],
    summary="Create a new complaint record",
    description=(
        "Accepts a complaint payload, stores it in the database, and queues a minimal message to Kafka.\n"
        "Returns the new record id and a status."
    ),
    responses={
        500: {"description": "Database error. Please try again later."}
    },
)
async def submit(
    payload: SubmitIn = Body(
        ..., 
        examples={
            "basic": {
                "summary": "Minimum happy-path",
                "value": {
                    "email_id": "74f3a8a9-bce7-4d8b-8f1b-1c4d1f2da111",
                    "first_name": "Asha",
                    "last_name": "K",
                    "email": "asha@example.com",
                    "subject": "Login issue",
                    "body": "I cannot log in to the portal after password reset."
                }
            }
        }
    )
):
    rec_id = str(uuid.uuid4())
    db: Session = SessionLocal()
    try:
        rec = EmailRecord(
            id=rec_id,
            email_id=payload.email_id,  # UUID
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=str(payload.email),
            subject=payload.subject,
            body=payload.body,
            attachment_name=None,
            attachment_data=None,
        )
        db.add(rec)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error. Please try again later.")
    finally:
        db.close()

    warning = None
    try:
        publish({
            "id": rec_id,
            "email_id": str(payload.email_id),
            "email": str(payload.email),
            "subject": payload.subject,
        })
    except Exception:
        warning = "Message not queued to Kafka."

    return {"id": rec_id, "status": "saved", "warning": warning}
