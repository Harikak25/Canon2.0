
import pytest
from pydantic import ValidationError
from app.schemas import SubmitIn

def test_valid_submitin():
    data = {
        "email_id": "test@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "subject": "Test Subject",
        "body": "This is a test message."
    }
    submit = SubmitIn(**data)
    assert submit.email_id == "test@example.com"
    assert submit.first_name == "John"

def test_invalid_email():
    data = {
        "email_id": "not-an-email",
        "first_name": "John",
        "last_name": "Doe",
        "subject": "Test",
        "body": "Body"
    }
    with pytest.raises(ValidationError):
        SubmitIn(**data)
