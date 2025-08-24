
import pytest
from pydantic import ValidationError
from app.schemas import SubmitIn, SubmitOut

def test_valid_submit_in():
    data = {
        "email_id": "test@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "subject": "Test Subject",
        "body": "This is a test complaint message."
    }
    submit = SubmitIn(**data)
    assert submit.email_id == data["email_id"]
    assert submit.first_name == data["first_name"]
    assert submit.last_name == data["last_name"]
    assert submit.subject == data["subject"]
    assert submit.body == data["body"]

def test_invalid_email_submit_in():
    with pytest.raises(ValidationError):
        SubmitIn(
            email_id="invalid-email",
            first_name="John",
            last_name="Doe",
            subject="Test Subject",
            body="Message"
        )

def test_empty_fields_submit_in():
    with pytest.raises(ValidationError):
        SubmitIn(
            email_id="test@example.com",
            first_name="",
            last_name="",
            subject="",
            body=""
        )

def test_submit_out():
    data = {
        "id": "1234",
        "status": "saved",
        "warning": None
    }
    out = SubmitOut(**data)
    assert out.id == data["id"]
    assert out.status == data["status"]
    assert out.warning is None
