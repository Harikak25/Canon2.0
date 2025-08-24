import uuid, os
import logging, traceback, time
import socket
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.requests import Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy import text
from .db import SessionLocal, engine
from .models import Base, EmailRecord
from .kafka_producer import publish
from .schemas import SubmitIn


Base.metadata.create_all(bind=engine)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("producer")



KAFKA_MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2
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

# Enable CORS for Angular dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "http://127.0.0.1:4200"
    ],  # Angular dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler to ensure endpoints never break
@app.exception_handler(Exception)
async def unhandled_exc_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

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
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))  # simple liveness check
        return {"ok": True}
    except Exception as e:
        logger.error("DB health check failed: %s", e)
        raise HTTPException(status_code=500, detail={"message": "Database not reachable"})
    finally:
        try:
            db.close()
        except Exception:
            pass


# Readiness endpoint
@app.get(
    "/ready",
    response_model=HealthResp,
    tags=["Health"],
    summary="Readiness check",
    description="Checks DB and Kafka broker reachability. Returns ok:true only if both are reachable."
)
def readiness():
    # Check DB
    db_ok = False
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        logger.error("Readiness DB check failed: %s", e)
    finally:
        try:
            db.close()
        except Exception:
            pass

    # Check Kafka by opening a TCP socket to the first bootstrap server
    kafka_ok = False
    try:
        bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
        first = bootstrap.split(",")[0].strip()
        host, port_str = first.split(":")
        with socket.create_connection((host, int(port_str)), timeout=3):
            kafka_ok = True
    except Exception as e:
        logger.error("Readiness Kafka socket check failed: %s", e)

    ok = db_ok and kafka_ok
    if ok:
        return {"ok": True}
    # If not ready, include detail and return 503 so orchestrators know it's not ready
    raise HTTPException(
        status_code=503,
        detail={"ok": False, "db_ok": db_ok, "kafka_ok": kafka_ok, "message": "Dependencies not ready"}
    )


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
                    "email_id": "asha@example.com",
                    "first_name": "Asha",
                    "last_name": "K",
                    "subject": "Login issue",
                    "body": "I cannot log in to the portal after password reset."
                }
            }
        }
    )
):
    logger.info("Received submission payload for %s", payload.email_id)
    rec_id = str(uuid.uuid4())
    db: Session = SessionLocal()
    try:
        rec = EmailRecord(
            id=rec_id,
            email_id=payload.email_id,
            first_name=payload.first_name,
            last_name=payload.last_name,
            subject=payload.subject,
            body=payload.body,
            attachment_name=None,
            attachment_data=None,
        )
        db.add(rec)
        db.commit()
        logger.info("Saved record %s to database for %s", rec_id, payload.email_id)
    except Exception:
        db.rollback()
        logger.error("Database error while saving record: %s", traceback.format_exc())
        raise HTTPException(status_code=500, detail={"message": "Database error. Please try again later."})
    finally:
        db.close()

    warning = None
    last_err = None
    for attempt in range(1, KAFKA_MAX_RETRIES + 1):
        try:
            publish({
                "id": rec_id,
                "email_id": str(payload.email_id),
                "first_name": payload.first_name,
                "last_name": payload.last_name,
                "subject": payload.subject,
                "body": payload.body,
            })
            logger.info("Published record %s to Kafka (attempt %d)", rec_id, attempt)
            last_err = None
            break
        except Exception as e:
            last_err = e
            logger.error("Kafka publish failed for %s (attempt %d/%d): %s", rec_id, attempt, KAFKA_MAX_RETRIES, e)
            traceback.print_exc()
            if attempt < KAFKA_MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS)
    if last_err is not None:
        warning = "Message not queued to Kafka."
        logger.error("All Kafka publish attempts failed for %s", rec_id)

    return {"id": rec_id, "status": "saved", "warning": warning}
