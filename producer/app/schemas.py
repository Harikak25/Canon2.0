from uuid import UUID
from pydantic import BaseModel, EmailStr, Field

class SubmitIn(BaseModel):
    email_id: UUID = Field(..., description="Correlation ID for the email record")
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    subject: str = Field(..., min_length=1, max_length=255)
    body: str = Field(..., min_length=1)

    model_config = {
        "json_schema_extra": {
            "example": {
                "email_id": "2b9b2f2c-8e1e-45a5-9d0b-3e6f8c2b4a11",
                "first_name": "Ada",
                "last_name": "Lovelace",
                "email": "ada@example.com",
                "subject": "Outage report",
                "body": "Service is currently down in region X."
            }
        }
    }

class SubmitOut(BaseModel):
    status: str
    message: str