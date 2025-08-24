from pydantic import BaseModel, EmailStr

class SubmitIn(BaseModel):
    email_id: EmailStr
    first_name: str
    last_name: str
    subject: str
    body: str