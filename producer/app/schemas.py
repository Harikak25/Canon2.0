from pydantic import BaseModel, EmailStr, Field

class SubmitIn(BaseModel):
    email_id: EmailStr = Field(..., description="Email address identifier")
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    subject: str = Field(..., min_length=1, max_length=255)
    body: str = Field(..., min_length=1)

    model_config = {
        "json_schema_extra": {
            "example": {
                "email_id": "ada@example.com",
                "first_name": "Ada",
                "last_name": "Lovelace",
                "subject": "Outage report",
                "body": "Service is currently down in region X."
            }
        }
    }

class SubmitOut(BaseModel):
    id: str
    status: str
    warning: str | None = None