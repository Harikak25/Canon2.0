from pydantic import BaseModel, EmailStr
from uuid import UUID

class SubmitIn(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    subject: str
    body: str
    email_id: UUID